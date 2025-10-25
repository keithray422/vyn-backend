from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Vyn"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:admin123@localhost:5432/vyn_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
