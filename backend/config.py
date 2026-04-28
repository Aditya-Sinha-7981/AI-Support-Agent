from pathlib import Path

from pydantic_settings import BaseSettings

# Paths — backend/ is the working directory for imports; data/ lives next to this file.
BACKEND_ROOT = Path(__file__).resolve().parent
DATA_DIR = BACKEND_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INDEXES_DIR = DATA_DIR / "indexes"


class Settings(BaseSettings):
    # LLM
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_THINKING_BUDGET: int = 0
    GEMINI_MAX_OUTPUT_TOKENS: int = 512
    # Embeddings (RAG retrieval; uses Gemini even when LLM_PROVIDER=groq)
    # Use a model id supported by google-genai embed_content (see Google AI ListModels).
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    SENTIMENT_LLM_FALLBACK: bool = False
    SENTIMENT_LLM_TIMEOUT_SECONDS: float = 3.0

    # STT
    STT_PROVIDER: str = "local"
    DEEPGRAM_API_KEY: str = ""

    # TTS
    TTS_PROVIDER: str = "edge"
    ELEVENLABS_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
