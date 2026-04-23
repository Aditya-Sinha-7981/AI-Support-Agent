import asyncio
from typing import AsyncGenerator

from google import genai

from config import settings
from .base import BaseLLM


class GeminiLLM(BaseLLM):
    _MAX_RETRIES = 3
    _BASE_BACKOFF_SECONDS = 0.8

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

    @staticmethod
    def _is_quota_error(message: str) -> bool:
        return "429" in message or "quota" in message or "resourceexhausted" in message

    @staticmethod
    def _is_transient_error(message: str) -> bool:
        transient_markers = (
            "503",
            "unavailable",
            "high demand",
            "deadline exceeded",
            "timeout",
            "temporarily",
            "try again later",
        )
        return any(marker in message for marker in transient_markers)

    async def _sleep_backoff(self, attempt: int) -> None:
        # attempt starts from 1 for retries; grow delay exponentially.
        await asyncio.sleep(self._BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))

    async def complete(self, prompt: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=self._model_name,
                    contents=prompt,
                    config=self._generation_config(),
                )
                text = getattr(response, "text", "")
                return text.strip()
            except Exception as exc:
                last_exc = exc
                message = str(exc).lower()
                if self._is_quota_error(message):
                    raise RuntimeError(
                        "Gemini quota exceeded. Check API plan/quota limits or switch LLM_PROVIDER to groq."
                    ) from exc
                if self._is_transient_error(message) and attempt < self._MAX_RETRIES:
                    await self._sleep_backoff(attempt + 1)
                    continue
                raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        raise RuntimeError(f"Gemini API call failed after retries: {last_exc}")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response_stream = None
        last_exc: Exception | None = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                response_stream = self._client.models.generate_content_stream(
                    model=self._model_name,
                    contents=prompt,
                    config=self._generation_config(),
                )
                break
            except Exception as exc:
                last_exc = exc
                message = str(exc).lower()
                if self._is_quota_error(message):
                    raise RuntimeError(
                        "Gemini quota exceeded. Check API plan/quota limits or switch LLM_PROVIDER to groq."
                    ) from exc
                if self._is_transient_error(message) and attempt < self._MAX_RETRIES:
                    await self._sleep_backoff(attempt + 1)
                    continue
                raise RuntimeError(f"Gemini stream init failed: {exc}") from exc

        if response_stream is None:
            raise RuntimeError(
                f"Gemini stream init failed after retries: {last_exc or 'unknown error'}"
            )

        stream_iterator = iter(response_stream)
        while True:
            try:
                chunk = await asyncio.to_thread(lambda: next(stream_iterator, None))
            except Exception as exc:
                message = str(exc).lower()
                if self._is_quota_error(message):
                    raise RuntimeError(
                        "Gemini quota exceeded during streaming. Check API quota or switch provider."
                    ) from exc
                if self._is_transient_error(message):
                    raise RuntimeError(
                        f"Gemini temporarily unavailable during streaming (after init succeeded): {exc}"
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
