# API Test Automation Framework

A Python API test automation framework built around pytest, httpx, and Pydantic, testing the
[ReqRes](https://reqres.in) REST API. Includes both mocked unit tests and live integration tests,
with Allure reporting and CI on every push.

## Tech Stack

- **Language:** Python 3.11+
- **Test runner:** pytest
- **HTTP client:** [httpx](https://www.python-httpx.org/) (sync)
- **Schema validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Config management:** pydantic-settings
- **Mocking:** [respx](https://lundberg.github.io/respx/)
- **Reporting:** [Allure](https://allurereport.org/)
- **CI/CD:** GitHub Actions

## Project Structure

```
src/
  clients/     # Service client classes (BaseClient, UserClient) wrapping API endpoints
  models/      # Pydantic models for requests/responses
  exceptions.py
  config.py    # Centralized settings via pydantic-settings
tests/
  unit/        # respx-mocked tests — no network calls
  api/         # Live tests against the real ReqRes API
```

## Running Locally

1. Install dependencies (including test/dev extras):
   ```bash
   pip install -e ".[dev]"
   ```

2. Set up your environment file:
   ```bash
   cp .env.example .env
   ```
   Then fill in a real `API_KEY` from [app.reqres.in](https://app.reqres.in) — required only
   for the live tests in `tests/api/`. Unit tests (`tests/unit/`) run with no key at all, since
   they mock the HTTP layer with `respx`.

3. Run the tests:
   ```bash
   pytest                  # everything
   pytest tests/unit       # unit tests only, no network/API key needed
   pytest tests/api        # live tests against the real API
   ```

4. Generate an Allure report locally:
   ```bash
   pytest --alluredir=allure-results
   allure generate allure-results --clean -o allure-report
   allure open allure-report   # or: open allure-report/index.html
   ```

## CI

Every push to `main` runs the full suite via [GitHub Actions](.github/workflows/api-tests.yml) and
publishes the Allure report to GitHub Pages — each run gets its own permanent link under `/runs/<run
number>/`, with `/latest/` always pointing at the newest one and the root page listing run history (see
the links at the top of this file). History is capped at the most recent 20 runs
(`PAGES_RETAIN_RUNS` in the workflow); older runs remain downloadable as build artifacts for ~90 days.
Pull request runs execute the tests but skip the Pages publish step, so they don't affect the shared
history.

📊 **[Latest Allure report](https://awareto.github.io/api-test-framework-py/latest/index.html)** ·
**[Browse all runs](https://awareto.github.io/api-test-framework-py/)** — tested against [ReqRes](https://reqres.in)