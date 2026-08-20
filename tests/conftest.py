"""Shared pytest fixtures and Allure environment setup for the test suite."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from faker import Faker

from src.clients.user_client import UserClient
from src.config import Settings, settings
from src.models.user import UserCreate

_faker = Faker()


@pytest.fixture(scope="session")
def config() -> Settings:
    """Session-scoped access to the centralized environment settings."""
    return settings


@pytest.fixture
def user_client() -> Iterator[UserClient]:
    """Function-scoped UserClient with guaranteed cleanup after each test."""
    client = UserClient()
    yield client
    client.close()


@pytest.fixture
def random_user_payload() -> UserCreate:
    """A UserCreate populated with Faker-generated data, unique per invocation."""
    return UserCreate(name=_faker.name(), job=_faker.job())


def pytest_configure(config: pytest.Config) -> None:
    """Write allure/environment.properties so the report shows target env metadata."""
    alluredir = config.getoption("--alluredir", default=None, skip=True)
    if not alluredir:
        return

    props = {
        "Environment": settings.environment,
        "Base URL": str(settings.base_url),
        "Executed At": datetime.now(UTC).isoformat(timespec="seconds"),
        "Python": os.popen("python --version").read().strip(),  # noqa: S605
    }

    env_file = Path(alluredir) / "environment.properties"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(
        "\n".join(f"{k}={v}" for k, v in props.items()) + "\n",
        encoding="utf-8",
    )
