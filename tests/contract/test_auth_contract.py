"""Contract tests for the Auth API — verify request/response shape against the
agreed contract, independent of the functional/business assertions already covered
by `tests/api/test_auth.py`.

These hit `auth_client.post` directly rather than going through
`AuthClient.login`/`register`, so a payload can deliberately omit a field that
`LoginRequest`/`RegisterRequest` would otherwise require us to provide.
"""

import allure
import pytest

from src.clients.auth_client import AuthClient
from src.exceptions import APIError


@allure.epic("Contract")
@allure.feature("Login")
@pytest.mark.integration
@pytest.mark.contract
class TestLoginContract:
    @allure.story("Response shape")
    @allure.title("POST /api/login response contains the contracted fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_response_matches_contract(self, auth_client: AuthClient) -> None:
        with allure.step("Log in with ReqRes's fixed test user"):
            response = auth_client.post(
                "/api/login", json={"email": "eve.holt@reqres.in", "password": "cityslicka"}
            )

        with allure.step("Assert the response contains at least the contracted fields"):
            # Subset, not equality: LoginResponse uses `extra="ignore"` deliberately —
            # ReqRes adds a `_meta` field here too, observed live.
            body = response.json()
            assert {"token"} <= set(body)

        with allure.step("Assert the token field's type matches the contract"):
            assert isinstance(body["token"], str)
            assert body["token"]

    @allure.story("Payload requirement")
    @allure.title("POST /api/login still rejects a payload missing 'password' entirely")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_rejects_missing_password(self, auth_client: AuthClient) -> None:
        with allure.step("Log in with a payload that omits the 'password' key entirely"):
            with pytest.raises(APIError) as exc_info:
                auth_client.post("/api/login", json={"email": "peter@klaven"})

        with allure.step("Assert the provider still enforces 'password' as required"):
            assert exc_info.value.status_code == 400
