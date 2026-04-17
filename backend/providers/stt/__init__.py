from config import settings
from .base import BaseSTT
from .deepgram import DeepgramSTT
from .local_whisper import LocalWhisperSTT


def get_stt_provider() -> BaseSTT:
    if settings.STT_PROVIDER == "deepgram":
        return DeepgramSTT()
    return LocalWhisperSTT()
