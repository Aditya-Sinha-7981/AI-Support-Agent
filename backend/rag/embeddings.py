"""Gemini text embeddings for FAISS retrieval."""

from __future__ import annotations

import asyncio
from typing import Sequence

import numpy as np
from google import genai

from config import settings

_BATCH_SIZE = 64


def _require_key() -> None:
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is required for embeddings (ingestion and RAG query). "
            "Set it in .env even if you use Groq for chat completion."
        )


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed multiple strings; order matches input."""
    if not texts:
        return []
    _require_key()

    out: list[list[float]] = []
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model = settings.GEMINI_EMBEDDING_MODEL

    def embed_batch(batch: list[str]) -> list[list[float]]:
        resp = client.models.embed_content(model=model, contents=batch)
        return [list(e.values) for e in resp.embeddings]

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = list(texts[i : i + _BATCH_SIZE])
        part = await asyncio.to_thread(embed_batch, batch)
        out.extend(part)
    return out


async def embed_query(text: str) -> np.ndarray:
    """Single query vector as float32 (1, dim), L2-normalized for inner-product search."""
    vecs = await embed_texts([text])
    arr = np.array([vecs[0]], dtype=np.float32)
    return normalize_rows(arr)


def normalize_rows(x: np.ndarray) -> np.ndarray:
    """L2-normalize each row in place (cosine similarity via inner product)."""
    norms = np.linalg.norm(x, axis=1, keepdims=True).astype(np.float32)
    np.maximum(norms, 1e-12, out=norms)
    x /= norms
    return x
