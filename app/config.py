"""
Application configuration using Pydantic Settings.
Loads from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Database URL (fallback)
    DATABASE_URL: str = "mysql+aiomysql://readonly_user:password@localhost:3306/u271850780_crm_api"
    DB_POOL_SIZE: int = 10
    DB_POOL_RECYCLE: int = 3600
    
    # Separate DB config (recommended for special chars in password)
    DB2_HOST: Optional[str] = "82.25.121.78"
    DB2_PORT: int = 3306
    DB2_USERNAME: Optional[str] = "u271850780_crm"
    DB2_PASSWORD: Optional[str] = "=l7OsdtiqUC"
    DB2_DATABASE: Optional[str] = "u271850780_crm_api"
    
    # Mock Mode (for testing without database)
    USE_MOCK_DATA: bool = False  # Set to False when database is available
    
    # LLM - Direct Gemini API (not Vertex AI)
    GEMINI_API_KEY: str = "AIzaSyAjihqeNcvbdJGQuK0So8J_dOb0KQG4xIY"
    
    # API Limits
    MAX_LIMIT: int = 500
    DEFAULT_LIMIT: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields not defined


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

