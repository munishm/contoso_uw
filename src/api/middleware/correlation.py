"""
Correlation ID middleware for request tracing.

Injects a correlation ID into each request for distributed tracing.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that injects correlation ID into requests."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with correlation ID."""
        # Get existing correlation ID from header or generate new one
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set in context variable
        token = correlation_id_var.set(correlation_id)

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id

            return response
        finally:
            # Reset context variable
            correlation_id_var.reset(token)
