from config import settings
from .base import BaseLLM
from .gemini import GeminiLLM
from .groq import GroqLLM


def get_llm_provider(provider: str | None = None) -> BaseLLM:
    selected = (provider or settings.LLM_PROVIDER).strip().lower()
    if selected == "groq":
        return GroqLLM()
    return GeminiLLM()
