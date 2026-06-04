from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_PATH: str = "data/jobs_database.db"
    API_PORT: int = 8001
    CORS_ORIGINS: list[str] = ["http://localhost:8000"]  # Frontend URL
    AI_RATE_LIMIT: int = 10  # Batch size for Gemini requests

    class Config:
        env_file = ".env"

settings = Settings()