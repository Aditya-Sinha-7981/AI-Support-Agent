from .base import BaseTTS


class ElevenLabsTTSProvider(BaseTTS):
    """
    Placeholder implementation for Phase 1.
    Real ElevenLabs integration will be completed in TTS fallback phase.
    """

    async def synthesize(self, text: str) -> bytes:
        return b""
