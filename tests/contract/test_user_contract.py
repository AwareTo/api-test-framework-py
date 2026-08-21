"""Contract tests for the User API — verify request/response shape against the
agreed contract, independent of the functional/business assertions already covered
by `tests/api/test_users.py`.

Response-side tests check that the fields the client depends on (`UserResponse`,
`UserCreateResponse`) are still present with the expected types. Payload-side tests
check that the provider's expectations of *our* requests haven't changed — that it
still accepts our current required fields, and still tolerates an extra one.

These hit `user_client.post`/`.get` directly rather than going through
`UserClient.create_user`/`get_user`, so a payload can deliberately include fields
outside what `UserCreate` allows.
"""

import allure
import pytest

from src.clients.user_client import UserClient
from src.models.user import UserCreate


@allure.epic("Contract")
@allure.feature("Get User")
@pytest.mark.integration
@pytest.mark.contract
class TestGetUserResponseContract:
    @allure.story("Response shape")
    @allure.title("GET /api/users/2 response contains the contracted fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_response_matches_contract(self, user_client: UserClient) -> None:
        with allure.step("Fetch user with ID 2"):
            response = user_client.get("/api/users/2")

        with allure.step("Assert the 'data' object contains at least the contracted fields"):
            # Subset, not equality: UserResponse uses `extra="ignore"` deliberately —
            # ReqRes is free to add fields (it already does, at the top level: `support`,
            # `_meta`) without that counting as a broken contract.
            data = response.json()["data"]
            assert {"id", "email", "first_name", "last_name", "avatar"} <= set(data)

        with allure.step("Assert each field's type matches the contract"):
            assert isinstance(data["id"], int)
            assert isinstance(data["email"], str)
            assert isinstance(data["first_name"], str)
            assert isinstance(data["last_name"], str)
            assert isinstance(data["avatar"], str)


@allure.epic("Contract")
@allure.feature("Create User")
@pytest.mark.integration
@pytest.mark.contract
class TestCreateUserContract:
    @allure.story("Response shape")
    @allure.title("POST /api/users response contains the contracted fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_response_matches_contract(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        with allure.step("Create a user with the current required payload"):
            response = user_client.post("/api/users", json=random_user_payload.model_dump())

        with allure.step("Assert the response contains at least the contracted fields"):
            # Subset, not equality — see comment in TestGetUserResponseContract above.
            # ReqRes adds `_meta` here too, observed live.
            body = response.json()
            assert {"id", "name", "job", "createdAt"} <= set(body)

        with allure.step("Assert each field's type matches the contract"):
            assert isinstance(body["id"], str)
            assert isinstance(body["name"], str)
            assert isinstance(body["job"], str)
            assert isinstance(body["createdAt"], str)

    @allure.story("Payload acceptance")
    @allure.title("POST /api/users still accepts exactly our current required fields")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_accepts_current_required_fields(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        with allure.step("Send only the fields our current UserCreate model sends"):
            response = user_client.post("/api/users", json=random_user_payload.model_dump())

        with allure.step("Assert the provider still accepts this payload as-is"):
            assert response.status_code == 201

    @allure.story("Payload tolerance")
    @allure.title("POST /api/users still tolerates an unrecognized extra field")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_user_tolerates_unexpected_extra_field(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        with allure.step("Send the current payload plus a field the provider doesn't know about"):
            payload = {**random_user_payload.model_dump(), "unexpected_field": "contract-poc"}
            response = user_client.post("/api/users", json=payload)

        with allure.step("Assert the extra field didn't cause a rejection"):
            assert response.status_code == 201
