"""Centralized environment configuration using pydantic-settings.

Values are sourced from environment variables (and an optional .env file),
letting the framework target different environments (dev/staging/prod)
without code changes.
"""
from typing import Optional

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    base_url: HttpUrl = HttpUrl("https://reqres.in")
    api_timeout: int = 10
    environment: str = "dev"
    api_key: Optional[SecretStr] = None


settings = Settings()
