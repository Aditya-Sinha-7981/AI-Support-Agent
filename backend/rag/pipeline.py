"""RAG pipeline: retrieve domain chunks, stream LLM answer, expose sources + sentiment."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import OrderedDict
from typing import Any, AsyncGenerator

from agent.sentiment import detect_sentiment
from config import settings
from providers.llm import get_llm_provider
from rag.retriever import Retriever

VALID_DOMAINS = frozenset({"banking", "ecommerce"})

_DOMAIN_LABEL = {
    "banking": "banking and financial services",
    "ecommerce": "e-commerce and online retail",
}

_retrievers: dict[str, Retriever] = {}
logger = logging.getLogger("ai_support.pipeline")


def _safe_int(value: object, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_retriever(domain: str) -> Retriever:
    if domain not in _retrievers:
        _retrievers[domain] = Retriever(domain)
    r = _retrievers[domain]
    r.ensure_loaded()
    return r


def _normalize_domain(domain: str) -> str:
    d = (domain or "banking").strip().lower()
    return d if d in VALID_DOMAINS else "banking"


def _sources_from_hits(hits: list[dict]) -> list[dict]:
    seen: set[tuple[str, int]] = set()
    out: list[dict] = []
    for h in hits:
        file_name = h.get("file") or "unknown"
        page = _safe_int(h.get("page", 1), default=1)
        key = (file_name, page)
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": file_name, "page": page})
    return out


def _format_history(history: list) -> str:
    lines: list[str] = []
    for turn in history:
        role = turn.get("role", "")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"Customer: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
    return "\n".join(lines)


def _tone_hint(sentiment: str) -> str:
    if sentiment == "frustrated":
        return "The customer sounds frustrated; be calm, empathetic, and solution-focused."
    if sentiment == "positive":
        return "The customer sounds positive; stay warm and clear."
    return "Keep a neutral, professional tone."


def _detect_language_hint(message: str) -> str:
    text = message or ""
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return "Hindi (Devanagari)"
    if any("\u0c00" <= ch <= "\u0c7f" for ch in text):
        return "Telugu"
    if any("\u0980" <= ch <= "\u09ff" for ch in text):
        return "Bengali"
    if any("\u0a00" <= ch <= "\u0a7f" for ch in text):
        return "Punjabi (Gurmukhi)"
    if any("\u0a80" <= ch <= "\u0aff" for ch in text):
        return "Gujarati"
    if any("\u0b00" <= ch <= "\u0b7f" for ch in text):
        return "Odia"
    if any("\u0b80" <= ch <= "\u0bff" for ch in text):
        return "Tamil"
    if any("\u0c80" <= ch <= "\u0cff" for ch in text):
        return "Kannada"
    if any("\u0d00" <= ch <= "\u0d7f" for ch in text):
        return "Malayalam"
    if any("\u0600" <= ch <= "\u06ff" for ch in text):
        return "Arabic"
    if any("\u0400" <= ch <= "\u04ff" for ch in text):
        return "Cyrillic-language script"
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "Chinese"
    if any("\u3040" <= ch <= "\u309f" for ch in text) or any(
        "\u30a0" <= ch <= "\u30ff" for ch in text
    ):
        return "Japanese"
    if any("\uac00" <= ch <= "\ud7af" for ch in text):
        return "Korean"
    if any("\u0e00" <= ch <= "\u0e7f" for ch in text):
        return "Thai"
    if any("\u0590" <= ch <= "\u05ff" for ch in text):
        return "Hebrew"
    return "Same language as user message"


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "quota" in text or "429" in text or "resource_exhausted" in text


# Words that suggest the message refers back to earlier turns and benefits from
# a rewrite that resolves anaphora into a standalone retrieval query.
_REFERENT_RE = re.compile(
    r"\b(it|its|that|this|those|these|they|them|their|same|above|earlier|previous|prev)\b",
    re.IGNORECASE,
)


def _should_rewrite(message: str, history: list) -> bool:
    """Decide whether the LLM rewrite call is worth spending a quota request on."""
    text = (message or "").strip()
    if not text:
        return False
    if len(history or []) < 2:
        return False
    if len(text) >= 60:
        return False
    return bool(_REFERENT_RE.search(text))


def _groq_configured() -> bool:
    """True only when GROQ_API_KEY is set to a real value (not blank or placeholder)."""
    key = (settings.GROQ_API_KEY or "").strip()
    if not key:
        return False
    return key.lower() not in {"your_key_here", "your-key-here", "changeme"}


def _normalize_message(message: str) -> str:
    return " ".join((message or "").lower().split())


class _LruTtlCache:
    """Tiny in-memory LRU with per-entry TTL; used for repeat-query short-circuit."""

    def __init__(self, capacity: int = 64, ttl_seconds: float = 900.0) -> None:
        self._capacity = max(1, capacity)
        self._ttl = max(0.0, ttl_seconds)
        self._items: "OrderedDict[str, tuple[float, dict[str, Any]]]" = OrderedDict()

    def get(self, key: str) -> dict[str, Any] | None:
        item = self._items.get(key)
        if item is None:
            return None
        ts, value = item
        if time.monotonic() - ts > self._ttl:
            self._items.pop(key, None)
            return None
        self._items.move_to_end(key)
        return value

    def set(self, key: str, value: dict[str, Any]) -> None:
        if key in self._items:
            self._items.move_to_end(key)
        self._items[key] = (time.monotonic(), value)
        while len(self._items) > self._capacity:
            self._items.popitem(last=False)


_response_cache = _LruTtlCache(capacity=64, ttl_seconds=900.0)


# Cap concurrent LLM calls so a burst of users cannot blow through RPM at once.
_LLM_SEMAPHORE = asyncio.Semaphore(2)


async def _bounded_complete(llm, prompt: str) -> str:
    async with _LLM_SEMAPHORE:
        return await llm.complete(prompt)


async def _bounded_stream(llm, prompt: str) -> AsyncGenerator[str, None]:
    async with _LLM_SEMAPHORE:
        async for token in llm.stream(prompt):
            yield token


def _build_prompt(
    *,
    domain: str,
    history: list,
    message: str,
    context_blocks: list[str],
    sentiment: str,
) -> str:
    label = _DOMAIN_LABEL.get(domain, "customer support")
    hist = _format_history(history)
    tone = _tone_hint(sentiment)
    language_hint = _detect_language_hint(message)

    context_section = "\n\n---\n\n".join(
        f"[Passage {i + 1}]\n{t}" for i, t in enumerate(context_blocks)
    )

    if not context_section.strip():
        context_section = "(No matching passages were found in the knowledge base.)"

    parts = [
        f"You are a helpful customer support assistant for {label}.",
        tone,
        f"Reply language must be exactly: {language_hint}.",
        "Always respond in the same language as the customer's latest message.",
        "Do not switch to Hindi unless the customer's message is in Hindi.",
        "Never ask the customer to switch to English.",
        "If the user writes in Hindi or any non-English language, your full reply must stay in that language.",
        "If the language is Telugu, reply only in Telugu.",
        "If the language is Tamil, reply only in Tamil.",
        "If the language is Kannada, reply only in Kannada.",
        "If the language is Malayalam, reply only in Malayalam.",
        "If knowledge is missing, state that limitation in the same user language.",
        "Answer using only the provided passages when they contain the answer. "
        "If the answer is not in the passages, say you do not have that information in the documentation.",
        "Do not invent account numbers, fees, or policies that are not stated in the passages.",
        f"\n## Knowledge base excerpts\n{context_section}\n",
    ]
    if hist:
        parts.append(f"## Prior conversation\n{hist}\n")
    parts.append(f"## Current customer message\n{message}\n\n## Your reply")
    return "\n".join(parts)


async def _stream_fixed(text: str) -> AsyncGenerator[str, None]:
    for word in text.split():
        yield word + " "


class RAGPipeline:
    """
    M3 calls `query` and reads `last_sources` / `last_sentiment` after the stream ends.
    """

    def __init__(self) -> None:
        self.last_sources: list[dict] = []
        self.last_sentiment = "neutral"
        self.last_suggestions: list[str] = []

    async def _rewrite_query(self, message: str, history: list, llm) -> str:
        hist = _format_history(history[-4:])
        rewrite_prompt = (
            "Rewrite the user's latest message as a clear standalone retrieval query.\n"
            "Keep intent intact. Do not add new facts.\n"
            "Return only the rewritten query.\n\n"
            f"Conversation history:\n{hist or '(none)'}\n\n"
            f'Latest user message: "{message.strip()}"'
        )
        rewritten = (await _bounded_complete(llm, rewrite_prompt)).strip()
        return rewritten or message.strip()

    async def _generate_suggestions(
        self, *, llm, assistant_reply: str, user_message: str
    ) -> list[str]:
        language_hint = _detect_language_hint(user_message)
        prompt = (
            "Based on the latest support exchange, suggest 3 short follow-up questions.\n"
            "Return only a JSON array of strings.\n\n"
            f"Language rule: Return suggestions in {language_hint}. Never switch to English unless the user wrote in English.\n"
            f'User message: "{user_message.strip()}"\n'
            f'Assistant reply: "{assistant_reply.strip()}"'
        )
        raw = (await _bounded_complete(llm, prompt)).strip()
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                return []
            out: list[str] = []
            for item in data:
                text = str(item).strip()
                if text:
                    out.append(text)
            return out[:3]
        except json.JSONDecodeError:
            return []

    async def query(
        self,
        message: str,
        domain: str,
        history: list,
    ) -> AsyncGenerator[str, None]:
        domain = _normalize_domain(domain)
        self.last_sources = []
        self.last_sentiment = await detect_sentiment(message)
        self.last_suggestions = []
        logger.info(
            "RAG start domain=%s sentiment=%s msg_chars=%d history_turns=%d",
            domain,
            self.last_sentiment,
            len(message or ""),
            len(history or []),
        )

        retriever = _get_retriever(domain)

        if not retriever.is_available():
            logger.warning("RAG index unavailable domain=%s", domain)
            notice = (
                "The knowledge base for this domain is not loaded yet. "
                "Please run ingestion (see backend/scripts/ingest_domain.py) and try again."
            )
            async for token in _stream_fixed(notice):
                yield token
            return

        cache_key = f"{domain}::{_normalize_message(message)}"
        cached = _response_cache.get(cache_key)
        if cached:
            logger.info(
                "RAG cache hit domain=%s tokens=%d",
                domain,
                len(cached.get("tokens", [])),
            )
            self.last_sources = list(cached.get("sources", []))
            self.last_suggestions = list(cached.get("suggestions", []))
            for token in cached.get("tokens", []):
                yield token
            return

        primary_provider = (settings.LLM_PROVIDER or "gemini").strip().lower()
        llm = get_llm_provider(primary_provider)
        retrieval_query = message.strip()
        if _should_rewrite(message, history):
            try:
                retrieval_query = await self._rewrite_query(message, history, llm)
            except Exception:  # noqa: BLE001
                logger.exception("Query rewrite failed; falling back to original query")
                retrieval_query = message.strip()
        else:
            logger.info("RAG rewrite skipped domain=%s (heuristic)", domain)

        hits = await retriever.search(retrieval_query, k=4)
        logger.info("RAG retrieved domain=%s hits=%d", domain, len(hits))
        if hits:
            self.last_sources = _sources_from_hits(hits)
        blocks = [h.get("text", "").strip() for h in hits if h.get("text")]
        prompt = _build_prompt(
            domain=domain,
            history=history,
            message=message.strip(),
            context_blocks=blocks,
            sentiment=self.last_sentiment,
        )
        logger.info("RAG prompt domain=%s prompt_chars=%d", domain, len(prompt))

        stream_tokens: list[str] = []
        full_reply = ""
        try:
            async for token in _bounded_stream(llm, prompt):
                stream_tokens.append(token)
                full_reply += token
                yield token
            if full_reply.strip():
                try:
                    self.last_suggestions = await self._generate_suggestions(
                        llm=llm, assistant_reply=full_reply, user_message=message
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("Suggestion generation failed")
                    self.last_suggestions = []
            else:
                self.last_suggestions = []
            self._store_cache(cache_key, stream_tokens)
            logger.info(
                "RAG stream complete domain=%s provider=%s tokens=%d",
                domain,
                primary_provider,
                len(stream_tokens),
            )
            return
        except Exception as primary_exc:  # noqa: BLE001
            should_try_groq = (
                primary_provider == "gemini"
                and _is_quota_error(primary_exc)
                and _groq_configured()
            )
            if not should_try_groq:
                if (
                    primary_provider == "gemini"
                    and _is_quota_error(primary_exc)
                    and not _groq_configured()
                ):
                    logger.warning(
                        "RAG gemini quota hit; groq fallback skipped (GROQ_API_KEY not configured)"
                    )
                raise

            logger.warning("RAG gemini quota hit; attempting groq fallback")
            try:
                fallback_llm = get_llm_provider("groq")
                async for token in _bounded_stream(fallback_llm, prompt):
                    stream_tokens.append(token)
                    full_reply += token
                    yield token
                if full_reply.strip():
                    try:
                        self.last_suggestions = await self._generate_suggestions(
                            llm=fallback_llm,
                            assistant_reply=full_reply,
                            user_message=message,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception("Suggestion generation failed on fallback")
                        self.last_suggestions = []
                else:
                    self.last_suggestions = []
                self._store_cache(cache_key, stream_tokens)
                logger.info(
                    "RAG stream complete domain=%s provider=groq_fallback tokens=%d",
                    domain,
                    len(stream_tokens),
                )
                return
            except Exception as fallback_exc:  # noqa: BLE001
                logger.exception("RAG groq fallback failed")
                raise RuntimeError(
                    f"Gemini quota exceeded and Groq fallback failed: {fallback_exc}"
                ) from fallback_exc

    def _store_cache(self, cache_key: str, stream_tokens: list[str]) -> None:
        if not stream_tokens:
            return
        _response_cache.set(
            cache_key,
            {
                "tokens": list(stream_tokens),
                "sources": list(self.last_sources),
                "suggestions": list(self.last_suggestions),
            },
        )


# Singleton — import and use this instance everywhere
pipeline = RAGPipeline()
