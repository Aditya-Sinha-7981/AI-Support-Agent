def route(message: str):
    """
    Decide where to send the message
    For now, everything goes to RAG pipeline
    """
    return "rag"