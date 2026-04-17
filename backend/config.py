from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_THINKING_BUDGET: int = 0
    GEMINI_MAX_OUTPUT_TOKENS: int = 512
    GROQ_API_KEY: str = ""

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
