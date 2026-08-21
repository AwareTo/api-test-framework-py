"""Contract tests for the User API — verify request/response shape against the agreed contract,
independent of the functional/business assertions already covered by `tests/api/test_users.py`.

Response-side tests check that the fields the client depends on (`UserResponse`,
`UserCreateResponse`) are still present with the expected types. Payload-side tests check that the
provider's expectations of *our* requests haven't changed — that it still accepts our current
required fields, and still tolerates an extra one.

These hit raw HTTP via `tests/steps/user/user_endpoint.py`'s `get_user_raw`/`create_user_raw`
rather than going through `UserClient.create_user`/`get_user`, so a payload can deliberately
include fields outside what `UserCreate` allows.
"""

import pytest

from src.clients.user_client import UserClient
from src.models.user import UserCreate
from tests.steps.contract_helper import assert_contains_fields, assert_field_types
from tests.steps.user.user_endpoint import create_user_raw, get_user_raw


@pytest.mark.contract
class TestGetUserResponseContract:
    def test_get_user_response_matches_contract(self, user_client: UserClient) -> None:
        """GET /api/users/2 response contains the contracted fields."""
        data = get_user_raw(user_client, 2).json()["data"]
        assert_contains_fields(data, {"id", "email", "first_name", "last_name", "avatar"})
        assert_field_types(
            data, {"id": int, "email": str, "first_name": str, "last_name": str, "avatar": str}
        )


@pytest.mark.contract
class TestCreateUserContract:
    def test_create_user_response_matches_contract(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        """POST /api/users response contains the contracted fields."""
        body = create_user_raw(user_client, random_user_payload.model_dump()).json()
        assert_contains_fields(body, {"id", "name", "job", "createdAt"})
        assert_field_types(body, {"id": str, "name": str, "job": str, "createdAt": str})

    def test_create_user_accepts_current_required_fields(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        """POST /api/users still accepts exactly our current required fields."""
        response = create_user_raw(user_client, random_user_payload.model_dump())
        assert response.status_code == 201

    def test_create_user_tolerates_unexpected_extra_field(
        self, user_client: UserClient, random_user_payload: UserCreate
    ) -> None:
        """POST /api/users still tolerates an unrecognized extra field."""
        payload = {**random_user_payload.model_dump(), "unexpected_field": "contract-poc"}
        response = create_user_raw(user_client, payload)
        assert response.status_code == 201
