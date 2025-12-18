"""
Application Insights telemetry integration.

Provides telemetry export to Azure Application Insights for distributed tracing,
metrics, and logging.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.api.config.settings import Settings

logger = logging.getLogger(__name__)

# Global telemetry client
_telemetry_client: Optional["TelemetryClient"] = None


class TelemetryClient:
    """
    Application Insights telemetry client.

    Provides methods for tracking events, metrics, and traces.
    """

    def __init__(self, connection_string: str) -> None:
        """
        Initialize telemetry client.

        Args:
            connection_string: Application Insights connection string
        """
        self.connection_string = connection_string
        self._initialized = False

        try:
            # Import OpenTelemetry components if available
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # Try to import Azure exporter
            try:
                from azure.monitor.opentelemetry.exporter import (
                    AzureMonitorTraceExporter,
                )

                # Configure tracer provider
                trace.set_tracer_provider(TracerProvider())
                tracer_provider = trace.get_tracer_provider()

                # Add Azure Monitor exporter
                exporter = AzureMonitorTraceExporter(
                    connection_string=connection_string
                )
                span_processor = BatchSpanProcessor(exporter)
                tracer_provider.add_span_processor(span_processor)  # type: ignore

                self._tracer = trace.get_tracer(__name__)
                self._initialized = True
                logger.info("Application Insights telemetry initialized")

            except ImportError:
                logger.warning(
                    "azure-monitor-opentelemetry-exporter not installed. "
                    "Install with: pip install azure-monitor-opentelemetry-exporter"
                )

        except ImportError:
            logger.warning(
                "OpenTelemetry not installed. Telemetry disabled. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk"
            )

    @property
    def is_initialized(self) -> bool:
        """Check if telemetry is properly initialized."""
        return self._initialized

    def track_event(
        self,
        name: str,
        properties: Optional[dict[str, str]] = None,
        measurements: Optional[dict[str, float]] = None,
    ) -> None:
        """
        Track a custom event.

        Args:
            name: Event name
            properties: String properties to attach
            measurements: Numeric measurements to attach
        """
        if not self._initialized:
            return

        with self._tracer.start_as_current_span(name) as span:
            if properties:
                for key, value in properties.items():
                    span.set_attribute(key, value)
            if measurements:
                for key, value in measurements.items():
                    span.set_attribute(key, value)

    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Track a custom metric.

        Args:
            name: Metric name
            value: Metric value
            properties: Additional properties
        """
        if not self._initialized:
            return

        with self._tracer.start_as_current_span(f"metric:{name}") as span:
            span.set_attribute("metric.name", name)
            span.set_attribute("metric.value", value)
            if properties:
                for key, val in properties.items():
                    span.set_attribute(key, val)

    def track_exception(
        self,
        exception: Exception,
        properties: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Track an exception.

        Args:
            exception: The exception to track
            properties: Additional properties
        """
        if not self._initialized:
            return

        with self._tracer.start_as_current_span("exception") as span:
            span.record_exception(exception)
            if properties:
                for key, value in properties.items():
                    span.set_attribute(key, value)

    def track_request(
        self,
        method: str,
        url: str,
        duration_ms: float,
        status_code: int,
        success: bool,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Track an HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            success: Whether request was successful
            correlation_id: Correlation ID
        """
        if not self._initialized:
            return

        with self._tracer.start_as_current_span(f"{method} {url}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.duration_ms", duration_ms)
            span.set_attribute("success", success)
            if correlation_id:
                span.set_attribute("correlation_id", correlation_id)


def initialize_telemetry(settings: Settings) -> Optional[TelemetryClient]:
    """
    Initialize the global telemetry client.

    Args:
        settings: Application settings

    Returns:
        Initialized telemetry client or None if not configured
    """
    global _telemetry_client

    if not settings.appinsights_connection_string:
        logger.info("Application Insights not configured - telemetry disabled")
        return None

    _telemetry_client = TelemetryClient(settings.appinsights_connection_string)
    return _telemetry_client


def get_telemetry_client() -> Optional[TelemetryClient]:
    """Get the global telemetry client."""
    return _telemetry_client
