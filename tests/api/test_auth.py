"""Live API tests for AuthClient against the ReqRes service."""

import allure
import pytest

from src.clients.auth_client import AuthClient
from src.exceptions import APIError
from src.models.auth import LoginRequest, RegisterRequest


@allure.epic("Auth API")
@allure.feature("Register")
@pytest.mark.integration
class TestRegister:
    @allure.story("Successful registration")
    @allure.title("POST /api/register returns a token for a valid known user")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_register_success(self, auth_client: AuthClient) -> None:
        with allure.step("Register with ReqRes's fixed test user"):
            result = auth_client.register(RegisterRequest(email="eve.holt@reqres.in", password="pistol"))

        with allure.step("Assert response contains an id and a token"):
            assert result.id
            assert result.token

    @allure.story("Missing password")
    @allure.title("POST /api/register without a password raises APIError")
    @allure.severity(allure.severity_level.NORMAL)
    def test_register_missing_password_raises_api_error(self, auth_client: AuthClient) -> None:
        with allure.step("Register with a password-less payload"):
            with pytest.raises(APIError) as exc_info:
                auth_client.register(RegisterRequest(email="sydney@fife", password=""))

        with allure.step("Assert the API rejected the request with a 400"):
            assert exc_info.value.status_code == 400


@allure.epic("Auth API")
@allure.feature("Login")
@pytest.mark.integration
class TestLogin:
    @allure.story("Successful login")
    @allure.title("POST /api/login returns a token for a valid known user")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_success(self, auth_client: AuthClient) -> None:
        with allure.step("Log in with ReqRes's fixed test user"):
            result = auth_client.login(LoginRequest(email="eve.holt@reqres.in", password="cityslicka"))

        with allure.step("Assert response contains a token"):
            assert result.token

    @allure.story("Missing password")
    @allure.title("POST /api/login without a password raises APIError")
    @allure.severity(allure.severity_level.NORMAL)
    def test_login_missing_password_raises_api_error(self, auth_client: AuthClient) -> None:
        with allure.step("Log in with a password-less payload"):
            with pytest.raises(APIError) as exc_info:
                auth_client.login(LoginRequest(email="peter@klaven", password=""))

        with allure.step("Assert the API rejected the request with a 400"):
            assert exc_info.value.status_code == 400
