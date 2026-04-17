import asyncio
from typing import AsyncGenerator

from google import genai

from config import settings
from .base import BaseLLM


class GeminiLLM(BaseLLM):
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model_name = settings.GEMINI_MODEL

    def _generation_config(self):
        return genai.types.GenerateContentConfig(
            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            thinking_config=genai.types.ThinkingConfig(
                thinking_budget=settings.GEMINI_THINKING_BUDGET
            ),
        )

    async def complete(self, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model_name,
                contents=prompt,
                config=self._generation_config(),
            )
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "quota" in message or "resourceexhausted" in message:
                raise RuntimeError(
                    "Gemini quota exceeded. Check API plan/quota limits or switch LLM_PROVIDER to groq."
                ) from exc
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc
        text = getattr(response, "text", "")
        return text.strip()

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            response_stream = self._client.models.generate_content_stream(
                model=self._model_name,
                contents=prompt,
                config=self._generation_config(),
            )
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "quota" in message or "resourceexhausted" in message:
                raise RuntimeError(
                    "Gemini quota exceeded. Check API plan/quota limits or switch LLM_PROVIDER to groq."
                ) from exc
            raise RuntimeError(f"Gemini stream init failed: {exc}") from exc

        stream_iterator = iter(response_stream)
        while True:
            try:
                chunk = await asyncio.to_thread(lambda: next(stream_iterator, None))
            except Exception as exc:
                message = str(exc).lower()
                if "429" in message or "quota" in message or "resourceexhausted" in message:
                    raise RuntimeError(
                        "Gemini quota exceeded during streaming. Check API quota or switch provider."
                    ) from exc
                raise RuntimeError(f"Gemini streaming failed: {exc}") from exc

            if chunk is None:
                break

            text = getattr(chunk, "text", "")
            if text:
                # Normalize to smaller token-like pieces for smoother UI updates.
                for piece in text.split(" "):
                    if piece:
                        yield piece + " "
