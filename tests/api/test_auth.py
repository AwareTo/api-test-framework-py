"""Live API tests for AuthClient against the ReqRes service."""

import pytest

from src.clients.auth_client import AuthClient
from src.models.auth import LoginRequest, RegisterRequest
from tests.steps.auth.auth_endpoint import (
    login,
    login_expecting_rejection,
    register,
    register_expecting_rejection,
)
from tests.steps.auth.auth_helper import assert_has_id_and_token, assert_has_token, assert_rejected_with_400


@pytest.mark.integration
class TestRegister:
    def test_register_success(self, auth_client: AuthClient) -> None:
        """POST /api/register returns a token for a valid known user."""
        result = register(auth_client, RegisterRequest(email="eve.holt@reqres.in", password="pistol"))
        assert_has_id_and_token(result)

    def test_register_missing_password_raises_api_error(self, auth_client: AuthClient) -> None:
        """POST /api/register without a password raises APIError."""
        error = register_expecting_rejection(auth_client, RegisterRequest(email="sydney@fife", password=""))
        assert_rejected_with_400(error)


@pytest.mark.integration
class TestLogin:
    def test_login_success(self, auth_client: AuthClient) -> None:
        """POST /api/login returns a token for a valid known user."""
        result = login(auth_client, LoginRequest(email="eve.holt@reqres.in", password="cityslicka"))
        assert_has_token(result)

    def test_login_missing_password_raises_api_error(self, auth_client: AuthClient) -> None:
        """POST /api/login without a password raises APIError."""
        error = login_expecting_rejection(auth_client, LoginRequest(email="peter@klaven", password=""))
        assert_rejected_with_400(error)
