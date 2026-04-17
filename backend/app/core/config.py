"""
Application configuration loaded from environment variables / .env file.
All settings are validated at startup — bad config fails fast.
"""
from functools import lru_cache
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_list(v: Any) -> List[str]:
    """
    Accept a list field written in either format in .env:

        CORS_ORIGINS=http://localhost:5173,http://localhost:3000
        CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

    Already-parsed lists are returned as-is.
    """
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("["):
            import json
            return json.loads(v)
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_NAME: str = "AI Support Portal"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./support.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin Bootstrap
    ADMIN_EMAIL: str = "admin@support.com"
    ADMIN_PASSWORD: str = "Admin@123"

    # AI / Groq
    GROQ_API_KEY: str = ""
    GROQ_CLASSIFIER_MODEL: str = "llama3-70b-8192"
    GROQ_SUMMARY_MODEL: str = "llama-3.1-8b-instant"
    GROQ_KB_MODEL: str = "llama-3.1-8b-instant"

    # Vector Store
    CHROMA_PERSIST_PATH: str = "./chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    KB_SIMILARITY_THRESHOLD: float = 0.6

    # File Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_TYPES: List[str] = ["application/pdf", "text/plain"]

    # Optional Integrations
    YOUTUBE_API_KEY: str = ""

    # Validators
    @field_validator("CORS_ORIGINS", "ALLOWED_UPLOAD_TYPES", mode="before")
    @classmethod
    def parse_list_fields(cls, v: Any) -> List[str]:
        """Accept comma-separated OR JSON array format in .env"""
        return _parse_list(v)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def warn_weak_secret(cls, v: str) -> str:
        if v in ("dev-secret-change-in-production", "CHANGE_ME_USE_STRONG_RANDOM_SECRET"):
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is using a default/weak value. "
                "Set a strong secret in production.",
                stacklevel=2,
            )
        return v

    # Derived properties
    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of instantiating directly."""
    return Settings()