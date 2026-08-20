"""Service client abstracting the ReqRes /users endpoint."""
from __future__ import annotations

from typing import Any, Type, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from src.clients.base_client import BaseClient
from src.config import settings
from src.exceptions import SchemaValidationError
from src.models.user import UserCreate, UserCreateResponse, UserResponse

ModelT = TypeVar("ModelT", bound=BaseModel)


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
        return self._validate(UserResponse, response.json()["data"])

    def create_user(self, user_data: UserCreate) -> UserCreateResponse:
        response = self.post("/api/users", json=user_data.model_dump())
        return self._validate(UserCreateResponse, response.json())

    def delete_user(self, user_id: int) -> bool:
        response = self.delete(f"/api/users/{user_id}")
        return response.status_code == 204

    @staticmethod
    def _validate(model: Type[ModelT], data: Any) -> ModelT:
        """Map raw response data onto a Pydantic model, translating schema mismatches
        into a framework-specific error instead of letting a raw pydantic one leak out."""
        try:
            return model.model_validate(data)
        except PydanticValidationError as exc:
            raise SchemaValidationError(
                f"Response failed schema validation for {model.__name__}: {exc}"
            ) from exc
