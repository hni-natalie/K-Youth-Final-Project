from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_PATH: str = "data/jobs_database.db"
    GOOGLE_API_KEY: str
    CHAT_MODEL: str = "gemini-2.5-flash"
    CHAT_MODEL_FALLBACK: str = "gemini-3.1-flash-lite"
    API_PORT: int = 8001
    CORS_ORIGINS: list[str] = ["http://localhost:8000"]  # Frontend URL
    AI_RATE_LIMIT: int = 10  # Batch size for Gemini requests

    class Config:
        env_file = ".env"

settings = Settings()