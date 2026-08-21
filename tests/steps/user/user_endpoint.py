"""Allure step wrappers for calling the User API.

Includes both business-level actions that go through the typed `UserClient` (used by the
functional tests in `tests/api/test_users.py`) and raw/wire-level actions that call `.get`/`.post`
directly (used by the contract tests in `tests/contract/test_user_contract.py`, which need to
send payloads outside what `UserCreate` would allow).
"""

import allure
import pytest
from httpx import Response

from src.clients.user_client import UserClient
from src.exceptions import NotFoundError
from src.models.user import UserCreate, UserCreateResponse, UserResponse


@allure.step("Fetch user with ID {user_id}")
def get_user(user_client: UserClient, user_id: int) -> UserResponse:
    return user_client.get_user(user_id)


@allure.step("Fetch non-existent user ID {user_id}, expecting NotFoundError")
def get_user_expecting_not_found(user_client: UserClient, user_id: int) -> None:
    with pytest.raises(NotFoundError):
        user_client.get_user(user_id)


@allure.step("Create user: {name}, {job}")
def create_user(user_client: UserClient, name: str, job: str) -> UserCreateResponse:
    # Takes the scalar fields rather than the whole `UserCreate`, so allure.step's
    # `{param}` title placeholders can reference them directly — allure pre-stringifies
    # each parameter before formatting the title, so a dotted `{payload.name}` would
    # try attribute access on that string instead of the original object.
    return user_client.create_user(UserCreate(name=name, job=job))


@allure.step("Delete user with ID {user_id}")
def delete_user(user_client: UserClient, user_id: int) -> bool:
    return user_client.delete_user(user_id)


@allure.step("Fetch user with ID {user_id}")
def get_user_raw(user_client: UserClient, user_id: int) -> Response:
    return user_client.get(f"/api/users/{user_id}")


@allure.step("Send the user payload {payload}")
def create_user_raw(user_client: UserClient, payload: dict[str, object]) -> Response:
    return user_client.post("/api/users", json=payload)
