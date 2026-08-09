"""Unit tests for BaseClient using respx to mock HTTP responses."""
import httpx
import pytest
import respx

from src.clients.base_client import BaseClient
from src.exceptions import APIError, NotFoundError

BASE_URL = "https://example.test"


@pytest.fixture
def base_client() -> BaseClient:
    client = BaseClient(base_url=BASE_URL, timeout=5)
    yield client
    client.close()


@respx.mock
def test_get_returns_response_on_200(base_client: BaseClient) -> None:
    respx.get(f"{BASE_URL}/ping").mock(return_value=httpx.Response(200, json={"status": "ok"}))

    response = base_client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@respx.mock
def test_get_raises_not_found_error_on_404(base_client: BaseClient) -> None:
    respx.get(f"{BASE_URL}/missing").mock(return_value=httpx.Response(404, text="not found"))

    with pytest.raises(NotFoundError) as exc_info:
        base_client.get("/missing")

    assert exc_info.value.status_code == 404


@respx.mock
def test_get_raises_api_error_on_500(base_client: BaseClient) -> None:
    respx.get(f"{BASE_URL}/broken").mock(return_value=httpx.Response(500, text="server error"))

    with pytest.raises(APIError) as exc_info:
        base_client.get("/broken")

    assert exc_info.value.status_code == 500


@respx.mock
def test_post_sends_json_body_and_default_headers(base_client: BaseClient) -> None:
    route = respx.post(f"{BASE_URL}/items").mock(return_value=httpx.Response(201, json={"id": 1}))

    response = base_client.post("/items", json={"name": "widget"})

    assert response.status_code == 201
    sent_request = route.calls.last.request
    assert sent_request.headers["Content-Type"] == "application/json"


def test_context_manager_closes_client() -> None:
    with BaseClient(base_url=BASE_URL) as client:
        assert not client._client.is_closed

    assert client._client.is_closed
