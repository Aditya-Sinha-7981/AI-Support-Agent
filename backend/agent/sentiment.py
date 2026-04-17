async def detect_sentiment(message: str, llm=None) -> str:
    """
    Simple rule-based sentiment detection (no API needed)
    """

    message = message.lower()

    # frustrated / negative
    if any(word in message for word in ["angry", "bad", "worst", "hate", "not working", "issue", "problem"]):
        return "frustrated"

    # positive
    elif any(word in message for word in ["good", "great", "thanks", "awesome", "love"]):
        return "positive"

    # default
    return "neutral"