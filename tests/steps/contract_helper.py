"""Shared Allure step helpers for the contract tests — verifying a response body's shape against
the agreed contract, independent of the functional/business assertions in `tests/steps/*_helper.py`.
"""

import allure


@allure.step("Assert the response contains at least the contracted fields: {fields}")
def assert_contains_fields(body: dict[str, object], fields: set[str]) -> None:
    # Subset, not equality: the response models this protects (UserResponse,
    # UserCreateResponse, LoginResponse, ...) all use `extra="ignore"` deliberately —
    # ReqRes is free to add fields (observed live: `support`, `_meta`) without that
    # counting as a broken contract.
    assert fields <= set(body)


@allure.step("Assert each field's type matches the contract")
def assert_field_types(body: dict[str, object], expected_types: dict[str, type]) -> None:
    for field, expected_type in expected_types.items():
        assert isinstance(body[field], expected_type)
