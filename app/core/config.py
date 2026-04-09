"""
Central configuration.

pydantic-settings reads values from environment variables first,
then falls back to the .env file. The app will not start if a required
variable is missing -- that's intentional, better to fail fast at boot
than get a KeyError at 3am in production.
"""

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS -- stored as a JSON list in the env file
    CORS_ORIGINS: list[AnyHttpUrl] = []

    # Email -- optional, sending is skipped when SMTP_USER is blank
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "Task Manager"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
