import asyncio
from typing import AsyncGenerator

from groq import Groq

from config import settings
from .base import BaseLLM


class GroqLLM(BaseLLM):
    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq LLM provider")
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    async def complete(self, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Groq completion failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else ""
        return (content or "").strip()

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            stream = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Groq stream init failed: {exc}") from exc

        iterator = iter(stream)
        while True:
            try:
                chunk = await asyncio.to_thread(lambda: next(iterator, None))
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Groq streaming failed: {exc}") from exc
            if chunk is None:
                break

            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None) or ""
            if text:
                yield text
