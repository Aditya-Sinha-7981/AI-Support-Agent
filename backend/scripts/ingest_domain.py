#!/usr/bin/env python3
"""
Build the FAISS index for a domain from files under backend/data/documents/{domain}/.

Usage (from backend/ with venv active):
  python scripts/ingest_domain.py banking
  python scripts/ingest_domain.py ecommerce
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow `python scripts/ingest_domain.py` from backend/
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from rag.ingestor import ingest_domain, VALID_DOMAINS


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into FAISS for a domain.")
    parser.add_argument(
        "domain",
        choices=sorted(VALID_DOMAINS),
        help="Knowledge domain to index",
    )
    args = parser.parse_args()
    summary = asyncio.run(ingest_domain(args.domain))
    print("Ingest complete:", summary)


if __name__ == "__main__":
    main()
