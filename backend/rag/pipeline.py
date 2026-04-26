"""RAG pipeline: retrieve domain chunks, stream LLM answer, expose sources + sentiment."""

from __future__ import annotations

import logging
from typing import AsyncGenerator

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


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "quota" in text or "429" in text or "resource_exhausted" in text


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

    context_section = "\n\n---\n\n".join(
        f"[Passage {i + 1}]\n{t}" for i, t in enumerate(context_blocks)
    )

    if not context_section.strip():
        context_section = "(No matching passages were found in the knowledge base.)"

    parts = [
        f"You are a helpful customer support assistant for {label}.",
        tone,
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

    async def query(
        self,
        message: str,
        domain: str,
        history: list,
    ) -> AsyncGenerator[str, None]:
        domain = _normalize_domain(domain)
        self.last_sources = []
        self.last_sentiment = await detect_sentiment(message)
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

        primary_provider = (settings.LLM_PROVIDER or "gemini").strip().lower()
        llm = get_llm_provider(primary_provider)
        hits = await retriever.search(message.strip(), k=4)
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

        stream_token_count = 0
        try:
            async for token in llm.stream(prompt):
                stream_token_count += 1
                yield token
            logger.info(
                "RAG stream complete domain=%s provider=%s tokens=%d",
                domain,
                primary_provider,
                stream_token_count,
            )
            return
        except Exception as primary_exc:  # noqa: BLE001
            if primary_provider == "gemini" and _is_quota_error(primary_exc):
                logger.warning("RAG gemini quota hit; attempting groq fallback")
                try:
                    fallback_llm = get_llm_provider("groq")
                    async for token in fallback_llm.stream(prompt):
                        stream_token_count += 1
                        yield token
                    logger.info(
                        "RAG stream complete domain=%s provider=groq_fallback tokens=%d",
                        domain,
                        stream_token_count,
                    )
                    return
                except Exception as fallback_exc:  # noqa: BLE001
                    logger.exception("RAG groq fallback failed")
                    raise RuntimeError(
                        f"Gemini quota exceeded and Groq fallback failed: {fallback_exc}"
                    ) from fallback_exc
            raise


# Singleton — import and use this instance everywhere
pipeline = RAGPipeline()
