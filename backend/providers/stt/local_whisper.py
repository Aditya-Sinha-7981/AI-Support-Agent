from __future__ import annotations

import os
import tempfile
from typing import Optional

from faster_whisper import WhisperModel
from pathlib import Path

from .base import BaseSTT

_MODEL: Optional[WhisperModel] = None


def _get_model() -> WhisperModel:
    global _MODEL  # noqa: PLW0603
    if _MODEL is None:
        # Ensure the HF cache is writable in sandboxed/dev envs by keeping it under backend/.
        backend_root = Path(__file__).resolve().parents[2]
        hf_home = backend_root / ".hf"
        hf_home.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(hf_home))
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_home / "hub"))

        # Cross-platform, CPU-only, int8 quant for speed and compatibility.
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL


def _guess_suffix(audio_bytes: bytes) -> str:
    if len(audio_bytes) >= 12 and audio_bytes[0:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return ".wav"
    return ".webm"


class LocalWhisperSTT(BaseSTT):
    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        suffix = _guess_suffix(audio_bytes)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                tmp_path = f.name
                f.write(audio_bytes)

            model = _get_model()
            segments, _info = model.transcribe(tmp_path)
            text_parts = []
            for seg in segments:
                if seg.text:
                    text_parts.append(seg.text.strip())
            return " ".join([p for p in text_parts if p]).strip()
        finally:
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
