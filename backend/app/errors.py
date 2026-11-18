from typing import Any


class AppError(Exception):
    """Base for errors we raise on purpose. Each subclass maps to one HTTP status + code."""

    status_code: int = 500
    code: str = "internal"
    message: str = "Something went wrong."

    def __init__(
        self,
        message: str | None = None,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details
        self.headers = headers
        super().__init__(self.message)


class InvalidCursor(AppError):
    status_code = 400
    code = "invalid_cursor"
    message = "Invalid cursor."


class Unauthenticated(AppError):
    status_code = 401
    code = "unauthenticated"
    message = "Missing or invalid access token."


class NotAllowed(AppError):
    status_code = 403
    code = "not_allowed"
    message = "You are not allowed to do this."


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    message = "Not found."


class Conflict(AppError):
    status_code = 409
    code = "conflict"
    message = "This conflicts with existing data."


class BalanceNotZero(AppError):
    status_code = 409
    code = "balance_not_zero"
    message = "Settle up first: your balance must be zero."


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_error"
    message = "Some fields are invalid."


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Too many requests. Try again later."

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(headers={"Retry-After": str(retry_after_seconds)})


def error_body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict:
    """The one error shape every endpoint returns (API_SPEC.md §1)."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}
