from __future__ import annotations

from typing import Any

import httpx

from config import settings
from .base import BaseSTT


def _guess_mimetype(audio_bytes: bytes) -> str:
    # WAV files start with "RIFF....WAVE"
    if len(audio_bytes) >= 12 and audio_bytes[0:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "audio/wav"
    # Browser MediaRecorder commonly produces webm/opus; Deepgram accepts audio/webm.
    return "audio/webm"


class DeepgramSTT(BaseSTT):
    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        if not settings.DEEPGRAM_API_KEY:
            raise RuntimeError("DEEPGRAM_API_KEY is missing but STT_PROVIDER=deepgram is selected.")

        mimetype = _guess_mimetype(audio_bytes)
        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true",
        }
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": mimetype,
        }

        timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, params=params, headers=headers, content=audio_bytes)

        if resp.status_code in (401, 403):
            raise RuntimeError("Deepgram authentication failed (check DEEPGRAM_API_KEY).")
        if resp.status_code == 429:
            raise RuntimeError("Deepgram rate-limited (429). Try again later or use STT_PROVIDER=local.")
        if resp.status_code >= 400:
            raise RuntimeError(f"Deepgram STT failed ({resp.status_code}): {resp.text[:500]}")

        data: Any = resp.json()
        try:
            return (
                data["results"]["channels"][0]["alternatives"][0].get("transcript", "") or ""
            ).strip()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Deepgram response parsing failed.") from exc
