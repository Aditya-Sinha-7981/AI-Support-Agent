def route(message: str) -> str:
    """
    Decide where to route an incoming user message.
    """
    text = (message or "").strip().lower()
    if not text:
        return "empty"

    handoff_keywords = (
        "human",
        "agent",
        "representative",
        "supervisor",
        "manager",
    )
    if any(keyword in text for keyword in handoff_keywords):
        return "handoff"

    return "rag"