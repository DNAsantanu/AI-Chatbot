"""
Application configuration using Pydantic Settings.
Loads from .env file and environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "AI ChatBot"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- LLM Providers ---
    groq_api_key: Optional[str] = None
    huggingfacehub_api_token: Optional[str] = None

    # --- Web Search ---
    tavily_api_key: Optional[str] = None

    # --- Model Configuration ---
    llm_model_name: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    memory_window_size: int = 10

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_url: str = "http://localhost:8000"

    # --- CORS ---
    cors_origins: list[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
