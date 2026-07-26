"""Configuration management for NexusMind."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "NexusMind"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/nexusmind"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

    # Security
    secret_key: str = "change-me-in-production-use-strong-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days
    api_key_header: str = "X-API-Key"

    # LLM Providers
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"

    # ChromaDB
    chromadb_url: str = ""  # Remote ChromaDB URL (e.g., http://chromadb:8000)
    chromadb_persist_directory: str = "./data/chromadb"
    chromadb_collection_name: str = "nexusmind_memory"

    # Sandbox
    sandbox_docker_image: str = "nexusmind-sandbox:latest"
    sandbox_timeout_seconds: int = 300
    sandbox_max_concurrent: int = 10

    # Streaming
    sse_heartbeat_seconds: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 100

    # Paths
    workspace_root: Path = Path("./workspace")
    plugins_directory: Path = Path("./plugins")
    temp_directory: Path = Path("/tmp/nexusmind")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "json"

    def get_database_url_sync(self) -> str:
        """Get sync database URL for Alembic."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
