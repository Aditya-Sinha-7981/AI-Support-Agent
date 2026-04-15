from typing import AsyncGenerator

class RAGPipeline:
    """
    STUB — M1 will replace internals. M3 uses this interface as-is.
    Do not change the method signature or the last_sources/last_sentiment shape.
    """

    def __init__(self):
        self.last_sources = []
        self.last_sentiment = "neutral"

    async def query(
        self,
        message: str,
        domain: str,
        history: list
    ) -> AsyncGenerator[str, None]:
        """
        Yields string tokens one by one.
        After iteration completes, read self.last_sources and self.last_sentiment.
        """
        # --- STUB IMPLEMENTATION ---
        # M1 will replace everything below this line
        stub_response = f"[STUB] Received: '{message}' for domain '{domain}'"
        for word in stub_response.split():
            yield word + " "

        self.last_sources = [{"file": "stub_document.pdf", "page": 1}]
        self.last_sentiment = "neutral"
        # --- END STUB ---


# Singleton — import and use this instance everywhere
pipeline = RAGPipeline()
