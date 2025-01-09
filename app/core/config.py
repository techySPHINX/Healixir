from pydantic import  BaseSettings
from typing import List, Any
import os

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "HealXir"
    APP_VERSION: str = "1.0.0"

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./default.db")

    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "defaulkey")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Firebase Settings
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase_credentials.json")

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[Any] = ["*"]  # Update this in production

    # Environment Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # Options: 'development', 'production'

    class Config:
        env_file = ".env"  # Load environment variables from .env file


# Singleton instance of Settings
settings = Settings()
