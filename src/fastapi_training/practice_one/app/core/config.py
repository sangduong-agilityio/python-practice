from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Task Management API"
    debug: bool = True

    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
