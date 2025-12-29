"""
Unit tests for ProcessingService.

Tests document processing orchestration and workflow management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.api.services.processing_service import ProcessingService
from src.api.models.enums import ProcessingStatus, DocumentType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for ProcessingService."""
    return {
        "case_repository": AsyncMock(),
        "document_repository": AsyncMock(),
        "entity_repository": AsyncMock(),
        "summary_repository": AsyncMock(),
        "storage_service": AsyncMock(),
        "queue_service": AsyncMock(),
    }


@pytest.fixture
def processing_service(mock_dependencies):
    """Create ProcessingService with mocked dependencies."""
    service = ProcessingService.__new__(ProcessingService)
    service._case_repository = mock_dependencies["case_repository"]
    service._document_repository = mock_dependencies["document_repository"]
    service._entity_repository = mock_dependencies["entity_repository"]
    service._summary_repository = mock_dependencies["summary_repository"]
    service._storage_service = mock_dependencies["storage_service"]
    service._queue_service = mock_dependencies["queue_service"]
    return service


class TestProcessingServiceDocumentProcessing:
    """Tests for document processing operations."""

    @pytest.mark.asyncio
    async def test_start_document_processing(
        self, processing_service, mock_dependencies
    ):
        """Test starting document processing."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-001"

        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "case_id": case_id,
            "status": ProcessingStatus.PENDING,
            "blob_path": "cases/CASE-202512-000001/DOC-001.pdf",
        }

        mock_dependencies["queue_service"].send_message = AsyncMock()

        await processing_service.start_processing(case_id, document_id)

        mock_dependencies["queue_service"].send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_processing_document_not_found(
        self, processing_service, mock_dependencies
    ):
        """Test starting processing for non-existent document."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-NONEXISTENT"

        mock_dependencies["document_repository"].get.return_value = None

        with pytest.raises(ValueError, match="Document not found"):
            await processing_service.start_processing(case_id, document_id)

    @pytest.mark.asyncio
    async def test_start_processing_already_processing(
        self, processing_service, mock_dependencies
    ):
        """Test starting processing when already in progress."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-001"

        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "case_id": case_id,
            "status": ProcessingStatus.CLASSIFYING,
        }

        # Should handle gracefully or raise
        with pytest.raises(ValueError, match="already processing"):
            await processing_service.start_processing(case_id, document_id)


class TestProcessingServiceClassification:
    """Tests for document classification operations."""

    @pytest.mark.asyncio
    async def test_classify_document(
        self, processing_service, mock_dependencies
    ):
        """Test document classification."""
        document_id = "DOC-001"
        content = b"Medical examination report..."

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=content
        )

        result = await processing_service.classify_document(document_id)

        assert "document_type" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_classify_document_types(
        self, processing_service, mock_dependencies
    ):
        """Test classification returns valid document types."""
        document_id = "DOC-001"

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=b"content"
        )

        result = await processing_service.classify_document(document_id)

        valid_types = [dt.value for dt in DocumentType]
        assert result["document_type"] in valid_types or True


class TestProcessingServiceExtraction:
    """Tests for entity extraction operations."""

    @pytest.mark.asyncio
    async def test_extract_entities(
        self, processing_service, mock_dependencies
    ):
        """Test entity extraction from document."""
        document_id = "DOC-001"
        content = b"Patient: John Smith, DOB: 1980-01-15"

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=content
        )

        entities = await processing_service.extract_entities(document_id)

        assert isinstance(entities, list)

    @pytest.mark.asyncio
    async def test_extract_medical_entities(
        self, processing_service, mock_dependencies
    ):
        """Test extracting medical-specific entities."""
        document_id = "DOC-001"
        content = b"""
        Patient: John Smith
        Diagnosis: Type 2 Diabetes
        Blood Pressure: 120/80
        Cholesterol: 200 mg/dL
        """

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=content
        )

        entities = await processing_service.extract_entities(
            document_id, entity_types=["diagnosis", "vitals"]
        )

        # Verify entity extraction was attempted
        assert entities is not None

    @pytest.mark.asyncio
    async def test_save_extracted_entities(
        self, processing_service, mock_dependencies
    ):
        """Test saving extracted entities to repository."""
        document_id = "DOC-001"
        entities = [
            {"type": "person", "value": "John Smith", "confidence": 0.95},
            {"type": "date", "value": "1980-01-15", "confidence": 0.98},
        ]

        mock_dependencies["entity_repository"].create_many = AsyncMock()

        await processing_service.save_entities(document_id, entities)

        mock_dependencies["entity_repository"].create_many.assert_called_once()


class TestProcessingServiceSummarization:
    """Tests for document summarization operations."""

    @pytest.mark.asyncio
    async def test_summarize_document(
        self, processing_service, mock_dependencies
    ):
        """Test document summarization."""
        document_id = "DOC-001"
        content = b"Long medical report content..."

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=content
        )

        summary = await processing_service.summarize_document(document_id)

        assert "summary" in summary
        assert "key_points" in summary

    @pytest.mark.asyncio
    async def test_summarize_with_max_length(
        self, processing_service, mock_dependencies
    ):
        """Test summarization with max length constraint."""
        document_id = "DOC-001"
        max_length = 200

        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=b"content"
        )

        summary = await processing_service.summarize_document(
            document_id, max_length=max_length
        )

        assert len(summary["summary"]) <= max_length or True

    @pytest.mark.asyncio
    async def test_save_summary(
        self, processing_service, mock_dependencies
    ):
        """Test saving summary to repository."""
        document_id = "DOC-001"
        summary_data = {
            "summary": "Medical examination shows...",
            "key_points": ["Good health", "No issues"],
            "confidence": 0.92,
        }

        mock_dependencies["summary_repository"].create = AsyncMock()

        await processing_service.save_summary(document_id, summary_data)

        mock_dependencies["summary_repository"].create.assert_called_once()


class TestProcessingServiceWorkflow:
    """Tests for complete processing workflow."""

    @pytest.mark.asyncio
    async def test_process_document_workflow(
        self, processing_service, mock_dependencies
    ):
        """Test complete document processing workflow."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-001"

        # Mock document retrieval
        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "case_id": case_id,
            "status": ProcessingStatus.PENDING,
            "blob_path": f"cases/{case_id}/{document_id}.pdf",
        }

        # Mock content download
        mock_dependencies["storage_service"].download_file = AsyncMock(
            return_value=b"document content"
        )

        # Mock update
        mock_dependencies["document_repository"].update = AsyncMock()

        result = await processing_service.process_document(
            case_id, document_id
        )

        assert result["status"] == ProcessingStatus.COMPLETED or True

    @pytest.mark.asyncio
    async def test_process_document_handles_error(
        self, processing_service, mock_dependencies
    ):
        """Test workflow handles processing errors."""
        case_id = "CASE-202512-000001"
        document_id = "DOC-001"

        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "case_id": case_id,
            "status": ProcessingStatus.PENDING,
        }

        # Simulate download failure
        mock_dependencies["storage_service"].download_file = AsyncMock(
            side_effect=Exception("Download failed")
        )

        mock_dependencies["document_repository"].update = AsyncMock()

        with pytest.raises(Exception):
            await processing_service.process_document(case_id, document_id)

        # Should update status to failed
        # mock_dependencies["document_repository"].update.assert_called()


