"""Live API tests for UserClient against the ReqRes service."""

import pytest

from src.clients.user_client import UserClient
from src.models.user import UserCreate
from tests.steps.user.user_endpoint import create_user, delete_user, get_user, get_user_expecting_not_found
from tests.steps.user.user_helper import assert_create_user_matches, assert_deleted, assert_user_populated


@pytest.mark.integration
class TestGetUser:
    def test_get_user_success(self, user_client: UserClient) -> None:
        """GET /api/users/2 returns a valid UserResponse."""
        user = get_user(user_client, 2)
        assert_user_populated(user, expected_id=2)

    def test_get_user_not_found(self, user_client: UserClient) -> None:
        """GET /api/users/9999 raises NotFoundError."""
        get_user_expecting_not_found(user_client, 9999)


@pytest.mark.integration
class TestCreateUser:
    def test_create_user_success(self, user_client: UserClient, random_user_payload: UserCreate) -> None:
        """POST /api/users returns UserCreateResponse with matching fields."""
        result = create_user(user_client, random_user_payload.name, random_user_payload.job)
        assert_create_user_matches(result, random_user_payload)


@pytest.mark.integration
class TestDeleteUser:
    def test_delete_user_success(self, user_client: UserClient) -> None:
        """DELETE /api/users/2 returns True."""
        result = delete_user(user_client, 2)
        assert_deleted(result)
