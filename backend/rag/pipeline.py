"""RAG pipeline: retrieve domain chunks, stream LLM answer, expose sources + sentiment."""

from __future__ import annotations

from typing import AsyncGenerator

from agent.sentiment import detect_sentiment
from providers.llm import get_llm_provider
from rag.retriever import Retriever

VALID_DOMAINS = frozenset({"banking", "ecommerce"})

_DOMAIN_LABEL = {
    "banking": "banking and financial services",
    "ecommerce": "e-commerce and online retail",
}

_retrievers: dict[str, Retriever] = {}


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
        page = int(h.get("page", 1))
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

        retriever = _get_retriever(domain)

        if not retriever.is_available():
            notice = (
                "The knowledge base for this domain is not loaded yet. "
                "Please run ingestion (see backend/scripts/ingest_domain.py) and try again."
            )
            async for token in _stream_fixed(notice):
                yield token
            return

        llm = get_llm_provider()
        hits = await retriever.search(message.strip(), k=4)
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

        async for token in llm.stream(prompt):
            yield token


# Singleton — import and use this instance everywhere
pipeline = RAGPipeline()
