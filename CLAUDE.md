# Project Guidelines: API Test Automation Framework

> Tech stack, project structure, and test execution commands live in [README.md](README.md) —
> that's the single source of truth for those; don't duplicate them here.

## Architecture Rules
- Use strict type hinting on all functions and methods (`from typing import ...`).
- Never parse raw JSON directly in test files; always map API responses to Pydantic models.
- Abstract API endpoints behind service client classes (e.g., `UserClient`) located in `src/clients/`.
- Store Pydantic models in `src/models/` and framework exceptions in `src/exceptions.py`.
- Keep environment configuration centralized in `src/config.py` using `pydantic-settings`.
