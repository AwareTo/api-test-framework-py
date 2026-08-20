"""Base HTTP client wrapping httpx with shared request/response handling."""
from __future__ import annotations

import json
import time
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

# Retries are only safe for HTTP-idempotent verbs — repeating a GET/PUT/DELETE has the
# same effect as doing it once. POST is deliberately excluded: retrying a create after a
# transient server error risks creating a second resource, since we can't tell whether the
# original request was actually processed before the error came back.
_RETRYABLE_METHODS = {"GET", "PUT", "DELETE"}
# Only retry on errors that are plausibly transient infra hiccups, not on responses that
# reflect a real decision by the server (e.g. 404/422/401 are never retried).
_RETRYABLE_STATUS_CODES = {502, 503, 504}
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 0.2


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
        so a failing live-API test carries its own diagnostic context in the report.

        Idempotent verbs (GET/PUT/DELETE) are automatically retried on transient
        502/503/504 responses and on transport-level failures (connection/read
        timeouts, connection errors); every attempt is attached, so a retry that
        eventually succeeds still shows up in the report rather than reporting a
        silent clean pass."""
        with allure.step(f"{method} {path}"):
            send = getattr(self._client, method.lower())
            retryable = method.upper() in _RETRYABLE_METHODS

            attempt = 1
            while True:
                started_at = datetime.now(timezone.utc)
                try:
                    response = send(path, **kwargs)
                except httpx.TransportError as exc:
                    if attempt == 1:
                        self._attach_transport_error(exc, method, path, started_at)
                    else:
                        with allure.step(f"Retry attempt {attempt} of {_MAX_ATTEMPTS}"):
                            self._attach_transport_error(exc, method, path, started_at)

                    if not (retryable and attempt < _MAX_ATTEMPTS):
                        raise

                    time.sleep(_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                    attempt += 1
                    continue

                if attempt == 1:
                    self._attach_http_details(response, started_at)
                else:
                    with allure.step(f"Retry attempt {attempt} of {_MAX_ATTEMPTS}"):
                        self._attach_http_details(response, started_at)

                should_retry = (
                    retryable
                    and response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < _MAX_ATTEMPTS
                )
                if not should_retry:
                    return self._check_response(response)

                time.sleep(_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                attempt += 1

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

    def _attach_transport_error(
        self, exc: httpx.TransportError, method: str, path: str, started_at: datetime
    ) -> None:
        """Attach diagnostic context for a connection-level failure (timeout, reset, etc.)
        where no response was ever received, so the report still shows what was attempted."""
        try:
            request: Optional[httpx.Request] = exc.request
        except RuntimeError:
            # httpx raises rather than returning None when `.request` was never attached
            # (e.g. the connection failed before a Request object could be built).
            request = None
        if request is not None:
            allure.attach(
                json.dumps(self._describe_request(request), indent=2, default=str),
                name="Request",
                attachment_type=allure.attachment_type.JSON,
            )
        allure.attach(
            json.dumps(
                {
                    "timestamp": started_at.isoformat(timespec="milliseconds"),
                    "method": method,
                    "path": path,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
                indent=2,
            ),
            name="Transport Error",
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
