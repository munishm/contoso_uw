"""Middleware components for authentication, logging, and error handling."""

from src.api.middleware.auth import (
    JWKSClient,
    UserClaims,
    get_current_user,
    validate_token,
)
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
    # Auth
    "JWKSClient",
    "UserClaims",
    "get_current_user",
    "validate_token",
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
