"""Live API tests for UserClient against the ReqRes service."""
import pytest

from src.clients.user_client import UserClient
from src.exceptions import NotFoundError
from src.models.user import UserCreate, UserCreateResponse, UserResponse


def test_get_user_success(user_client: UserClient) -> None:
    user = user_client.get_user(2)

    assert isinstance(user, UserResponse)
    assert user.id == 2
    assert user.email
    assert user.first_name
    assert user.last_name
    assert user.avatar


def test_get_user_not_found(user_client: UserClient) -> None:
    with pytest.raises(NotFoundError):
        user_client.get_user(9999)


def test_create_user_success(user_client: UserClient, random_user_payload: UserCreate) -> None:
    result = user_client.create_user(random_user_payload)

    assert isinstance(result, UserCreateResponse)
    assert result.name == random_user_payload.name
    assert result.job == random_user_payload.job
    assert result.id


def test_delete_user_success(user_client: UserClient) -> None:
    assert user_client.delete_user(2) is True
