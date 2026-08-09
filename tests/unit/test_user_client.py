"""Unit tests for UserClient using respx to mock HTTP calls."""
import json

import httpx
import pytest
import respx

from src.clients.user_client import UserClient
from src.config import settings
from src.exceptions import NotFoundError
from src.models.user import UserCreate, UserCreateResponse, UserResponse

BASE_URL = str(settings.base_url).rstrip("/")


@pytest.fixture
def user_client() -> UserClient:
    client = UserClient()
    yield client
    client.close()


@respx.mock
def test_get_user_returns_mapped_model(user_client: UserClient) -> None:
    respx.get(f"{BASE_URL}/api/users/2").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": 2,
                    "email": "janet.weaver@reqres.in",
                    "first_name": "Janet",
                    "last_name": "Weaver",
                    "avatar": "https://reqres.in/img/faces/2-image.jpg",
                },
                "support": {"url": "https://reqres.in/#support-heading", "text": "..."},
            },
        )
    )

    user = user_client.get_user(2)

    assert isinstance(user, UserResponse)
    assert user.id == 2
    assert user.email == "janet.weaver@reqres.in"
    assert user.first_name == "Janet"
    assert user.last_name == "Weaver"
    assert user.avatar == "https://reqres.in/img/faces/2-image.jpg"


@respx.mock
def test_get_user_raises_not_found_error_on_failure(user_client: UserClient) -> None:
    respx.get(f"{BASE_URL}/api/users/999").mock(return_value=httpx.Response(404, text="not found"))

    with pytest.raises(NotFoundError) as exc_info:
        user_client.get_user(999)

    assert exc_info.value.status_code == 404


@respx.mock
def test_create_user_sends_payload_and_returns_mapped_model(user_client: UserClient) -> None:
    route = respx.post(f"{BASE_URL}/api/users").mock(
        return_value=httpx.Response(
            201,
            json={"name": "morpheus", "job": "leader", "id": "123", "createdAt": "2026-08-09T12:00:00.000Z"},
        )
    )

    result = user_client.create_user(UserCreate(name="morpheus", job="leader"))

    assert json.loads(route.calls.last.request.content) == {"name": "morpheus", "job": "leader"}
    assert isinstance(result, UserCreateResponse)
    assert result.id == "123"
    assert result.name == "morpheus"
    assert result.job == "leader"
    assert result.createdAt == "2026-08-09T12:00:00.000Z"


@respx.mock
def test_delete_user_returns_true_on_204(user_client: UserClient) -> None:
    respx.delete(f"{BASE_URL}/api/users/2").mock(return_value=httpx.Response(204))

    assert user_client.delete_user(2) is True
