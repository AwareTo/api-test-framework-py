"""Unit tests for the Settings configuration module."""
from pydantic import HttpUrl, SecretStr
from pytest import MonkeyPatch

from src.config import Settings, settings


def test_settings_singleton_uses_default_values() -> None:
    """The module-level `settings` singleton should load with the documented defaults
    when no environment variables or .env overrides are present beyond what ships
    in the repo's own .env file (which mirrors the defaults)."""
    assert settings.base_url == HttpUrl("https://reqres.in")
    assert settings.api_timeout == 10
    assert settings.environment == "dev"


def test_defaults_load_correctly_without_env_file(monkeypatch: MonkeyPatch) -> None:
    """With no .env file and no environment variables, fields fall back to their
    declared defaults."""
    for var in ("BASE_URL", "API_TIMEOUT", "ENVIRONMENT", "API_KEY"):
        monkeypatch.delenv(var, raising=False)

    result = Settings(_env_file=None)

    assert result.base_url == HttpUrl("https://reqres.in")
    assert result.api_timeout == 10
    assert result.environment == "dev"
    assert result.api_key is None


def test_environment_variables_override_defaults(monkeypatch: MonkeyPatch) -> None:
    """Environment variables take priority over field defaults."""
    monkeypatch.setenv("BASE_URL", "https://staging.example.com")
    monkeypatch.setenv("API_TIMEOUT", "30")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("API_KEY", "s3cr3t")

    result = Settings(_env_file=None)

    assert result.base_url == HttpUrl("https://staging.example.com")
    assert result.api_timeout == 30
    assert result.environment == "staging"
    assert isinstance(result.api_key, SecretStr)
    assert result.api_key.get_secret_value() == "s3cr3t"


def test_api_key_defaults_to_none_and_is_optional(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)

    result = Settings(_env_file=None)

    assert result.api_key is None


def test_api_key_is_kept_secret_in_repr(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "super-secret-value")

    result = Settings(_env_file=None)

    assert "super-secret-value" not in repr(result.api_key)
    assert result.api_key.get_secret_value() == "super-secret-value"
