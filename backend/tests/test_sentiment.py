import pytest

from agent.sentiment import detect_sentiment


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("this is not working", "frustrated"),
        ("I am really frustrated!!", "frustrated"),
        ("worst experience ever", "frustrated"),
        ("STILL NOT FIXED", "frustrated"),
        ("thanks but issue still not resolved", "frustrated"),
        ("why is this so hard", "frustrated"),
        ("thanks, this worked great", "positive"),
        ("awesome support thank you", "positive"),
        ("what are your timings?", "neutral"),
        ("can you share my statement", "neutral"),
        ("not good", "frustrated"),
        ("not bad actually", "neutral"),
        ("", "neutral"),
        ("   ", "neutral"),
    ],
)
async def test_detect_sentiment_local_only(message: str, expected: str) -> None:
    assert await detect_sentiment(message, llm=None) == expected
