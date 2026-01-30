"""
Configuration Module for SaaS Application
==========================================
Loads and validates all environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # App Settings
    APP_NAME: str = os.getenv("APP_NAME", "AI Social Automation")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_social.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # LLM Defaults
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
    DEFAULT_LLM_TEMPERATURE: float = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "0.7"))
    
    # Scheduler
    SCHEDULER_CHECK_INTERVAL: int = int(os.getenv("SCHEDULER_CHECK_INTERVAL", "60"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate critical settings."""
        errors = []
        if cls.SECRET_KEY == "change-this-secret-key":
            errors.append("SECRET_KEY must be changed from default")
        if not cls.ENCRYPTION_KEY:
            errors.append("ENCRYPTION_KEY is required for API key encryption")
        return errors


settings = Settings()
