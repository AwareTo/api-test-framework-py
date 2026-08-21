"""Allure step wrappers for calling the Auth API.

Includes both business-level actions that go through the typed `AuthClient` (used by the
functional tests in `tests/api/test_auth.py`) and raw/wire-level actions that call `.post`
directly (used by the contract tests in `tests/contract/test_auth_contract.py`, which need to
send payloads outside what `LoginRequest`/`RegisterRequest` would allow).
"""

import allure
import pytest
from httpx import Response

from src.clients.auth_client import AuthClient
from src.exceptions import APIError
from src.models.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse


@allure.step("Register with ReqRes's fixed test user")
def register(auth_client: AuthClient, payload: RegisterRequest) -> RegisterResponse:
    return auth_client.register(payload)


@allure.step("Register with a payload the API is expected to reject")
def register_expecting_rejection(auth_client: AuthClient, payload: RegisterRequest) -> APIError:
    with pytest.raises(APIError) as exc_info:
        auth_client.register(payload)
    return exc_info.value


@allure.step("Log in with ReqRes's fixed test user")
def login(auth_client: AuthClient, payload: LoginRequest) -> LoginResponse:
    return auth_client.login(payload)


@allure.step("Log in with a payload the API is expected to reject")
def login_expecting_rejection(auth_client: AuthClient, payload: LoginRequest) -> APIError:
    with pytest.raises(APIError) as exc_info:
        auth_client.login(payload)
    return exc_info.value


@allure.step("Log in with ReqRes's fixed test user")
def login_raw(auth_client: AuthClient) -> Response:
    return auth_client.post("/api/login", json={"email": "eve.holt@reqres.in", "password": "cityslicka"})


@allure.step("Log in with a payload that omits the 'password' key entirely")
def login_missing_password(auth_client: AuthClient) -> APIError:
    with pytest.raises(APIError) as exc_info:
        auth_client.post("/api/login", json={"email": "peter@klaven"})
    return exc_info.value
