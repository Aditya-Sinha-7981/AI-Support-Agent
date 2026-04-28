#!/usr/bin/env python3
"""
Unit-style checks for hybrid sentiment detector behavior.

Usage (from backend/):
  python scripts/test_sentiment_detector.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from agent.sentiment import detect_sentiment


async def _assert_case(message: str, expected: set[str]) -> None:
    got = await detect_sentiment(message)
    if got not in expected:
        expected_str = ", ".join(sorted(expected))
        raise AssertionError(f"Message={message!r} expected in {{{expected_str}}} but got {got!r}")
    print(f"PASS: {message!r} -> {got}")


async def main() -> None:
    # negative
    await _assert_case("this is not working", {"frustrated"})
    await _assert_case("worst experience ever", {"frustrated"})
    await _assert_case("I am really frustrated!!", {"frustrated"})

    # positive
    await _assert_case("thanks, this worked great", {"positive"})
    await _assert_case("awesome support", {"positive"})

    # neutral
    await _assert_case("what are your timings?", {"neutral"})
    await _assert_case("can you share my statement", {"neutral"})

    # negation
    await _assert_case("not good", {"frustrated"})
    # documented choice: "not bad" maps to neutral for stability.
    await _assert_case("not bad actually", {"neutral"})

    # mixed
    await _assert_case("thanks but issue still not resolved", {"frustrated"})

    # robustness
    await _assert_case("", {"neutral"})
    await _assert_case("THIS APP IS BROKEN!!!!", {"frustrated"})
    await _assert_case("thaaaanks??? really helpful!!!", {"positive"})

    # natural-language phrasing checks (less keywordy)
    await _assert_case(
        "I have tried this for two days and it still fails every time, please fix this.",
        {"frustrated"},
    )
    await _assert_case(
        "Hey team, I really appreciate the quick help, everything is smooth now.",
        {"positive"},
    )
    await _assert_case(
        "Could you help me understand the charges on my latest account statement?",
        {"neutral"},
    )
    await _assert_case("it is too bad", {"frustrated"})
    await _assert_case("this is bad service", {"frustrated"})

    print("\nAll sentiment detector checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
