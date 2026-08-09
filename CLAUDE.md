# Project Guidelines: API Test Automation Framework

## Tech Stack
- Language: Python 3.11+
- Test Runner: pytest
- HTTP Client: httpx (synchronous primary, async-ready)
- Data & Schema Validation: Pydantic v2
- Config Management: pydantic-settings
- Mocking: respx
- Reporting: pytest-html

## Architecture Rules
- Use strict type hinting on all functions and methods (`from typing import ...`).
- Never parse raw JSON directly in test files; always map API responses to Pydantic models.
- Abstract API endpoints behind service client classes (e.g., `UserClient`) located in `src/clients/`.
- Store Pydantic models in `src/models/` and framework exceptions in `src/exceptions.py`.
- Keep environment configuration centralized in `src/config.py` using `pydantic-settings`.

## Test Execution Commands
- Run all tests: `pytest`
- Run unit tests only: `pytest tests/unit`
- Run integration tests: `pytest tests/api`
- Generate HTML report: `pytest --html=report.html --self-contained-html`
