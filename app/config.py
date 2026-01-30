"""
Configuration Management Module
===============================
Loads and validates environment variables for the application.
Uses python-dotenv to load from .env file and provides type-safe access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
# Look for .env in the project root directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """
    Application settings loaded from environment variables.
    All sensitive data should come from .env file, never hardcoded.
    """
    
    # =========================================
    # LLM Configuration
    # =========================================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_CONTENT_TOKENS: int = int(os.getenv("MAX_CONTENT_TOKENS", "1000"))
    
    # =========================================
    # Database Configuration
    # =========================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./social_automation.db")
    
    # =========================================
    # Server Configuration
    # =========================================
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # =========================================
    # LinkedIn Configuration
    # =========================================
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    LINKEDIN_REDIRECT_URI: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/linkedin/callback")
    
    # =========================================
    # Facebook/Instagram Configuration
    # =========================================
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    
    # =========================================
    # Scheduler Configuration
    # =========================================
    SCHEDULER_CHECK_INTERVAL: int = int(os.getenv("SCHEDULER_CHECK_INTERVAL", "60"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that required settings are configured.
        Returns a list of missing/invalid settings.
        """
        errors = []
        
        # Check LLM configuration
        if not cls.OPENAI_API_KEY and cls.LLM_PROVIDER == "openai":
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        
        return errors
    
    @classmethod
    def is_linkedin_configured(cls) -> bool:
        """Check if LinkedIn credentials are configured."""
        return bool(cls.LINKEDIN_ACCESS_TOKEN)
    
    @classmethod
    def is_facebook_configured(cls) -> bool:
        """Check if Facebook credentials are configured."""
        return bool(cls.FACEBOOK_ACCESS_TOKEN and cls.FACEBOOK_PAGE_ID)
    
    @classmethod
    def is_instagram_configured(cls) -> bool:
        """Check if Instagram credentials are configured."""
        return bool(cls.FACEBOOK_ACCESS_TOKEN and cls.INSTAGRAM_BUSINESS_ACCOUNT_ID)


# Create a singleton instance for easy import
settings = Settings()
