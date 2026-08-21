"""Contract tests for the Auth API — verify request/response shape against the agreed contract,
independent of the functional/business assertions already covered by `tests/api/test_auth.py`.

These hit raw HTTP via `tests/steps/auth/auth_endpoint.py`'s `login_raw`/`login_missing_password`
rather than going through `AuthClient.login`, so a payload can deliberately omit a field that
`LoginRequest` would otherwise require us to provide.
"""

import pytest

from src.clients.auth_client import AuthClient
from tests.steps.auth.auth_endpoint import login_missing_password, login_raw
from tests.steps.auth.auth_helper import assert_rejected_with_400
from tests.steps.contract_helper import assert_contains_fields, assert_field_types


@pytest.mark.contract
class TestLoginContract:
    def test_login_response_matches_contract(self, auth_client: AuthClient) -> None:
        """POST /api/login response contains the contracted fields."""
        body = login_raw(auth_client).json()
        assert_contains_fields(body, {"token"})
        assert_field_types(body, {"token": str})
        assert body["token"]

    def test_login_rejects_missing_password(self, auth_client: AuthClient) -> None:
        """POST /api/login still rejects a payload missing 'password' entirely."""
        error = login_missing_password(auth_client)
        assert_rejected_with_400(error)
