"""Integration tests exercising the real API (marked slow; requires network access)."""

from collections.abc import Iterator

import pytest

from src.clients.user_client import UserClient
from src.models.user import UserCreate, UserCreateResponse, UserResponse

pytestmark = pytest.mark.integration


@pytest.fixture
def user_client() -> Iterator[UserClient]:
    client = UserClient()
    yield client
    client.close()


def test_get_user_from_live_api(user_client: UserClient) -> None:
    user = user_client.get_user(2)

    assert isinstance(user, UserResponse)
    assert user.id == 2


def test_create_user_on_live_api(user_client: UserClient) -> None:
    result = user_client.create_user(UserCreate(name="morpheus", job="leader"))

    assert isinstance(result, UserCreateResponse)
    assert result.name == "morpheus"
    assert result.job == "leader"


def test_delete_user_on_live_api(user_client: UserClient) -> None:
    assert user_client.delete_user(2) is True
