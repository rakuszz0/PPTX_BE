from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    # SQLAlchemy URL for PostgreSQL.  Override this through DATABASE_URL in
    # deployments (for example, with a managed PostgreSQL connection string).
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/wizape_presentation"
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = ""
    AI_API_KEY: str = ""
    MAX_CONCURRENCY: int = 2
    MIN_QA_SCORE: int = 85
    CORS_ORIGINS: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
