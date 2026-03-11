"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Settings
    API_TITLE: str = "LegalAid India API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "REST API for Legal Aid India platform"
    DEBUG: bool = False

    # Database Settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/legal_aid_india"
    DB_ECHO: bool = False  # Log SQL queries

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    # Server Settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
