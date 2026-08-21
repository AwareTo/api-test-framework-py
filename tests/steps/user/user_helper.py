"""Allure step wrappers for asserting on User API results, for the functional tests in
`tests/api/test_users.py`. The contract tests in `tests/contract/test_user_contract.py` use the
generic body-shape assertions in `tests/steps/contract_helper.py` instead.
"""

import allure

from src.models.user import UserCreate, UserCreateResponse, UserResponse


@allure.step("Assert response model and fields are populated")
def assert_user_populated(user: UserResponse, expected_id: int) -> None:
    assert isinstance(user, UserResponse)
    assert user.id == expected_id
    assert user.email
    assert user.first_name
    assert user.last_name
    assert user.avatar


@allure.step("Assert response contains matching name, job, and an ID")
def assert_create_user_matches(result: UserCreateResponse, payload: UserCreate) -> None:
    assert isinstance(result, UserCreateResponse)
    assert result.name == payload.name
    assert result.job == payload.job
    assert result.id


@allure.step("Assert deletion returned True")
def assert_deleted(result: bool) -> None:
    assert result is True
