"""Shared pytest fixtures and pytest-html reporting hooks for the test suite."""
from datetime import datetime, timezone
from typing import Iterator, List

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


def pytest_html_results_table_header(cells: List[str]) -> None:
    """Add "Timestamp" and "Environment" columns to the pytest-html results table."""
    cells.insert(2, "<th>Timestamp</th>")
    cells.insert(3, "<th>Environment</th>")


def pytest_html_results_table_row(report: pytest.TestReport, cells: List[str]) -> None:
    """Populate the "Timestamp" and "Environment" columns for each result row."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cells.insert(2, f"<td>{timestamp}</td>")
    cells.insert(3, f"<td>{settings.environment}</td>")
