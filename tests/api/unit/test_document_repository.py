"""
Unit tests for DocumentRepository.

Tests document data access operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from src.api.repositories.document_repository import DocumentRepository
from src.api.models.enums import ProcessingStatus, DocumentType


@pytest.fixture
def mock_container():
    """Create a mock Cosmos DB container."""
    container = AsyncMock()
    container.create_item = AsyncMock()
    container.read_item = AsyncMock()
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = MagicMock()
    return container


@pytest.fixture
def document_repository(mock_container):
    """Create DocumentRepository with mocked container."""
    with patch.object(DocumentRepository, 'container', new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = mock_container
        repo = DocumentRepository()
        yield repo


@pytest.fixture
def sample_document():
    """Sample document data."""
    return {
        "id": "DOC-001",
        "case_id": "CASE-202512-000001",
        "filename": "medical_report.pdf",
        "original_filename": "medical_report.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024000,
        "blob_path": "cases/CASE-202512-000001/DOC-001.pdf",
        "document_type": DocumentType.MEDICAL_REPORT.value,
        "processing_status": ProcessingStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "user@example.com",
        "metadata": {},
        "is_deleted": False,
        "processing_history": [],
    }


class TestDocumentRepositoryCreate:
    """Tests for document creation."""

    @pytest.mark.asyncio
    async def test_create_document(
        self, document_repository, mock_container, sample_document
    ):
        """Test creating a new document."""
        mock_container.create_item.return_value = sample_document

        result = await document_repository.create_document({
            "id": "DOC-001",
            "case_id": "CASE-202512-000001",
            "filename": "medical_report.pdf",
        })

        mock_container.create_item.assert_called_once()
        call_args = mock_container.create_item.call_args[1]
        item = call_args["body"]

        # Check defaults are set
        assert "created_at" in item
        assert "updated_at" in item
        assert item.get("processing_status") == ProcessingStatus.PENDING.value
        assert "processing_history" in item

    @pytest.mark.asyncio
    async def test_create_document_with_processing_history(
        self, document_repository, mock_container, sample_document
    ):
        """Test that document creation adds initial processing history."""
        mock_container.create_item.return_value = sample_document

        await document_repository.create_document({
            "id": "DOC-001",
            "case_id": "CASE-202512-000001",
        })

        call_args = mock_container.create_item.call_args[1]
        item = call_args["body"]

        assert len(item.get("processing_history", [])) > 0
        assert item["processing_history"][0]["status"] == ProcessingStatus.PENDING.value


class TestDocumentRepositoryGet:
    """Tests for document retrieval."""

    @pytest.mark.asyncio
    async def test_get_document(
        self, document_repository, mock_container, sample_document
    ):
        """Test retrieving a document by ID."""
        mock_container.read_item.return_value = sample_document

        result = await document_repository.get_document(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
        )

        mock_container.read_item.assert_called_once_with(
            item="DOC-001",
            partition_key="CASE-202512-000001",
        )
        assert result["id"] == "DOC-001"

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, document_repository, mock_container
    ):
        """Test retrieving a non-existent document returns None."""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item.side_effect = CosmosResourceNotFoundError(
            status_code=404,
            message="Not found",
        )

        result = await document_repository.get_document(
            document_id="DOC-NONEXISTENT",
            case_id="CASE-202512-000001",
        )

        assert result is None


class TestDocumentRepositoryUpdate:
    """Tests for document updates."""

    @pytest.mark.asyncio
    async def test_update_document(
        self, document_repository, mock_container, sample_document
    ):
        """Test updating a document."""
        mock_container.read_item.return_value = sample_document
        updated_doc = {**sample_document, "filename": "updated_report.pdf"}
        mock_container.replace_item.return_value = updated_doc

        result = await document_repository.update_document(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
            updates={"filename": "updated_report.pdf"},
        )

        mock_container.replace_item.assert_called_once()
        assert result["filename"] == "updated_report.pdf"

    @pytest.mark.asyncio
    async def test_update_document_tracks_status_change(
        self, document_repository, mock_container, sample_document
    ):
        """Test that status changes are tracked in processing_history."""
        mock_container.read_item.return_value = sample_document
        mock_container.replace_item.return_value = {
            **sample_document,
            "processing_status": ProcessingStatus.CLASSIFYING.value,
        }

        await document_repository.update_document(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
            updates={"processing_status": ProcessingStatus.CLASSIFYING.value},
        )

        call_args = mock_container.replace_item.call_args[1]
        item = call_args["body"]

        # Check processing history was updated
        assert any(
            entry["status"] == ProcessingStatus.CLASSIFYING.value
            for entry in item.get("processing_history", [])
        )


class TestDocumentRepositoryDelete:
    """Tests for document deletion."""

    @pytest.mark.asyncio
    async def test_delete_document(
        self, document_repository, mock_container
    ):
        """Test deleting a document."""
        mock_container.delete_item.return_value = None

        result = await document_repository.delete_document(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
        )

        mock_container.delete_item.assert_called_once_with(
            item="DOC-001",
            partition_key="CASE-202512-000001",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self, document_repository, mock_container
    ):
        """Test deleting a non-existent document."""
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.delete_item.side_effect = CosmosResourceNotFoundError(
            status_code=404,
            message="Not found",
        )

        result = await document_repository.delete_document(
            document_id="DOC-NONEXISTENT",
            case_id="CASE-202512-000001",
        )

        assert result is False


class TestDocumentRepositoryList:
    """Tests for document listing."""

    @pytest.mark.asyncio
    async def test_list_documents_for_case(
        self, document_repository, mock_container, sample_document
    ):
        """Test listing documents for a case."""
        # Create async iterator for query results
        async def async_iter_items():
            yield sample_document

        mock_container.query_items.return_value = async_iter_items()

        result = await document_repository.list_documents_for_case(
            case_id="CASE-202512-000001",
        )

        mock_container.query_items.assert_called_once()
        assert len(result) == 1
        assert result[0]["id"] == "DOC-001"


class TestDocumentRepositoryCount:
    """Tests for document counting."""

    @pytest.mark.asyncio
    async def test_count_documents_for_case(
        self, document_repository, mock_container
    ):
        """Test counting documents for a case."""
        # Create async iterator for count query results
        # SELECT VALUE COUNT(1) returns just the integer directly
        async def async_iter_count():
            yield 5

        mock_container.query_items.return_value = async_iter_count()

        count = await document_repository.count_documents_for_case(
            case_id="CASE-202512-000001",
        )

        assert count == 5


class TestDocumentRepositoryProcessingStatus:
    """Tests for processing status updates."""

    @pytest.mark.asyncio
    async def test_update_processing_status(
        self, document_repository, mock_container, sample_document
    ):
        """Test updating processing status."""
        mock_container.read_item.return_value = sample_document
        mock_container.replace_item.return_value = {
            **sample_document,
            "processing_status": ProcessingStatus.COMPLETED.value,
        }

        result = await document_repository.update_processing_status(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
            status=ProcessingStatus.COMPLETED,
        )

        assert result["processing_status"] == ProcessingStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_update_processing_status_with_error(
        self, document_repository, mock_container, sample_document
    ):
        """Test updating processing status with error message."""
        mock_container.read_item.return_value = sample_document
        mock_container.replace_item.return_value = {
            **sample_document,
            "processing_status": ProcessingStatus.FAILED.value,
            "processing_error": "Classification failed",
        }

        result = await document_repository.update_processing_status(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
            status=ProcessingStatus.FAILED,
            error="Classification failed",
        )

        assert result["processing_status"] == ProcessingStatus.FAILED.value
        assert result["processing_error"] == "Classification failed"


class TestDocumentRepositoryClassification:
    """Tests for document classification."""

    @pytest.mark.asyncio
    async def test_set_classification(
        self, document_repository, mock_container, sample_document
    ):
        """Test setting document classification."""
        mock_container.read_item.return_value = sample_document
        mock_container.replace_item.return_value = {
            **sample_document,
            "classification": "financial_statement",
            "classification_confidence": 0.95,
        }

        result = await document_repository.set_classification(
            document_id="DOC-001",
            case_id="CASE-202512-000001",
            classification="financial_statement",
            confidence=0.95,
        )

        assert result["classification"] == "financial_statement"
        assert result["classification_confidence"] == 0.95
