from .base import BaseSTT


class DeepgramSTT(BaseSTT):
    """
    Placeholder implementation for Phase 1.
    Real Deepgram API call will be completed in the STT phase.
    """

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        return "Transcription pending Deepgram integration."
