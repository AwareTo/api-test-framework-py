"""Allure step wrappers for asserting on Auth API results.

`assert_rejected_with_400` is shared: both the functional tests in `tests/api/test_auth.py` and
the contract test in `tests/contract/test_auth_contract.py` check the same thing — that a rejected
request comes back as a 400 — just for different reasons (bad business input vs. a missing
required field).
"""

import allure

from src.exceptions import APIError
from src.models.auth import LoginResponse, RegisterResponse


@allure.step("Assert response contains an id and a token")
def assert_has_id_and_token(result: RegisterResponse) -> None:
    assert result.id
    assert result.token


@allure.step("Assert response contains a token")
def assert_has_token(result: LoginResponse) -> None:
    assert result.token


@allure.step("Assert the API rejected the request with a 400")
def assert_rejected_with_400(error: APIError) -> None:
    assert error.status_code == 400
