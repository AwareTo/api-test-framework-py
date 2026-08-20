"""Unit tests for AuthClient using respx to mock HTTP calls.

These tests double as proof that BaseClient's shared retry/error-handling/schema-validation
logic works identically for a second, unrelated domain (auth) and not just for UserClient —
in particular, test_login_raises_unauthorized_error_on_401 exercises the exact same
_STATUS_TO_EXCEPTION mapping that UserClient relies on, with zero auth-specific code added
to BaseClient.
"""

import json
from collections.abc import Iterator

import allure
import httpx
import pytest
import respx

from src.clients.auth_client import AuthClient
from src.config import settings
from src.exceptions import APIError, SchemaValidationError, UnauthorizedError
from src.models.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse

BASE_URL = str(settings.base_url).rstrip("/")


@pytest.fixture
def auth_client() -> Iterator[AuthClient]:
    client = AuthClient()
    yield client
    client.close()


@allure.epic("Auth API")
@allure.feature("Register")
@allure.story("Unit - response deserialization")
@allure.title("register() sends correct JSON body and maps response onto RegisterResponse")
@allure.severity(allure.severity_level.CRITICAL)
@respx.mock
def test_register_sends_payload_and_returns_mapped_model(auth_client: AuthClient) -> None:
    route = respx.post(f"{BASE_URL}/api/register").mock(
        return_value=httpx.Response(200, json={"id": 4, "token": "QpwL5tke4Pnpja7X4"})
    )

    result = auth_client.register(RegisterRequest(email="eve.holt@reqres.in", password="pistol"))

    assert json.loads(route.calls.last.request.content) == {
        "email": "eve.holt@reqres.in",
        "password": "pistol",
    }
    assert isinstance(result, RegisterResponse)
    assert result.id == 4
    assert result.token == "QpwL5tke4Pnpja7X4"


@allure.epic("Auth API")
@allure.feature("Register")
@allure.story("Unit - error handling")
@allure.title("register() raises APIError on 400 (missing password)")
@allure.severity(allure.severity_level.NORMAL)
@respx.mock
def test_register_raises_api_error_on_400(auth_client: AuthClient) -> None:
    respx.post(f"{BASE_URL}/api/register").mock(
        return_value=httpx.Response(400, json={"error": "Missing password"})
    )

    with pytest.raises(APIError) as exc_info:
        auth_client.register(RegisterRequest(email="sydney@fife", password=""))

    assert exc_info.value.status_code == 400


@allure.epic("Auth API")
@allure.feature("Register")
@allure.story("Unit - schema validation")
@allure.title("register() raises SchemaValidationError when the response doesn't match RegisterResponse")
@allure.severity(allure.severity_level.NORMAL)
@respx.mock
def test_register_raises_schema_validation_error_on_malformed_response(auth_client: AuthClient) -> None:
    respx.post(f"{BASE_URL}/api/register").mock(return_value=httpx.Response(200, json={"id": "not-an-int"}))

    with pytest.raises(SchemaValidationError):
        auth_client.register(RegisterRequest(email="eve.holt@reqres.in", password="pistol"))


@allure.epic("Auth API")
@allure.feature("Login")
@allure.story("Unit - response deserialization")
@allure.title("login() sends correct JSON body and maps response onto LoginResponse")
@allure.severity(allure.severity_level.CRITICAL)
@respx.mock
def test_login_sends_payload_and_returns_mapped_model(auth_client: AuthClient) -> None:
    route = respx.post(f"{BASE_URL}/api/login").mock(
        return_value=httpx.Response(200, json={"token": "QpwL5tke4Pnpja7X4"})
    )

    result = auth_client.login(LoginRequest(email="eve.holt@reqres.in", password="cityslicka"))

    assert json.loads(route.calls.last.request.content) == {
        "email": "eve.holt@reqres.in",
        "password": "cityslicka",
    }
    assert isinstance(result, LoginResponse)
    assert result.token == "QpwL5tke4Pnpja7X4"


@allure.epic("Auth API")
@allure.feature("Login")
@allure.story("Unit - error handling")
@allure.title("login() raises UnauthorizedError on 401 (wrong password)")
@allure.severity(allure.severity_level.CRITICAL)
@respx.mock
def test_login_raises_unauthorized_error_on_401(auth_client: AuthClient) -> None:
    """Proves BaseClient's _STATUS_TO_EXCEPTION mapping is genuinely shared: no auth-specific
    exception handling was added anywhere, yet a 401 from a completely different endpoint
    still raises the same UnauthorizedError that UserClient relies on."""
    respx.post(f"{BASE_URL}/api/login").mock(
        return_value=httpx.Response(401, json={"error": "user not found"})
    )

    with pytest.raises(UnauthorizedError) as exc_info:
        auth_client.login(LoginRequest(email="eve.holt@reqres.in", password="wrong-password"))

    assert exc_info.value.status_code == 401


@allure.epic("Auth API")
@allure.feature("Login")
@allure.story("Unit - error handling")
@allure.title("login() raises APIError on 400 (missing password)")
@allure.severity(allure.severity_level.NORMAL)
@respx.mock
def test_login_raises_api_error_on_400(auth_client: AuthClient) -> None:
    respx.post(f"{BASE_URL}/api/login").mock(
        return_value=httpx.Response(400, json={"error": "Missing password"})
    )

    with pytest.raises(APIError) as exc_info:
        auth_client.login(LoginRequest(email="peter@klaven", password=""))

    assert exc_info.value.status_code == 400
