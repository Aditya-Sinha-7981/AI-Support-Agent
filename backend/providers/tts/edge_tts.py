from __future__ import annotations

import edge_tts

from .base import BaseTTS


class EdgeTTSProvider(BaseTTS):
    async def synthesize(self, text: str) -> bytes:
        text = (text or "").strip()
        if not text:
            return b""

        communicate = edge_tts.Communicate(text=text, voice="en-US-JennyNeural")
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                audio.extend(chunk["data"])
        return bytes(audio)
