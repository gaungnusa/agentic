from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql://orchestrator_admin:AdminBatuPassword2026!@localhost:54320/batu_networks_erp_ai"
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_PROVIDER: str = "openai_compatible"  # Pilihan: 'openai_compatible', 'ollama', atau 'anthropic'
    OPENAI_BASE_URL: str = "https://ai.sumopod.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "qwen3.7-flash-2026-07-15"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    APP_PORT: int = 8000
    ALLOWED_ENTITIES: List[str] = ["SG", "VN", "KR", "IN", "JP"]
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()