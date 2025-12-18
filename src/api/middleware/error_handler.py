"""
Global exception handler for consistent error responses.

Converts exceptions to standard ErrorResponse format.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.api.middleware.correlation import get_correlation_id
from src.api.models.common import ErrorResponse, ValidationErrorDetail, ValidationErrorResponse

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "internal_error",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details
        super().__init__(message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not_found",
            details=details,
        )


class ConflictError(APIError):
    """Conflict error (e.g., duplicate resource, ETag mismatch)."""

    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_type="conflict",
            details=details,
        )


class BadRequestError(APIError):
    """Bad request error."""

    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="bad_request",
            details=details,
        )


class UnauthorizedError(APIError):
    """Unauthorized error."""

    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="unauthorized",
            details=details,
        )


class ForbiddenError(APIError):
    """Forbidden error."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="forbidden",
            details=details,
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error."""

    def __init__(
        self, message: str = "Service temporarily unavailable", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="service_unavailable",
            details=details,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle custom API errors."""
        correlation_id = get_correlation_id()
        logger.error(
            f"API error: {exc.error_type} - {exc.message}",
            extra={"correlation_id": correlation_id, "status_code": exc.status_code},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.error_type,
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI validation errors."""
        correlation_id = get_correlation_id()
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"correlation_id": correlation_id},
        )

        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append(
                ValidationErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=error["type"],
                )
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ValidationErrorResponse(
                message="Validation failed",
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        correlation_id = get_correlation_id()
        logger.warning(
            f"Pydantic validation error: {exc.errors()}",
            extra={"correlation_id": correlation_id},
        )

        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append(
                ValidationErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=error["type"],
                )
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ValidationErrorResponse(
                message="Validation failed",
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        correlation_id = get_correlation_id()
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={"correlation_id": correlation_id},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="internal_error",
                message="An unexpected error occurred",
                details=None,
            ).model_dump(),
        )
