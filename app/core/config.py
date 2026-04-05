"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import json

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

    # CORS Settings - provide as JSON string in env or Python list in .env
    CORS_ORIGINS: Optional[str] = None

    # Server Settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        # Parse CORS_ORIGINS if it's a JSON string
        if isinstance(self.CORS_ORIGINS, str):
            try:
                self.CORS_ORIGINS = json.loads(self.CORS_ORIGINS)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, treat as single origin
                self.CORS_ORIGINS = [self.CORS_ORIGINS]
        elif self.CORS_ORIGINS is None:
            self.CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]

settings = Settings()
