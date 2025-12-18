"""
Request/response logging middleware.

Logs incoming requests and outgoing responses with correlation IDs.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)

# Fields that should be redacted in logs
SENSITIVE_FIELDS = {"password", "token", "api_key", "secret", "authorization"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Log request and response details."""
        correlation_id = get_correlation_id()
        start_time = time.perf_counter()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": self._redact_sensitive(dict(request.query_params)),
                "client_ip": self._get_client_ip(request),
            },
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"-> {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"-> Exception ({duration_ms:.2f}ms): {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                },
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check for forwarded header (from proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP (client IP)
            return forwarded.split(",")[0].strip()

        # Fall back to direct client
        if request.client:
            return request.client.host
        return "unknown"

    def _redact_sensitive(self, data: dict) -> dict:
        """Redact sensitive fields from data for logging."""
        redacted = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_FIELDS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        return redacted
