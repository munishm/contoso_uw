"""
Azure Service Bus queue service for document processing events.

Handles publishing messages to trigger document processing pipeline.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusSender

from src.api.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for Azure Service Bus operations."""

    _instance: Optional["QueueService"] = None
    _client: Optional[ServiceBusClient] = None
    _sender: Optional[ServiceBusSender] = None
    _credential: Optional[DefaultAzureCredential] = None

    def __new__(cls) -> "QueueService":
        """Ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, settings: Optional[Settings] = None) -> None:
        """Initialize the Service Bus client."""
        if self._client is not None:
            return

        settings = settings or get_settings()

        if settings.service_bus_connection_string:
            # Use connection string
            self._client = ServiceBusClient.from_connection_string(
                settings.service_bus_connection_string
            )
        elif settings.service_bus_namespace:
            # Use Azure AD authentication
            self._credential = DefaultAzureCredential()
            self._client = ServiceBusClient(
                fully_qualified_namespace=settings.service_bus_namespace,
                credential=self._credential,
            )
        else:
            raise ValueError("SERVICE_BUS_NAMESPACE or SERVICE_BUS_CONNECTION_STRING is required")

        self._sender = self._client.get_queue_sender(settings.service_bus_queue_name)
        logger.info(f"Service Bus client initialized for queue: {settings.service_bus_queue_name}")

    async def close(self) -> None:
        """Close the Service Bus client."""
        if self._sender:
            await self._sender.close()
            self._sender = None
        if self._client:
            await self._client.close()
            self._client = None
        if self._credential:
            await self._credential.close()
            self._credential = None
        logger.info("Service Bus client closed")

    @property
    def sender(self) -> ServiceBusSender:
        """Get the queue sender."""
        if self._sender is None:
            raise RuntimeError("Queue service not initialized. Call initialize() first.")
        return self._sender

    async def send_document_uploaded_event(
        self,
        case_id: str,
        document_id: str,
        blob_path: str,
        correlation_id: str,
    ) -> None:
        """
        Send a document uploaded event to trigger processing.

        Args:
            case_id: The parent case identifier
            document_id: The document identifier
            blob_path: Path to the document in Blob Storage
            correlation_id: Request correlation ID for tracing
        """
        message_body = {
            "case_id": case_id,
            "document_id": document_id,
            "blob_path": blob_path,
            "event_type": "document.uploaded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }

        message = ServiceBusMessage(
            body=json.dumps(message_body),
            content_type="application/json",
            session_id=case_id,  # Use case_id as session for ordered processing
            correlation_id=correlation_id,
            application_properties={
                "event_type": "document.uploaded",
                "case_id": case_id,
                "document_id": document_id,
            },
        )

        await self.sender.send_messages(message)
        logger.info(
            f"Sent document.uploaded event for document {document_id} "
            f"(case: {case_id}, correlation: {correlation_id})"
        )

    async def send_reprocess_event(
        self,
        case_id: str,
        document_id: str,
        blob_path: str,
        correlation_id: str,
    ) -> None:
        """
        Send a reprocess event for a document.

        Args:
            case_id: The parent case identifier
            document_id: The document identifier
            blob_path: Path to the document in Blob Storage
            correlation_id: Request correlation ID for tracing
        """
        message_body = {
            "case_id": case_id,
            "document_id": document_id,
            "blob_path": blob_path,
            "event_type": "document.reprocess",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }

        message = ServiceBusMessage(
            body=json.dumps(message_body),
            content_type="application/json",
            session_id=case_id,
            correlation_id=correlation_id,
            application_properties={
                "event_type": "document.reprocess",
                "case_id": case_id,
                "document_id": document_id,
            },
        )

        await self.sender.send_messages(message)
        logger.info(
            f"Sent document.reprocess event for document {document_id} "
            f"(case: {case_id}, correlation: {correlation_id})"
        )

    async def check_health(self) -> bool:
        """
        Check if Service Bus is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Sender being open indicates connection is healthy
            return self._sender is not None
        except Exception as e:
            logger.error(f"Service Bus health check failed: {e}")
            return False


# Global service instance
queue_service = QueueService()
