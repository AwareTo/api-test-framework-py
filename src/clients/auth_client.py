"""Service client abstracting the ReqRes /register and /login endpoints."""

from __future__ import annotations

from src.clients.base_client import BaseClient
from src.config import settings
from src.models.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse


class AuthClient(BaseClient):
    """Wraps HTTP calls to the ReqRes /api/register and /api/login endpoints and maps
    responses to Pydantic models.

    Deliberately mirrors UserClient's constructor rather than sharing it via BaseClient:
    each concrete client resolves its own settings independently so BaseClient stays
    generic (it has no knowledge of the app's Settings model)."""

    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        super().__init__(
            base_url=base_url or str(settings.base_url),
            timeout=timeout if timeout is not None else settings.api_timeout,
            api_key=settings.api_key.get_secret_value() if settings.api_key else None,
        )

    def register(self, credentials: RegisterRequest) -> RegisterResponse:
        response = self.post("/api/register", json=credentials.model_dump())
        return self._validate(RegisterResponse, response.json())

    def login(self, credentials: LoginRequest) -> LoginResponse:
        response = self.post("/api/login", json=credentials.model_dump())
        return self._validate(LoginResponse, response.json())
