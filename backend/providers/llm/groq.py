from typing import AsyncGenerator
from .base import BaseLLM


class GroqLLM(BaseLLM):
    """
    Placeholder implementation for Phase 1.
    Real Groq SDK integration will be completed in LLM fallback phase.
    """

    async def complete(self, prompt: str) -> str:
        return "Groq completion placeholder."

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        for token in ["Groq ", "stream ", "placeholder."]:
            yield token