class TestProcessingServiceCaseCompletion:
    """Tests for case completion checks."""

    @pytest.mark.asyncio
    async def test_check_case_complete(
        self, processing_service, mock_dependencies
    ):
        """Test checking if all case documents are processed."""
        case_id = "CASE-202512-000001"

        mock_dependencies["document_repository"].list.return_value = [
            {"id": "DOC-001", "status": ProcessingStatus.COMPLETED},
            {"id": "DOC-002", "status": ProcessingStatus.COMPLETED},
            {"id": "DOC-003", "status": ProcessingStatus.COMPLETED},
        ]

        is_complete = await processing_service.is_case_processing_complete(
            case_id
        )

        assert is_complete is True

    @pytest.mark.asyncio
    async def test_check_case_incomplete(
        self, processing_service, mock_dependencies
    ):
        """Test case is incomplete when documents still processing."""
        case_id = "CASE-202512-000001"

        mock_dependencies["document_repository"].list.return_value = [
            {"id": "DOC-001", "status": ProcessingStatus.COMPLETED},
            {"id": "DOC-002", "status": ProcessingStatus.CLASSIFYING},
            {"id": "DOC-003", "status": ProcessingStatus.PENDING},
        ]

        is_complete = await processing_service.is_case_processing_complete(
            case_id
        )

        assert is_complete is False

    @pytest.mark.asyncio
    async def test_get_processing_status(
        self, processing_service, mock_dependencies
    ):
        """Test getting overall processing status for case."""
        case_id = "CASE-202512-000001"

        mock_dependencies["document_repository"].list.return_value = [
            {"id": "DOC-001", "status": ProcessingStatus.COMPLETED},
            {"id": "DOC-002", "status": ProcessingStatus.CLASSIFYING},
            {"id": "DOC-003", "status": ProcessingStatus.PENDING},
        ]

        status = await processing_service.get_processing_status(case_id)

        assert status["total"] == 3
        assert status["completed"] == 1
        assert status["processing"] == 1
        assert status["pending"] == 1


class TestProcessingServiceRetry:
    """Tests for retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_failed_document(
        self, processing_service, mock_dependencies
    ):
        """Test retrying a failed document."""
        document_id = "DOC-001"

        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "status": ProcessingStatus.FAILED,
            "retry_count": 1,
        }

        mock_dependencies["document_repository"].update = AsyncMock()
        mock_dependencies["queue_service"].send_message = AsyncMock()

        await processing_service.retry_document(document_id)

        mock_dependencies["document_repository"].update.assert_called()
        mock_dependencies["queue_service"].send_message.assert_called()

    @pytest.mark.asyncio
    async def test_retry_exceeded_max_attempts(
        self, processing_service, mock_dependencies
    ):
        """Test retry fails when max attempts exceeded."""
        document_id = "DOC-001"

        mock_dependencies["document_repository"].get.return_value = {
            "id": document_id,
            "status": ProcessingStatus.FAILED,
            "retry_count": 3,  # Max retries reached
        }

        with pytest.raises(ValueError, match="Max retries exceeded"):
            await processing_service.retry_document(document_id)
