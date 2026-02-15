"""Nutrition Bot - Production Configuration"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Bot
    bot_token: str
    
    # OpenAI API (for GPT-4 analysis)
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Database
    database_path: Path = Path("/data/.openclaw/workspace/nutrition_bot_v2/nutrition.db")
    
    # LLM
    model_name: str = "moonshot/kimi-k2.5"
    max_tokens: int = 1000
    temperature: float = 0.3
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 20
    
    # Logging
    log_level: str = "INFO"
    
    # OpenAI (for Whisper fallback)
    openai_api_key: str = ""
    
    # GROQ (free Whisper)
    groq_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
