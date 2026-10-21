"""Typed settings loaded from environment variables / ``.env`` (prefix ``APP_``)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    name: str = "Starter API"
    env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="dev-only-insecure-secret-change-me-0123456789", min_length=32)

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    db_echo: bool = False
    redis_url: str | None = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=14, ge=1)

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]
    log_level: str = "INFO"
    log_json: bool = True

    first_superuser_email: str | None = None
    first_superuser_password: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalise_database_url(cls, value: object) -> object:
        """Managed Postgres providers (Render, Heroku-style) hand out ``postgres://`` or
        ``postgresql://`` URLs; route them through the asyncpg driver this app uses."""
        if isinstance(value, str):
            for prefix in ("postgres://", "postgresql://"):
                if value.startswith(prefix):
                    return "postgresql+asyncpg://" + value[len(prefix) :]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
