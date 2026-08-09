"""Framework-level exceptions for the API test automation framework."""


class FrameworkError(Exception):
    """Base exception for all framework-raised errors."""


class ApiError(FrameworkError):
    """Raised when an API call returns an unexpected status code."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class SchemaValidationError(FrameworkError):
    """Raised when an API response fails to validate against its Pydantic model."""


class APIError(Exception):
    """Raised by BaseClient when an API call returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class NotFoundError(APIError):
    """Raised when an API call returns a 404 Not Found response."""


class ValidationError(APIError):
    """Raised when an API call returns a 422 Unprocessable Entity response."""


class UnauthorizedError(APIError):
    """Raised when an API call returns a 401 Unauthorized response."""
