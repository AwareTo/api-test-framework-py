"""Base HTTP client wrapping httpx with shared request/response handling."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Optional, Type

import allure
import httpx

from src.exceptions import APIError, NotFoundError, UnauthorizedError, ValidationError

_STATUS_TO_EXCEPTION: dict[int, Type[APIError]] = {
    401: UnauthorizedError,
    404: NotFoundError,
    422: ValidationError,
}

# Header names whose values must never be attached verbatim to an Allure report —
# reports are published straight to public GitHub Pages, so secrets can't ride along.
_SENSITIVE_HEADERS = {"x-api-key", "authorization"}
_REDACTED = "***REDACTED***"


class BaseClient:
    """Thin wrapper around httpx.Client providing shared headers, error handling,
    and lifecycle management for concrete service clients to build on."""

    def __init__(self, base_url: str, timeout: int = 10, api_key: Optional[str] = None) -> None:
        self.base_url = base_url
        self.timeout = timeout
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._call("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._call("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._call("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._call("DELETE", path, **kwargs)

    def _call(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Issue the request as an Allure step, attaching request/response details
        (redacted headers, body, status, latency) before any failure is raised —
        so a failing live-API test carries its own diagnostic context in the report."""
        with allure.step(f"{method} {path}"):
            started_at = datetime.now(timezone.utc)
            send = getattr(self._client, method.lower())
            response = send(path, **kwargs)
            self._attach_http_details(response, started_at)
            return self._check_response(response)

    def _attach_http_details(self, response: httpx.Response, started_at: datetime) -> None:
        allure.attach(
            json.dumps(self._describe_request(response.request), indent=2, default=str),
            name="Request",
            attachment_type=allure.attachment_type.JSON,
        )
        allure.attach(
            json.dumps(self._describe_response(response, started_at), indent=2, default=str),
            name="Response",
            attachment_type=allure.attachment_type.JSON,
        )

    @staticmethod
    def _redact_headers(headers: httpx.Headers) -> dict[str, str]:
        return {
            key: (_REDACTED if key.lower() in _SENSITIVE_HEADERS else value)
            for key, value in headers.items()
        }

    @staticmethod
    def _describe_request(request: httpx.Request) -> dict[str, Any]:
        body: Any = None
        if request.content:
            try:
                body = json.loads(request.content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = request.content.decode("utf-8", errors="replace")
        return {
            "method": request.method,
            "url": str(request.url),
            "headers": BaseClient._redact_headers(request.headers),
            "body": body,
        }

    @staticmethod
    def _describe_response(response: httpx.Response, started_at: datetime) -> dict[str, Any]:
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        return {
            "timestamp": started_at.isoformat(timespec="milliseconds"),
            "status_code": response.status_code,
            "latency_ms": round(response.elapsed.total_seconds() * 1000, 1),
            "headers": BaseClient._redact_headers(response.headers),
            "body": body,
        }

    def _check_response(self, response: httpx.Response) -> httpx.Response:
        if response.is_success:
            return response

        exception_cls = _STATUS_TO_EXCEPTION.get(response.status_code, APIError)
        raise exception_cls(response.status_code, response.text)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
