from config import settings
from .base import BaseTTS
from .edge_tts import EdgeTTSProvider
from .elevenlabs import ElevenLabsTTSProvider


def get_tts_provider() -> BaseTTS:
    if settings.TTS_PROVIDER == "elevenlabs":
        return ElevenLabsTTSProvider()
    return EdgeTTSProvider()
