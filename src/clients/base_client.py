"""Base HTTP client wrapping httpx with shared request/response handling."""
from __future__ import annotations

from types import TracebackType
from typing import Any, Optional, Type

import httpx

from src.exceptions import APIError, NotFoundError, UnauthorizedError, ValidationError

_STATUS_TO_EXCEPTION: dict[int, Type[APIError]] = {
    401: UnauthorizedError,
    404: NotFoundError,
    422: ValidationError,
}


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
        response = self._client.get(path, **kwargs)
        return self._check_response(response)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.post(path, **kwargs)
        return self._check_response(response)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.put(path, **kwargs)
        return self._check_response(response)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.delete(path, **kwargs)
        return self._check_response(response)

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
