from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Locate .env file at project root
env_file = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.

    All required settings must exist in .env.
    The application will fail to start if they are missing.
    """

    # Application
    APP_NAME: str = Field(..., description="Application name")
    DEBUG: bool = Field(..., description="Debug mode")

    # Security
    SECRET_KEY: str = Field(..., min_length=32, description="JWT signing key")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")

    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time"
    )

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
