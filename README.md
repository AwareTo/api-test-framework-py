# API Test Automation Framework

![CI](https://github.com/AwareTo/api-test-framework-py/actions/workflows/api-tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Type checked](https://img.shields.io/badge/mypy-strict-blue)
![Lint](https://img.shields.io/badge/lint-ruff-red)
![Reports](https://img.shields.io/badge/reports-allure-orange)

A production-grade API test automation framework built around **pytest**, **httpx**, and **Pydantic**,
testing the [ReqRes](https://reqres.in) REST API. Typed service clients, automatic retry resilience,
rich Allure reporting with secret redaction, parallel test execution, and a CI/CD pipeline that
publishes a live report site on every push — all wired together end to end.

📊 **[Latest Allure report](https://awareto.github.io/api-test-framework-py/latest/index.html)** ·
**[Browse all runs](https://awareto.github.io/api-test-framework-py/)** — tested against [ReqRes](https://reqres.in)

## ✨ Features

### 🧱 Typed, layered architecture
- Service-client pattern (`BaseClient` → `UserClient`, `AuthClient`) abstracts every HTTP call behind
  typed methods — no test ever touches raw `httpx` or raw JSON.
- Every response is mapped onto a **Pydantic v2** model; a schema mismatch raises a
  framework-specific `SchemaValidationError` instead of leaking a raw dict or a bare pydantic error.
- Centralized, typed settings via **pydantic-settings** (`.env`-driven), with `api_key` stored as
  `SecretStr` so it can never leak into a repr, a log line, or an Allure attachment by accident.
- A custom exception hierarchy maps HTTP status codes to typed exceptions —
  `NotFoundError` (404), `ValidationError` (422), `UnauthorizedError` (401), and a generic `APIError`
  for everything else.
- Strict type hints throughout — `mypy --strict` passes clean across both `src/` and `tests/`.

### 🔁 Resilient by default
- Idempotent verbs (`GET`/`PUT`/`DELETE`) are automatically retried, with exponential backoff, on
  transient `502`/`503`/`504` responses **and** on transport-level failures (timeouts, dropped
  connections, connection resets).
- `POST` is deliberately never retried — replaying a create after an ambiguous failure risks minting
  a duplicate resource, so the framework refuses to guess.
- Exhausted retries re-raise the **original** exception unchanged — no wrapping that hides the real
  cause from the test output.

### 📊 Rich Allure reporting
- Every HTTP call runs as its own Allure step, and every attempt — including retries — attaches full
  request/response detail: method, URL, headers, body, status code, latency, and timestamp.
- Sensitive headers (`x-api-key`, `Authorization`) are automatically redacted before anything is
  attached, since reports are published to a public GitHub Pages site.
- Environment metadata (target environment, base URL, Python version) is stamped into every report
  run automatically, so a report is self-describing months later.
- Reports auto-publish on every push to `main`, with a **permanent link per run**, a `latest`
  redirect, and a history page listing every retained run with its pass/fail counts and commit.

### ⚡ Fast, safe parallel execution
- Unit tests (mocked with `respx`, zero network calls, zero shared state) run in parallel via
  **pytest-xdist** (`-n auto`).
- Live tests against the real API stay **serial by default** (`-n 1`) so the suite never
  rate-limits a shared external service.
- Both are independently configurable in CI — `UNIT_PYTEST_WORKERS` and `API_PYTEST_WORKERS` — right
  down to a manual `workflow_dispatch` override, so bumping one can never accidentally parallelize
  the other.

### 🛡️ Quality gates, enforced twice
- `ruff` (lint + format, covering pycodestyle/pyflakes/isort/pyupgrade/bugbear) and `mypy --strict`
  run identically in **two independent places**: a local `pre-commit` git hook and a dedicated CI
  `lint` job — nothing reaches `main` unchecked, whether or not the hook fired locally.
- `Faker`-generated payloads keep test data unique per run instead of relying on brittle hardcoded
  fixtures.

### 🚀 CI/CD, end to end
- GitHub Actions pipeline: **lint → test (with Allure) → publish**, running on every push and pull
  request.
- Pull request runs execute the full suite but skip publishing, so the shared report history on
  `main` stays clean.
- History is capped and pruned automatically (last 20 runs retained on the site); older runs remain
  downloadable as build artifacts.

## Tech Stack

- **Language:** Python 3.11+
- **Test runner:** pytest (+ pytest-xdist for parallel execution)
- **HTTP client:** [httpx](https://www.python-httpx.org/) (sync)
- **Schema validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Config management:** pydantic-settings
- **Mocking:** [respx](https://lundberg.github.io/respx/)
- **Test data:** Faker
- **Reporting:** [Allure](https://allurereport.org/)
- **Static analysis:** ruff (lint + format), mypy (strict mode)
- **Local quality gate:** pre-commit
- **CI/CD:** GitHub Actions + GitHub Pages

## Project Structure

```
src/
  clients/     # Service client classes (BaseClient, UserClient, AuthClient) wrapping API endpoints
  models/      # Pydantic models for requests/responses
  exceptions.py
  config.py    # Centralized settings via pydantic-settings
tests/
  unit/        # respx-mocked tests — no network calls
  api/         # Live tests against the real ReqRes API
scripts/
  build_pages_site.py   # Merges each CI run's Allure report into the GitHub Pages site
```

## Running Locally

1. Install dependencies (including test/dev extras):
   ```bash
   pip install -e ".[dev]"
   ```

2. Wire up the local quality gate (one-time):
   ```bash
   pre-commit install
   ```

3. Set up your environment file:
   ```bash
   cp .env.example .env
   ```
   Then fill in a real `API_KEY` from [app.reqres.in](https://app.reqres.in) — required only
   for the live tests in `tests/api/`. Unit tests (`tests/unit/`) run with no key at all, since
   they mock the HTTP layer with `respx`.

4. Run the tests:
   ```bash
   pytest                       # everything
   pytest tests/unit            # unit tests only, no network/API key needed
   pytest tests/api             # live tests against the real API
   pytest tests/unit -n auto    # unit tests in parallel (pytest-xdist)
   ```
   Unit tests are safe to parallelize — no shared state, and xdist runs each worker as its own
   process. Live tests against `tests/api/` are kept serial in CI (`-n 1`) to avoid rate-limiting
   the real API. In CI, override each independently via `UNIT_PYTEST_WORKERS` / `API_PYTEST_WORKERS`
   (or the matching inputs on a manual `workflow_dispatch` run) — they're separate knobs on purpose,
   so bumping unit-test parallelism can never accidentally also parallelize the live-API step.

5. Run the quality gate manually (same checks CI runs):
   ```bash
   ruff check .
   ruff format --check .
   mypy
   ```

6. Generate an Allure report locally:
   ```bash
   pytest --alluredir=allure-results
   allure generate allure-results --clean -o allure-report
   allure open allure-report   # or: open allure-report/index.html
   ```

## CI

Every push to `main` runs the full suite via [GitHub Actions](.github/workflows/api-tests.yml) —
an independent `lint` job (ruff + mypy) alongside the `test` job — and publishes the Allure report
to GitHub Pages. Each run gets its own permanent link under `/runs/<run number>/`, with `/latest/`
always pointing at the newest one and the root page listing run history (see the links at the top of
this file). History is capped at the most recent 20 runs (`PAGES_RETAIN_RUNS` in the workflow);
older runs remain downloadable as build artifacts for ~90 days. Pull request runs execute the tests
but skip the Pages publish step, so they don't affect the shared history.
