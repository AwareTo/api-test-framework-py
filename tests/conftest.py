"""Shared pytest fixtures and Allure environment setup for the test suite."""

import logging
import os
from collections.abc import Generator, Iterator
from datetime import UTC, datetime
from pathlib import Path

import allure
import pytest
from faker import Faker

from src.clients.auth_client import AuthClient
from src.clients.user_client import UserClient
from src.config import Settings, settings
from src.models.user import UserCreate
from src.utils.logger import configure_logging

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
def auth_client() -> Iterator[AuthClient]:
    """Function-scoped AuthClient with guaranteed cleanup after each test."""
    client = AuthClient()
    yield client
    client.close()


@pytest.fixture
def random_user_payload() -> UserCreate:
    """A UserCreate populated with Faker-generated data, unique per invocation."""
    return UserCreate(name=_faker.name(), job=_faker.job())


@pytest.fixture(autouse=True)
def _capture_logs_for_allure(caplog: pytest.LogCaptureFixture) -> None:
    """Force every test to request `caplog`, and force it to DEBUG.

    Two effects, both needed for `pytest_runtest_makereport` below to attach a failure
    log to Allure: (1) requesting `caplog` here — autouse, on every test — means it's
    always present in `item.funcargs`, even though no test in this suite requests it
    directly; pytest only instantiates a fixture on demand, so without this the hook
    would find nothing to attach. (2) `set_level(DEBUG)` ensures a failure gets full
    detail regardless of the environment's configured handler level (CI's persisted
    `logs/test_run.jsonl` file stays at INFO — see `src/utils/logger.py`).
    """
    caplog.set_level(logging.DEBUG)


def pytest_configure(config: pytest.Config) -> None:
    """Configure structured logging, then write allure/environment.properties.

    Logging is configured in *every* process, including each pytest-xdist worker —
    `tests/unit` runs under `-n auto`, and that's exactly where the `BaseClient` HTTP
    calls worth logging execute. `worker_id` (from `workerinput`, present only on
    worker configs) is folded into the CI log filename so workers don't clobber each
    other's file.

    The environment.properties write, in contrast, must happen exactly once: every
    worker would otherwise race to write the same file. `workerinput` distinguishes a
    worker config from the controller (or a plain non-parallel run), so that write is
    guarded and skipped on workers.
    """
    worker_id = getattr(config, "workerinput", {}).get("workerid")
    configure_logging(worker_id=worker_id)

    if hasattr(config, "workerinput"):
        return

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


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    """Use each test's one-line docstring as its Allure report title.

    Replaces an explicit `@allure.title(...)` on every test: the docstring already
    has to describe what the test does, so it doubles as the title with no extra
    decorator. Tests without a docstring keep Allure's default (the test's node ID).

    Must run during the *call* phase, not fixture setup — an autouse fixture calling
    `allure.dynamic.title(...)` gets silently overwritten, because allure-pytest's own
    `pytest_runtest_setup` hook unconditionally resets the title from the item's name
    right after setup finishes, after any fixture has already run.
    """
    doc = item.function.__doc__ if isinstance(item, pytest.Function) else None
    if doc:
        allure.dynamic.title(doc.strip())
    return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """On a failing test, attach its captured log output to the Allure report.

    `caplog` is guaranteed present in `item.funcargs` by the autouse
    `_capture_logs_for_allure` fixture above; without that, `funcargs.get("caplog")`
    would be `None` here since none of this suite's tests request `caplog` directly.
    `funcargs` isn't part of `pytest.Item`'s typed interface (only function-based test
    items carry it at runtime), hence the `getattr` fallback rather than `item.funcargs`
    directly.
    """
    rep = yield
    if rep.when == "call" and rep.failed:
        caplog = getattr(item, "funcargs", {}).get("caplog")
        if caplog is not None and caplog.text:
            allure.attach(caplog.text, name="Failure Log", attachment_type=allure.attachment_type.TEXT)
    return rep
