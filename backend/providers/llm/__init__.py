from config import settings
from .base import BaseLLM
from .gemini import GeminiLLM
from .groq import GroqLLM


def get_llm_provider() -> BaseLLM:
    if settings.LLM_PROVIDER == "groq":
        return GroqLLM()
    return GeminiLLM()
