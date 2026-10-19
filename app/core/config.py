"""
app/core/config.py
------------------
Application configuration using pydantic-settings.

pydantic-settings automatically reads values from environment variables
and from a .env file. This gives us type-safe, validated configuration
that fails fast at startup if something is missing.
"""

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings object for the entire application.

    All fields map 1-to-1 with environment variable names (case-insensitive).
    Pydantic will raise a clear error at startup if a required value is missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",          # Read from .env file in project root
        env_file_encoding="utf-8",
        case_sensitive=False,      # DATABASE_URL == database_url
        extra="ignore",            # Silently ignore unknown env vars
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/taskdb"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    # --- JWT ---
    SECRET_KEY: str = "change-this-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- CORS ---
    # JSON list of allowed frontend origins, e.g. '["http://localhost:3000"]'
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list[str]:
        """
        Allow CORS_ORIGINS to be either a JSON string or a Python list.
        When read from .env it comes as a string, e.g. '["http://..."]'.
        """
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    # --- Email / SMTP ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "no-reply@example.com"
    SMTP_PASSWORD: str = ""

    # --- App meta ---
    APP_TITLE: str = "Task Management API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


# Single shared instance — import this everywhere instead of re-instantiating
settings = Settings()
