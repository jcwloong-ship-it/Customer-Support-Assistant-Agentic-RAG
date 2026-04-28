"""Application settings loaded from environment variables / .env file."""

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI provider
    ai_provider: Literal["openai", "anthropic"] = Field(default="openai", env="AI_PROVIDER")

    openai_api_key:       str   = Field(default="", env="OPENAI_API_KEY")
    openai_embed_model:   str   = Field(default="text-embedding-3-small", env="OPENAI_EMBED_MODEL")
    openai_chat_model:    str   = Field(default="gpt-4o", env="OPENAI_CHAT_MODEL")

    anthropic_api_key:    str   = Field(default="", env="ANTHROPIC_API_KEY")
    anthropic_chat_model: str   = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_CHAT_MODEL")

    # Google (optional — required only for Calendar / Gmail tools)
    google_calendar_email: str = Field(default="", env="GOOGLE_CALENDAR_EMAIL")

    # Agent tuning
    temperature:          float = Field(default=0.1)
    max_agent_iterations: int   = Field(default=5)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
