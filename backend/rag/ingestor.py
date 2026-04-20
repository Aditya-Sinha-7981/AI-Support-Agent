"""Load domain documents, chunk, embed with Gemini, persist FAISS + metadata."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from pypdf import PdfReader

from config import DOCUMENTS_DIR, INDEXES_DIR, settings
from rag.embeddings import embed_texts, normalize_rows

# ~512 tokens / ~50 token overlap (CORE.md) — character approximation
_CHUNK_CHARS = 2048
_OVERLAP_CHARS = 200

VALID_DOMAINS = frozenset({"banking", "ecommerce"})


def _chunk_text(text: str, chunk_size: int = _CHUNK_CHARS, overlap: int = _OVERLAP_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def _extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    out: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ""
        if t.strip():
            out.append((i + 1, t))
    return out


def _extract_txt(path: Path) -> list[tuple[int, str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return [(1, raw)]


def _gather_chunks(domain: str) -> list[dict[str, Any]]:
    root = DOCUMENTS_DIR / domain
    if not root.is_dir():
        raise FileNotFoundError(f"No document folder at {root}")

    records: list[dict[str, Any]] = []
    exts = {".pdf", ".txt", ".md"}

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        rel_name = path.name
        if path.suffix.lower() == ".pdf":
            pages = _extract_pdf_pages(path)
            for page_num, page_text in pages:
                for chunk in _chunk_text(page_text):
                    records.append(
                        {"file": rel_name, "page": page_num, "text": chunk}
                    )
        else:
            pages = _extract_txt(path)
            for page_num, page_text in pages:
                for chunk in _chunk_text(page_text):
                    records.append(
                        {"file": rel_name, "page": page_num, "text": chunk}
                    )
    return records


async def ingest_domain(domain: str) -> dict[str, Any]:
    """
    Build FAISS index under data/indexes/{domain}/.
    Returns a small summary dict (chunk count, paths).
    """
    domain = domain.strip().lower()
    if domain not in VALID_DOMAINS:
        raise ValueError(f"domain must be one of {sorted(VALID_DOMAINS)}")

    chunks = _gather_chunks(domain)
    if not chunks:
        raise ValueError(
            f"No ingestible content in {DOCUMENTS_DIR / domain}. "
            "Add .pdf, .txt, or .md files."
        )

    texts = [c["text"] for c in chunks]
    vectors = await embed_texts(texts)
    dim = len(vectors[0])
    mat = np.array(vectors, dtype=np.float32)
    normalize_rows(mat)

    index = faiss.IndexFlatIP(dim)
    index.add(mat)

    out_dir = INDEXES_DIR / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.faiss"
    meta_path = out_dir / "metadata.json"

    faiss.write_index(index, str(index_path))
    payload = {
        "domain": domain,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        "dim": dim,
        "chunks": chunks,
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "domain": domain,
        "chunks": len(chunks),
        "index_path": str(index_path),
        "metadata_path": str(meta_path),
    }


def run_ingest_sync(domain: str) -> dict[str, Any]:
    """CLI / script entry (blocking)."""
    return asyncio.run(ingest_domain(domain))
