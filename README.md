# API Test Automation Framework

![CI](https://github.com/AwareTo/api-test-framework-py/actions/workflows/api-tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Type checked](https://img.shields.io/badge/mypy-strict-blue)
![Lint](https://img.shields.io/badge/lint-ruff-red)
![Reports](https://img.shields.io/badge/reports-allure-orange)

A production-grade API test automation framework built around **pytest**, **httpx**, and
**Pydantic v2**, testing the [ReqRes](https://reqres.in) REST API. Typed service clients on a
resilient shared core, rich Allure reporting, and a CI/CD pipeline that publishes a live,
historical report site on every push — a reference architecture, not just a test suite.

📊 **[Latest Allure report](https://awareto.github.io/api-test-framework-py/latest/index.html)** ·
**[Browse all runs](https://awareto.github.io/api-test-framework-py/)**

## ✨ Features

### 🧱 Typed, layered architecture
- Service-client pattern abstracts every HTTP call behind typed methods; every response maps onto a
  **Pydantic v2** model, or raises a typed `SchemaValidationError` — never a leaked raw dict.
- A custom exception hierarchy maps HTTP status codes to typed exceptions (`NotFoundError`,
  `ValidationError`, `UnauthorizedError`, generic `APIError`).
- Centralized, typed settings via **pydantic-settings**, `.env`-driven, with `api_key` as
  `SecretStr` so it can never leak into a repr, log line, or Allure attachment.
- `mypy --strict` passes clean across the entire codebase.

### 🔁 Resilient by default
- Idempotent verbs (`GET`/`PUT`/`DELETE`) retry automatically with exponential backoff on transient
  `502`/`503`/`504` responses and on transport-level failures.
- `POST` is never retried — retrying an ambiguous create risks minting a duplicate resource.
- Exhausted retries re-raise the original exception unchanged; every attempt, including retries, is
  attached to the report — a flaky-but-passing run stays visible.

### 📊 Rich Allure reporting
- Every HTTP call is its own Allure step, with full request/response detail (headers, body, status,
  latency, timestamp) attached — for every attempt, not just the last.
- Sensitive headers (`x-api-key`, `Authorization`) and body fields (`password`) are redacted before
  anything is attached, since reports publish to a public site.
- Reports auto-publish on every push: a permanent link per run, a `latest` redirect, and a history
  page of every retained run with pass/fail counts and commit.
- A failing test automatically carries its own captured structured log as a report attachment.

### 📋 Structured logging
- **structlog** piped through stdlib `logging`, attached at the root logger so every module's
  logger propagates correctly and pytest's `caplog` can capture it for report attachment.
- Colorized console output locally; one JSON object per line to a per-worker file in CI — INFO in
  the persisted file, full DEBUG captured for a failing test's report attachment either way.

### ⚡ Fast, safe parallel execution
- Fully mocked unit tests run in parallel via **pytest-xdist** (`-n auto`); live tests against the
  real API stay serial (`-n 1`) so the suite never rate-limits a shared external service.
- Both are independently configurable in CI, right down to a manual `workflow_dispatch` override.

### 🛡️ Quality gates, enforced twice
- `ruff` (lint + format) and `mypy --strict` run identically in a local `pre-commit` hook and a
  dedicated CI `lint` job — nothing reaches `main` unchecked either way.

### 🔍 Contract testing
- A dedicated `tests/contract/` suite verifies response shape (fields/types) and payload tolerance
  (required fields still accepted, extra fields still tolerated, invalid payloads still rejected)
  against the live provider — catching a silent contract drift that functional tests wouldn't.

### 🚀 CI/CD, end to end
- GitHub Actions: independent `lint` job alongside `test` (unit → live API → Allure → publish), on
  every push and pull request.
- Pull requests run the full suite but skip publishing, keeping `main`'s shared report history
  clean. History is capped and pruned automatically (last 20 runs); older runs stay downloadable as
  build artifacts.

## Tech Stack

- **Language:** Python 3.11+
- **Test runner:** pytest (+ pytest-xdist)
- **HTTP client:** [httpx](https://www.python-httpx.org/)
- **Schema validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Config management:** pydantic-settings
- **Mocking:** [respx](https://lundberg.github.io/respx/)
- **Test data:** Faker
- **Logging:** structlog
- **Reporting:** [Allure](https://allurereport.org/)
- **Static analysis:** ruff, mypy (strict)
- **Local quality gate:** pre-commit
- **CI/CD:** GitHub Actions + GitHub Pages

## Project Structure

```
src/
  clients/     # BaseClient (retries, redaction, validation) → UserClient, AuthClient
  models/      # Pydantic request/response models
  utils/       # structlog ↔ stdlib logging integration
  exceptions.py
  config.py    # Centralized settings via pydantic-settings
tests/
  unit/        # respx-mocked, zero network calls, parallel
  api/         # Live functional tests against the real API
  contract/    # Live wire-shape/contract tests against the real API
  steps/       # Shared Allure step layer (endpoint + helper, per domain) used by api/ and contract/
scripts/
  build_pages_site.py   # Merges each CI run's Allure report into the GitHub Pages history site
```

See [PROJECT_REPORT.md](PROJECT_REPORT.md) for the full architectural write-up, request-lifecycle
walkthrough, and test-suite breakdown.

## Running Locally

```bash
pip install -e ".[dev]"       # install, including test/dev extras
pre-commit install            # wire up the local quality gate (one-time)
cp .env.example .env          # then fill in a real API_KEY from app.reqres.in
```

```bash
pytest                        # everything
pytest tests/unit             # unit tests only — no network/API key needed
pytest tests/api              # live functional tests
pytest tests/contract         # live contract tests
pytest tests/unit -n auto     # unit tests in parallel
```

```bash
ruff check . && ruff format --check . && mypy   # the same quality gate CI runs
```

```bash
pytest --alluredir=allure-results && allure generate allure-results --clean -o allure-report
allure open allure-report
```

## CI

Every push to `main` runs the full suite via [GitHub Actions](.github/workflows/api-tests.yml) —
an independent `lint` job alongside `test` — and publishes the Allure report to GitHub Pages, with
a permanent link per run and a capped, pruned history (see the links at the top of this file).
Pull requests run the tests but skip publishing.

## Architecture

```
tests/            → what to verify (docstring + a few one-line step calls, nothing else)
tests/steps/      → how to do it (every @allure.step lives here — endpoint calls + assertions)
src/clients/      → typed service clients, one per API domain (UserClient, AuthClient, ...)
BaseClient        → shared core: retries, redaction, Allure attachment, schema validation
```

Every layer knows only the layer below it. Nothing above `BaseClient` touches raw `httpx` or raw
JSON — every response is mapped onto a Pydantic model or a typed exception before a test ever sees
it. Adding a new API domain means one client class, its models, and a `tests/steps/` package —
zero changes to retry logic, reporting, or config. Test files under `tests/steps/` are further
split by **domain** (`auth/`, `user/`) and by **concern** (`*_endpoint.py` for API actions,
`*_helper.py` for assertions), so shared logic — like a single `assert_rejected_with_400` used by
both functional and contract tests — has exactly one home instead of quietly duplicating.

Business flows (`tests/api/`) always go through typed request models, so a malformed payload is
structurally impossible to send. A separate `tests/contract/` suite deliberately bypasses those
typed methods to probe the provider's raw wire-level shape and tolerance — a real behavioral split,
not just file organization.
