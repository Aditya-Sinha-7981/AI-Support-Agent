#!/usr/bin/env python3
"""
Exercise the RAG pipeline in isolation (CORE build step 2).

Prerequisites:
  - GEMINI_API_KEY in .env
  - Index built for that domain, e.g.:
      python scripts/ingest_domain.py banking
      python scripts/ingest_domain.py ecommerce

Usage (from backend/):
  python scripts/test_rag_pipeline.py
  python scripts/test_rag_pipeline.py --domain ecommerce
  python scripts/test_rag_pipeline.py --domain ecommerce --question "How long does standard shipping take?"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_DEFAULT_QUESTIONS = {
    "banking": "What is the minimum opening deposit for the Everyday Savings account?",
    "ecommerce": "How long do I have to return most items for a full refund?",
}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG pipeline against an ingested domain index.")
    parser.add_argument(
        "--domain",
        choices=("banking", "ecommerce"),
        default="banking",
        help="Which knowledge base to query (must have been ingested first).",
    )
    parser.add_argument(
        "--question",
        default=None,
        help="Override the default question for that domain.",
    )
    args = parser.parse_args()

    from rag.pipeline import pipeline

    question = args.question or _DEFAULT_QUESTIONS[args.domain]
    print("Question:", question)
    print("Answer stream:", end=" ", flush=True)
    async for token in pipeline.query(question, args.domain, []):
        print(token, end="", flush=True)
    print()
    print("Sources:", pipeline.last_sources)
    print("Sentiment:", pipeline.last_sentiment)


if __name__ == "__main__":
    asyncio.run(main())
