"""
Unit tests for QueueService.

Tests Service Bus queue operations with Azure AD authentication.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.api.services.queue_service import QueueService


@pytest.fixture
def mock_service_bus_client():
    """Create mock ServiceBusClient."""
    mock_client = MagicMock()
    mock_sender = MagicMock()
    mock_receiver = MagicMock()

    mock_client.get_queue_sender.return_value = mock_sender
    mock_client.get_queue_receiver.return_value = mock_receiver

    return mock_client


@pytest.fixture
def queue_service(mock_service_bus_client):
    """Create QueueService with mocked client."""
    with patch(
        "src.api.services.queue_service.ServiceBusClient"
    ) as mock_class:
        mock_class.return_value = mock_service_bus_client

        service = QueueService.__new__(QueueService)
        service._client = mock_service_bus_client
        service._queue_name = "test-queue"
        service._namespace = "test-namespace.servicebus.windows.net"

        return service


class TestQueueServiceInitialization:
    """Tests for QueueService initialization."""

    @patch("src.api.services.queue_service.DefaultAzureCredential")
    @patch("src.api.services.queue_service.ServiceBusClient")
    def test_init_with_namespace(self, mock_client_class, mock_credential):
        """Test initialization with namespace (Azure AD auth)."""
        mock_credential_instance = MagicMock()
        mock_credential.return_value = mock_credential_instance

        service = QueueService(
            namespace="mynamespace.servicebus.windows.net",
            queue_name="my-queue",
        )

        mock_credential.assert_called_once()
        mock_client_class.assert_called_once()

    @patch("src.api.services.queue_service.ServiceBusClient")
    def test_init_with_connection_string(self, mock_client_class):
        """Test initialization with connection string fallback."""
        service = QueueService(
            connection_string="Endpoint=sb://test.servicebus.windows.net/;",
            queue_name="my-queue",
        )

        mock_client_class.from_connection_string.assert_called_once()


class TestQueueServiceSendMessage:
    """Tests for sending messages to queue."""

    @pytest.mark.asyncio
    async def test_send_message(self, queue_service, mock_service_bus_client):
        """Test sending a simple message."""
        message_body = {"case_id": "CASE-001", "action": "process"}

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.send_messages = AsyncMock()

        await queue_service.send_message(message_body)

        mock_sender.send_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_properties(
        self, queue_service, mock_service_bus_client
    ):
        """Test sending message with custom properties."""
        message_body = {"case_id": "CASE-001", "action": "classify"}
        properties = {
            "priority": "high",
            "source": "api",
            "correlation_id": "corr-123",
        }

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.send_messages = AsyncMock()

        await queue_service.send_message(
            message_body, application_properties=properties
        )

        mock_sender.send_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_batch_messages(
        self, queue_service, mock_service_bus_client
    ):
        """Test sending multiple messages in batch."""
        messages = [
            {"case_id": "CASE-001", "action": "process"},
            {"case_id": "CASE-002", "action": "process"},
            {"case_id": "CASE-003", "action": "process"},
        ]

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.send_messages = AsyncMock()

        await queue_service.send_batch(messages)

        mock_sender.send_messages.assert_called_once()


class TestQueueServiceReceiveMessages:
    """Tests for receiving messages from queue."""

    @pytest.mark.asyncio
    async def test_receive_messages(
        self, queue_service, mock_service_bus_client
    ):
        """Test receiving messages from queue."""
        mock_message = MagicMock()
        mock_message.body = json.dumps(
            {"case_id": "CASE-001", "action": "process"}
        ).encode()

        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver.__aexit__ = AsyncMock(return_value=None)
        mock_receiver.receive_messages = AsyncMock(return_value=[mock_message])

        messages = await queue_service.receive_messages(max_messages=1)

        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_receive_messages_empty_queue(
        self, queue_service, mock_service_bus_client
    ):
        """Test receiving from empty queue."""
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver.__aexit__ = AsyncMock(return_value=None)
        mock_receiver.receive_messages = AsyncMock(return_value=[])

        messages = await queue_service.receive_messages(max_messages=10)

        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_receive_messages_with_timeout(
        self, queue_service, mock_service_bus_client
    ):
        """Test receiving messages with custom timeout."""
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver.__aexit__ = AsyncMock(return_value=None)
        mock_receiver.receive_messages = AsyncMock(return_value=[])

        await queue_service.receive_messages(
            max_messages=5, max_wait_time=30
        )

        call_kwargs = mock_receiver.receive_messages.call_args.kwargs
        assert call_kwargs.get("max_wait_time") == 30


class TestQueueServiceMessageCompletion:
    """Tests for message completion and abandonment."""

    @pytest.mark.asyncio
    async def test_complete_message(
        self, queue_service, mock_service_bus_client
    ):
        """Test completing a message."""
        mock_message = MagicMock()
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.complete_message = AsyncMock()

        await queue_service.complete_message(mock_message)

        mock_receiver.complete_message.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_abandon_message(
        self, queue_service, mock_service_bus_client
    ):
        """Test abandoning a message."""
        mock_message = MagicMock()
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.abandon_message = AsyncMock()

        await queue_service.abandon_message(mock_message)

        mock_receiver.abandon_message.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_dead_letter_message(
        self, queue_service, mock_service_bus_client
    ):
        """Test moving message to dead letter queue."""
        mock_message = MagicMock()
        reason = "Processing failed"
        description = "Document extraction failed after 3 retries"

        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.dead_letter_message = AsyncMock()

        await queue_service.dead_letter_message(
            mock_message, reason=reason, error_description=description
        )

        mock_receiver.dead_letter_message.assert_called_once()


class TestQueueServiceScheduledMessages:
    """Tests for scheduled message operations."""

    @pytest.mark.asyncio
    async def test_schedule_message(
        self, queue_service, mock_service_bus_client
    ):
        """Test scheduling a message for later delivery."""
        message_body = {"case_id": "CASE-001", "action": "reminder"}
        scheduled_time = datetime(2025, 12, 18, 10, 0, 0)

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.schedule_messages = AsyncMock(return_value=[12345])

        sequence_numbers = await queue_service.schedule_message(
            message_body, scheduled_time
        )

        mock_sender.schedule_messages.assert_called_once()
        assert 12345 in sequence_numbers

    @pytest.mark.asyncio
    async def test_cancel_scheduled_message(
        self, queue_service, mock_service_bus_client
    ):
        """Test canceling a scheduled message."""
        sequence_number = 12345

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.cancel_scheduled_messages = AsyncMock()

        await queue_service.cancel_scheduled_message(sequence_number)

        mock_sender.cancel_scheduled_messages.assert_called_once_with(
            sequence_number
        )


class TestQueueServiceHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(
        self, queue_service, mock_service_bus_client
    ):
        """Test health check returns healthy status."""
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver.__aexit__ = AsyncMock(return_value=None)
        mock_receiver.peek_messages = AsyncMock(return_value=[])

        result = await queue_service.health_check()

        assert result["healthy"] is True
        assert result["service"] == "service_bus"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(
        self, queue_service, mock_service_bus_client
    ):
        """Test health check returns unhealthy on error."""
        mock_receiver = mock_service_bus_client.get_queue_receiver()
        mock_receiver.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver.__aexit__ = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        result = await queue_service.health_check()

        assert result["healthy"] is False
        assert "error" in result


class TestQueueServiceProcessingMessages:
    """Tests for document processing message patterns."""

    @pytest.mark.asyncio
    async def test_send_document_processing_request(
        self, queue_service, mock_service_bus_client
    ):
        """Test sending document processing request."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-001"
        processing_type = "classification"

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.send_messages = AsyncMock()

        await queue_service.send_processing_request(
            case_id=case_id,
            document_id=document_id,
            processing_type=processing_type,
        )

        mock_sender.send_messages.assert_called_once()
        call_args = mock_sender.send_messages.call_args[0][0]

        # Verify message structure
        message_body = json.loads(str(call_args))
        assert message_body["case_id"] == case_id
        assert message_body["document_id"] == document_id
        assert message_body["processing_type"] == processing_type

    @pytest.mark.asyncio
    async def test_send_case_completion_notification(
        self, queue_service, mock_service_bus_client
    ):
        """Test sending case completion notification."""
        case_id = "CASE-202512-000001"
        status = "approved"

        mock_sender = mock_service_bus_client.get_queue_sender()
        mock_sender.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender.__aexit__ = AsyncMock(return_value=None)
        mock_sender.send_messages = AsyncMock()

        await queue_service.send_case_notification(
            case_id=case_id,
            notification_type="completion",
            status=status,
        )

        mock_sender.send_messages.assert_called_once()
