from .base import BaseTTS


class EdgeTTSProvider(BaseTTS):
    """
    Placeholder implementation for Phase 1.
    Real edge-tts integration will be completed in TTS phase.
    """

    async def synthesize(self, text: str) -> bytes:
        return b""
