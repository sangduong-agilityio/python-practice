"""
Central configuration.

pydantic-settings reads values from environment variables first,
then falls back to the .env file. The app will not start if a required
variable is missing -- that is intentional: fail fast at boot rather
than encounter a KeyError at 3am in production.
"""

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Automatically replace sync driver with asyncpg for cloud deployments.

        Railway and Heroku may supply either postgresql:// or postgres://,
        both of which default to psycopg2 (sync). We normalise to
        postgresql+asyncpg:// so SQLAlchemy async engine works correctly.
        """
        if not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS -- stored as a JSON array in the env file
    CORS_ORIGINS: list[AnyHttpUrl] = []

    # Security
    ALLOWED_HOSTS: list[str] = ["*"]

    # Redis -- used for response caching
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Cache TTL in seconds for GET /projects and GET /tags
    CACHE_TTL_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # Email -- optional, sending is skipped when SMTP_USER is blank
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "Task Manager"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


settings = Settings()
