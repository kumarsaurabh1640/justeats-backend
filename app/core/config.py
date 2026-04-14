"""Application configuration using Pydantic Settings.

Environment variables are loaded from .env file.
All settings can be overridden via environment variables.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        APP_NAME: Display name for the application.
        DEBUG: Enable debug mode (exposes additional info in responses).
        DATABASE_URL: Async PostgreSQL connection string.
        SECRET_KEY: JWT signing key (must be changed in production).
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token validity period.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token validity period.
        CORS_ORIGINS: List of allowed CORS origins.
        SMTP_*: Email configuration for password reset.
        MOSTLY_ORDERED_THRESHOLD: Order count to mark items as "Mostly Ordered".
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "JustEats"
    DEBUG: bool = False

    # DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/justeats"
    DATABASE_URL : str ="postgresql+asyncpg://postgres:root@postgres:5432/justeats"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    MOSTLY_ORDERED_THRESHOLD: int = 10


settings = Settings()
