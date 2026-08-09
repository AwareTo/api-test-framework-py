"""Service client abstracting the ReqRes /users endpoint."""
from __future__ import annotations

from src.clients.base_client import BaseClient
from src.config import settings
from src.models.user import UserCreate, UserCreateResponse, UserResponse


class UserClient(BaseClient):
    """Wraps HTTP calls to the ReqRes /api/users endpoint and maps responses to Pydantic models."""

    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        super().__init__(
            base_url=base_url or str(settings.base_url),
            timeout=timeout if timeout is not None else settings.api_timeout,
            api_key=settings.api_key.get_secret_value() if settings.api_key else None,
        )

    def get_user(self, user_id: int) -> UserResponse:
        response = self.get(f"/api/users/{user_id}")
        return UserResponse.model_validate(response.json()["data"])

    def create_user(self, user_data: UserCreate) -> UserCreateResponse:
        response = self.post("/api/users", json=user_data.model_dump())
        return UserCreateResponse.model_validate(response.json())

    def delete_user(self, user_id: int) -> bool:
        response = self.delete(f"/api/users/{user_id}")
        return response.status_code == 204
