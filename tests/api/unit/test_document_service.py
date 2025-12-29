"""
Unit tests for DocumentService.

Tests business logic for document management operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from src.api.services.document_service import DocumentService
from src.api.models.enums import ProcessingStatus, DocumentType
from src.api.middleware.error_handler import NotFoundError, BadRequestError


@pytest.fixture
def mock_case_repo():
    """Create a mock case repository."""
    return AsyncMock()


@pytest.fixture
def mock_document_repo():
    """Create a mock document repository."""
    return AsyncMock()


@pytest.fixture
def mock_entity_repo():
    """Create a mock entity repository."""
    return AsyncMock()


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    return AsyncMock()


@pytest.fixture
def mock_queue_service():
    """Create a mock queue service."""
    return AsyncMock()


@pytest.fixture
def document_service(
    mock_case_repo,
    mock_document_repo,
    mock_entity_repo,
    mock_storage_service,
    mock_queue_service,
):
    """Create a document service with mocked dependencies."""
    return DocumentService(
        case_repository=mock_case_repo,
        document_repository=mock_document_repo,
        entity_repository=mock_entity_repo,
        storage_service=mock_storage_service,
        queue_service=mock_queue_service,
    )


@pytest.fixture
def sample_case():
    """Sample case document."""
    return {
        "case_id": "CASE-202512-000001",
        "client_name": "John Smith",
        "status": "draft",
        "is_deleted": False,
    }


@pytest.fixture
def sample_document():
    """Sample document metadata."""
    return {
        "id": "doc-123",
        "document_id": "doc-123",
        "case_id": "CASE-202512-000001",
        "filename": "application.pdf",
        "original_filename": "application.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024000,
        "blob_path": "cases/CASE-202512-000001/documents/doc-123/application.pdf",
        "md5_checksum": "abc123",
        "processing_status": "pending",
        "document_type": None,
        "created_at": "2025-12-17T10:00:00",
        "updated_at": "2025-12-17T10:00:00",
        "uploaded_by": "user@example.com",
    }


class TestDocumentServiceUpload:
    """Tests for document upload."""

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self,
        document_service,
        mock_case_repo,
        mock_document_repo,
        mock_storage_service,
        mock_queue_service,
        sample_case,
        sample_document,
    ):
        """Test successful document upload."""
        # Arrange
        mock_case_repo.get_case.return_value = sample_case
        mock_storage_service.upload_document.return_value = (
            "cases/CASE-202512-000001/documents/doc-123/application.pdf",
            "abc123",
        )
        mock_document_repo.create_document.return_value = sample_document

        file_content = BytesIO(b"PDF content here")

        # Act
        result = await document_service.upload_document(
            case_id="CASE-202512-000001",
            filename="application.pdf",
            content=file_content,
            content_type="application/pdf",
            size_bytes=1024000,
            user_id="user@example.com",
            correlation_id="corr-123",
        )

        # Assert
        assert result.document_id == "doc-123"
        assert result.filename == "application.pdf"
        mock_storage_service.upload_document.assert_called_once()
        mock_queue_service.send_document_uploaded_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_document_case_not_found(
        self,
        document_service,
        mock_case_repo,
    ):
        """Test upload to non-existent case raises NotFoundError."""
        mock_case_repo.get_case.return_value = None

        file_content = BytesIO(b"PDF content")

        with pytest.raises(NotFoundError):
            await document_service.upload_document(
                case_id="CASE-NONEXISTENT",
                filename="doc.pdf",
                content=file_content,
                content_type="application/pdf",
                size_bytes=1024,
                user_id="user@example.com",
                correlation_id="corr-123",
            )

    @pytest.mark.asyncio
    async def test_upload_document_invalid_content_type(
        self,
        document_service,
        mock_case_repo,
        sample_case,
    ):
        """Test upload with invalid content type raises BadRequestError."""
        mock_case_repo.get_case.return_value = sample_case

        file_content = BytesIO(b"content")

        with pytest.raises(BadRequestError):
            await document_service.upload_document(
                case_id="CASE-202512-000001",
                filename="malware.exe",
                content=file_content,
                content_type="application/x-executable",
                size_bytes=1024,
                user_id="user@example.com",
                correlation_id="corr-123",
            )


class TestDocumentServiceGet:
    """Tests for retrieving documents."""

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        document_service,
        mock_document_repo,
        sample_document,
    ):
        """Test successful document retrieval."""
        mock_document_repo.get_document.return_value = sample_document

        result = await document_service.get_document(
            case_id="CASE-202512-000001",
            document_id="doc-123",
        )

        assert result.document_id == "doc-123"
        assert result.filename == "application.pdf"

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self,
        document_service,
        mock_document_repo,
    ):
        """Test getting non-existent document raises NotFoundError."""
        mock_document_repo.get_document.return_value = None

        with pytest.raises(NotFoundError):
            await document_service.get_document(
                case_id="CASE-202512-000001",
                document_id="doc-nonexistent",
            )


class TestDocumentServiceDelete:
    """Tests for deleting documents."""

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        document_service,
        mock_document_repo,
        mock_storage_service,
        sample_document,
    ):
        """Test successful document deletion."""
        mock_document_repo.get_document.return_value = sample_document
        mock_document_repo.delete_document.return_value = True
        mock_storage_service.delete_document.return_value = True

        await document_service.delete_document(
            case_id="CASE-202512-000001",
            document_id="doc-123",
        )

        mock_document_repo.delete_document.assert_called_once()
        mock_storage_service.delete_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        document_service,
        mock_document_repo,
    ):
        """Test deleting non-existent document raises NotFoundError."""
        mock_document_repo.get_document.return_value = None

        with pytest.raises(NotFoundError):
            await document_service.delete_document(
                case_id="CASE-202512-000001",
                document_id="doc-nonexistent",
            )


class TestDocumentServiceList:
    """Tests for listing documents."""

    @pytest.mark.asyncio
    async def test_list_documents_for_case(
        self,
        document_service,
        mock_document_repo,
        sample_document,
    ):
        """Test listing documents for a case."""
        mock_document_repo.list_documents_for_case.return_value = [sample_document]

        result = await document_service.list_documents(
            case_id="CASE-202512-000001",
        )

        assert len(result) == 1
        assert result[0].document_id == "doc-123"

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self,
        document_service,
        mock_document_repo,
    ):
        """Test listing documents with no results."""
        mock_document_repo.list_documents_for_case.return_value = []

        result = await document_service.list_documents(
            case_id="CASE-202512-000001",
        )

        assert len(result) == 0


class TestDocumentServiceDownloadUrl:
    """Tests for generating download URLs."""

    @pytest.mark.asyncio
    async def test_get_download_url_success(
        self,
        document_service,
        mock_document_repo,
        mock_storage_service,
        sample_document,
    ):
        """Test successful download URL generation."""
        mock_document_repo.get_document.return_value = sample_document
        mock_storage_service.get_download_url.return_value = (
            "https://storage.blob.core.windows.net/docs/file?sas=token",
            datetime.utcnow(),
        )

        result = await document_service.get_download_url(
            case_id="CASE-202512-000001",
            document_id="doc-123",
        )

        assert "https://" in result.download_url
        mock_storage_service.get_download_url.assert_called_once()
