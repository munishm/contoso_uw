"""Middleware components for logging and error handling."""

from src.api.middleware.correlation import CorrelationMiddleware, get_correlation_id
from src.api.middleware.error_handler import (
    APIError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    setup_exception_handlers,
)
from src.api.middleware.logging import LoggingMiddleware

__all__ = [
    # Correlation
    "CorrelationMiddleware",
    "get_correlation_id",
    # Error handling
    "APIError",
    "BadRequestError",
    "ConflictError",
    "NotFoundError",
    "UnauthorizedError",
    "setup_exception_handlers",
    # Logging
    "LoggingMiddleware",
]
