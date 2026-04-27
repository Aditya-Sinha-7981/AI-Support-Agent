#!/usr/bin/env python3
"""
Verify CORE Step 3 contract on the real FastAPI WebSocket route.

Checks:
1) `/ws/chat/{session_id}?domain=...` accepts a message.
2) Server emits required terminal sequence with optional extras.
3) At least one token is streamed.

Run from backend/:
  python scripts/test_step3_ws.py
  python scripts/test_step3_ws.py --domain ecommerce --message "What is your return policy?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


VALID_SENTIMENTS = {"positive", "neutral", "frustrated"}


def _assert_event_order(events: list[dict]) -> None:
    if not events:
        raise AssertionError("No WebSocket events received.")

    event_types = [e.get("type") for e in events]
    if event_types[-1] != "done":
        raise AssertionError(f"Last event must be 'done', got: {event_types[-1]!r}")

    try:
        first_sources = event_types.index("sources")
        first_sentiment = event_types.index("sentiment")
        done_idx = event_types.index("done")
    except ValueError as exc:
        raise AssertionError(f"Missing required terminal event: {exc}") from exc

    if not (first_sources < first_sentiment < done_idx):
        raise AssertionError(
            "Invalid event order. Expected token* -> sources -> sentiment -> done."
        )

    token_count = sum(1 for t in event_types[:first_sources] if t == "token")
    non_token_before_sources = [
        t for t in event_types[:first_sources] if t not in {"token", "status"}
    ]

    if token_count == 0:
        raise AssertionError("Expected at least one token event before sources.")
    if non_token_before_sources:
        raise AssertionError(
            f"Only token/status events allowed before sources. Got: {non_token_before_sources}"
        )

    if any(t == "token" for t in event_types[first_sources:]):
        raise AssertionError("No token events are allowed after sources.")

    sources_payload = events[first_sources].get("content")
    if not isinstance(sources_payload, list):
        raise AssertionError("`sources.content` must be a list.")

    sentiment_payload = events[first_sentiment].get("content")
    if sentiment_payload not in VALID_SENTIMENTS:
        raise AssertionError(
            f"`sentiment.content` must be one of {sorted(VALID_SENTIMENTS)}, got {sentiment_payload!r}."
        )

    tail = event_types[first_sentiment + 1 : done_idx]
    invalid_tail_types = [t for t in tail if t not in {"suggestions", "ticket"}]
    if invalid_tail_types:
        raise AssertionError(
            f"Only suggestions/ticket may appear after sentiment before done. Got: {invalid_tail_types}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Step 3 WebSocket contract using FastAPI TestClient."
    )
    parser.add_argument(
        "--domain",
        choices=("banking", "ecommerce"),
        default="banking",
        help="Domain query parameter for /ws/chat.",
    )
    parser.add_argument(
        "--session-id",
        default="step3-check",
        help="Session id to use in the ws path.",
    )
    parser.add_argument(
        "--message",
        default="What documents do I need to open a savings account?",
        help="Message payload sent to the websocket.",
    )
    args = parser.parse_args()

    ws_path = f"/ws/chat/{args.session_id}?domain={args.domain}"
    events: list[dict] = []

    with TestClient(app) as client:
        with client.websocket_connect(ws_path) as ws:
            ws.send_json({"message": args.message})
            while True:
                payload = ws.receive_json()
                events.append(payload)
                if payload.get("type") == "done":
                    break

    _assert_event_order(events)

    token_text = "".join(
        e.get("content", "") for e in events if e.get("type") == "token"
    ).strip()
    sources = next(e.get("content") for e in events if e.get("type") == "sources")
    sentiment = next(e.get("content") for e in events if e.get("type") == "sentiment")

    print("Step 3 WebSocket contract check: PASS")
    print(f"Domain: {args.domain}")
    print(f"Token chars: {len(token_text)}")
    print(f"Sources: {sources}")
    print(f"Sentiment: {sentiment}")


if __name__ == "__main__":
    main()

