from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Task Management API"
    debug: bool = True
    secret_key: str = "supersecret"

    class Config:
        env_file = ".env"


settings = Settings()
