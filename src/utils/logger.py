"""Structured logging setup: structlog piped through stdlib logging so pytest's
`caplog` fixture (which only sees stdlib `logging` records) can capture everything
this framework logs and attach it to a failing test's Allure report.

Two output modes, chosen automatically by environment:
- Local (default): colorized, human-readable output on stdout, DEBUG and up.
- CI (`CI=true`, set automatically by GitHub Actions): one JSON object per line,
  INFO and up, written to `logs/test_run.jsonl` — kept off stdout so CI output stays
  readable, and uploaded as a build artifact when a run fails.

The underlying root logger and structlog's own filtering are always left at DEBUG;
only each *handler* enforces the INFO-in-CI/DEBUG-locally split. This is deliberate:
it's what lets `tests/conftest.py`'s autouse `caplog.set_level(logging.DEBUG)` capture
full DEBUG detail for a failing test's Allure attachment even in CI, where the
persisted `logs/test_run.jsonl` file itself stays at INFO. If the logger or structlog's
filter were pinned to INFO in CI, DEBUG records would never be created in the first
place and no amount of `caplog.set_level()` could recover them.

Handlers are attached to the *root* stdlib logger, not to a single named one. Every
`get_logger(__name__)` call in application code (e.g. `BaseClient`'s module-level
`_logger = get_logger(__name__)`) creates its own distinct stdlib logger via
`structlog.stdlib.LoggerFactory()`; a logger with no handler of its own only reaches
ours by *propagating up to root* — never sideways to a differently-named logger. Root
is therefore the only attachment point that works for every caller regardless of name.
`structlog.stdlib.add_logger_name` in the processor chain puts that name back into
each record (as a `logger` field) so output stays attributable per module.

`get_logger()` deliberately returns the plain, un-bound `structlog.get_logger(name)`
proxy — no `.bind()` call on it here. `get_logger(__name__)` at module scope runs at
*import* time, which (via `conftest.py`'s own top-level imports of the service clients)
happens before `pytest_configure` has called `configure_logging()`. `structlog`'s lazy
proxy defers picking up the configured processors/factory until the first actual log
call, exactly to make that ordering safe — but calling `.bind()` on the proxy forces
immediate resolution against whatever config (or lack of it) is active *right then*,
silently locking every subsequent log call from that logger onto structlog's
unconfigured defaults (a raw print, never touching our stdlib handlers at all). Keeping
`get_logger()` bind-free preserves the laziness that makes deferred configuration work.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import cast

import structlog

# Third-party loggers that propagate to root by default and would otherwise flood our
# handlers (and the CI JSONL file) with connection-level chatter unrelated to this
# framework's own request/response events.
_NOISY_THIRD_PARTY_LOGGERS = ("httpx", "httpcore")


def configure_logging(worker_id: str | None = None) -> None:
    """Configure the root stdlib logger and wire structlog to it.

    Safe to call more than once in the same process (existing handlers are cleared
    first) — `tests/conftest.py` calls this from `pytest_configure`, which fires once
    per pytest-xdist worker process as well as for a plain, non-parallel run.

    `worker_id` is the xdist worker id (e.g. "gw0") when running under `-n`, so each
    worker gets its own CI log file (`logs/test_run.gw0.jsonl`) instead of every worker
    process racing to write the same one. Leave it `None` for a plain run — the file is
    then just `logs/test_run.jsonl`.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)

    for name in _NOISY_THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    is_ci = os.getenv("CI", "false").lower() == "true"

    handler: logging.Handler
    if is_ci:
        Path("logs").mkdir(parents=True, exist_ok=True)
        suffix = f".{worker_id}" if worker_id else ""
        handler = logging.FileHandler(f"logs/test_run{suffix}.jsonl")
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(processor=structlog.processors.JSONRenderer())
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(processor=structlog.dev.ConsoleRenderer(colors=True))
        )

    root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger routed through the stdlib root logger that
    `configure_logging` sets up, tagged with `name` (typically a module's
    `__name__`) via the `add_logger_name` processor.

    See the module docstring for why this must NOT call `.bind()` on the result.
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
