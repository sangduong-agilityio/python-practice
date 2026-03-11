from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


env_file = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_file)


class Settings(BaseSettings):
    """Application settings loaded from .env file.

    Important: All required settings must be defined in .env file.
    The application will fail to start if required settings are missing.
    """

    # Required settings (no defaults) - must come from .env
    app_name: str = Field(..., description="Application name")
    debug: bool = Field(..., description="Debug mode")
    SECRET_KEY: str = Field(..., min_length=32,
                            description="Secret key for JWT signing")

    # Optional settings with safe defaults
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Token expiration time in minutes")

    class Config:
        env_file = str(env_file)
        env_file_encoding = "utf-8"


settings = Settings()
