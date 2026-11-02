"""
AgentTutor application configuration.
All settings are loaded from environment variables; no secrets are hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Flask ─────────────────────────────────────────────────────────────────
    flask_env: str = "development"
    flask_debug: bool = True
    secret_key: str = Field(default="dev-secret-change-in-production")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://agenttutor:password@localhost:5432/agenttutor_dev"
    )
    test_database_url: str = Field(
        default="postgresql://agenttutor:password@localhost:5432/agenttutor_test"
    )

    # ── LLM Provider ─────────────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic", "google", "mock"] = "mock"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3

    # ── Embedding Provider ────────────────────────────────────────────────────
    embedding_provider: Literal["openai", "sentence_transformers", "mock"] = "mock"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # ── Retrieval ─────────────────────────────────────────────────────────────
    enable_vector_search: bool = False
    retrieval_top_k: int = 5

    # ── File Upload ───────────────────────────────────────────────────────────
    max_upload_size_mb: int = 25
    allowed_extensions: str = "pdf,txt,md,docx"
    upload_dir: str = "./uploads"

    # ── Security ──────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173"
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-in-production")
    jwt_access_token_expires_minutes: int = 60
    jwt_refresh_token_expires_days: int = 30

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_default: str = "200 per day, 50 per hour"
    rate_limit_messages: str = "30 per minute"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Code Execution ────────────────────────────────────────────────────────
    enable_code_execution: bool = False
    code_runner_timeout_seconds: int = 10

    @property
    def allowed_extension_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @field_validator("secret_key")
    @classmethod
    def warn_default_secret(cls, v: str) -> str:
        if v in ("dev-secret-change-in-production", "change-me-use-a-long-random-string"):
            import warnings
            warnings.warn(
                "SECRET_KEY is set to a development default. "
                "Set a strong SECRET_KEY in production.",
                stacklevel=2,
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
