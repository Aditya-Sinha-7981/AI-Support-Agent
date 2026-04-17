from .base import BaseSTT


class LocalWhisperSTT(BaseSTT):
    """
    Placeholder implementation for Phase 1.
    Real faster-whisper wiring will be completed in the STT phase.
    """

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        return "Transcription pending local whisper integration."
