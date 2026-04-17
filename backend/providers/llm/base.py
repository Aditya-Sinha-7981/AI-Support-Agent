from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseLLM(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Return a full completion string."""

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yield completion text as streaming tokens/chunks."""
