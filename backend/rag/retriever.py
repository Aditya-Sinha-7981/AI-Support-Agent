"""Load FAISS index + metadata and retrieve top-K chunks for a query."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss

from config import INDEXES_DIR
from rag.embeddings import embed_query

DEFAULT_TOP_K = 4


class Retriever:
    def __init__(self, domain: str) -> None:
        self.domain = domain
        self._index: faiss.Index | None = None
        self._chunks: list[dict[str, Any]] = []
        self._dim: int = 0
        self._index_mtime: float | None = None

    @property
    def index_path(self) -> Path:
        return INDEXES_DIR / self.domain / "index.faiss"

    @property
    def metadata_path(self) -> Path:
        return INDEXES_DIR / self.domain / "metadata.json"

    def is_available(self) -> bool:
        return self.index_path.is_file() and self.metadata_path.is_file()

    def load(self) -> None:
        if not self.is_available():
            self._index = None
            self._chunks = []
            self._dim = 0
            return

        self._index = faiss.read_index(str(self.index_path))
        raw = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self._chunks = list(raw.get("chunks", []))
        self._dim = int(raw.get("dim", 0))

    def ensure_loaded(self) -> None:
        if not self.is_available():
            self._index = None
            self._chunks = []
            self._dim = 0
            return
        mtime = self.index_path.stat().st_mtime
        if self._index is None or mtime != self._index_mtime:
            self.load()
            self._index_mtime = mtime

    async def search(self, query: str, k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        self.ensure_loaded()
        if self._index is None or self._index.ntotal == 0:
            return []

        q = await embed_query(query)
        k_eff = min(k, int(self._index.ntotal))
        scores, indices = self._index.search(q, k_eff)

        hits: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            meta = self._chunks[idx]
            hits.append(
                {
                    "file": meta.get("file", ""),
                    "page": int(meta.get("page", 1)),
                    "text": meta.get("text", ""),
                    "score": float(score),
                }
            )
        return hits
