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
    route = respx.get(f"{BASE_URL}/missing").mock(return_value=httpx.Response(404, text="not found"))

    with pytest.raises(NotFoundError) as exc_info:
        base_client.get("/missing")

    assert exc_info.value.status_code == 404
    assert route.call_count == 1  # 404 is a real decision by the server, never retried


@respx.mock
def test_get_retries_on_503_then_succeeds(base_client: BaseClient) -> None:
    route = respx.get(f"{BASE_URL}/flaky").mock(
        side_effect=[
            httpx.Response(503, text="unavailable"),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )

    response = base_client.get("/flaky")

    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_get_raises_api_error_after_exhausting_retries_on_503(base_client: BaseClient) -> None:
    route = respx.get(f"{BASE_URL}/always-503").mock(return_value=httpx.Response(503, text="unavailable"))

    with pytest.raises(APIError) as exc_info:
        base_client.get("/always-503")

    assert exc_info.value.status_code == 503
    assert route.call_count == 3  # exhausted all attempts, no more retries after the last one


@respx.mock
def test_get_retries_on_transport_error_then_succeeds(base_client: BaseClient) -> None:
    route = respx.get(f"{BASE_URL}/flaky-connection").mock(
        side_effect=[
            httpx.ConnectTimeout("connection timed out"),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )

    response = base_client.get("/flaky-connection")

    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_get_raises_transport_error_after_exhausting_retries(base_client: BaseClient) -> None:
    route = respx.get(f"{BASE_URL}/always-down").mock(side_effect=httpx.ConnectError("connection refused"))

    with pytest.raises(httpx.ConnectError):
        base_client.get("/always-down")

    assert route.call_count == 3  # exhausted all attempts, original exception re-raised as-is


@respx.mock
def test_post_does_not_retry_on_transport_error() -> None:
    """POST is never retried on a transport error either — a dropped connection gives even
    less certainty than a 503 about whether the server processed the create."""
    client = BaseClient(base_url=BASE_URL, timeout=5)
    route = respx.post(f"{BASE_URL}/items").mock(side_effect=httpx.ConnectError("connection refused"))

    with pytest.raises(httpx.ConnectError):
        client.post("/items", json={"name": "widget"})

    assert route.call_count == 1
    client.close()


@respx.mock
def test_post_does_not_retry_on_503() -> None:
    """POST is never retried, even on a transient-looking 503 — retrying a create risks
    creating a duplicate resource since we can't tell if the original was processed."""
    client = BaseClient(base_url=BASE_URL, timeout=5)
    route = respx.post(f"{BASE_URL}/items").mock(return_value=httpx.Response(503, text="unavailable"))

    with pytest.raises(APIError):
        client.post("/items", json={"name": "widget"})

    assert route.call_count == 1
    client.close()


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
