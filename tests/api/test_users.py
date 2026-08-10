"""Live API tests for UserClient against the ReqRes service."""
import allure
import pytest

from src.clients.user_client import UserClient
from src.exceptions import NotFoundError
from src.models.user import UserCreate, UserCreateResponse, UserResponse


@allure.epic("User API")
@allure.feature("Get User")
class TestGetUser:

    @allure.story("Successful retrieval")
    @allure.title("GET /api/users/2 returns a valid UserResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_success(self, user_client: UserClient) -> None:
        with allure.step("Fetch user with ID 2"):
            user = user_client.get_user(2)

        with allure.step("Assert response model and fields are populated"):
            assert isinstance(user, UserResponse)
            assert user.id == 2
            assert user.email
            assert user.first_name
            assert user.last_name
            assert user.avatar

    @allure.story("Not found")
    @allure.title("GET /api/users/9999 raises NotFoundError")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_user_not_found(self, user_client: UserClient) -> None:
        with allure.step("Fetch non-existent user ID 9999"):
            with pytest.raises(NotFoundError):
                user_client.get_user(9999)


@allure.epic("User API")
@allure.feature("Create User")
class TestCreateUser:

    @allure.story("Successful creation")
    @allure.title("POST /api/users returns UserCreateResponse with matching fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_success(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        with allure.step(f"Create user: {random_user_payload.name}, {random_user_payload.job}"):
            result = user_client.create_user(random_user_payload)

        with allure.step("Assert response contains matching name, job, and an ID"):
            assert isinstance(result, UserCreateResponse)
            assert result.name == random_user_payload.name
            assert result.job == random_user_payload.job
            assert result.id


@allure.epic("User API")
@allure.feature("Delete User")
class TestDeleteUser:

    @allure.story("Successful deletion")
    @allure.title("DELETE /api/users/2 returns True")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_user_success(self, user_client: UserClient) -> None:
        with allure.step("Delete user with ID 2"):
            result = user_client.delete_user(2)

        with allure.step("Assert deletion returned True"):
            assert result is True
