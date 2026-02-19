from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/cryptodash"
    REDIS_URL: str = "redis://redis:6379"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"

    JWT_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"

    class Config:
        env_file = ".env"


settings = Settings()
