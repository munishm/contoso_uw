"""
Document business logic service.

Handles document operations including upload, validation, storage, and retrieval.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from src.api.config.settings import get_settings
from src.api.middleware.error_handler import BadRequestError, NotFoundError
from src.api.models.document import (
    DocumentDetailResponse,
    DocumentDownloadResponse,
    DocumentEntitiesResponse,
    DocumentListResponse,
    DocumentMetadataUpdateRequest,
    DocumentSummaryResponse,
    DocumentUploadResponse,
    ExtractedEntity,
)
from src.api.models.enums import DocumentType, ProcessingStatus
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.services.queue_service import QueueService
from src.api.services.storage_service import StorageService

logger = logging.getLogger(__name__)


# Allowed MIME types for document upload
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentService:
    """Service for document management operations."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        case_repository: CaseRepository,
        entity_repository: EntityRepository,
        storage_service: StorageService,
        queue_service: QueueService,
    ) -> None:
        """
        Initialize document service with dependencies.

        Args:
            document_repository: Repository for document data access
            case_repository: Repository for case data access
            entity_repository: Repository for entity data access
            storage_service: Service for blob storage operations
            queue_service: Service for message queue operations
        """
        self.document_repo = document_repository
        self.case_repo = case_repository
        self.entity_repo = entity_repository
        self.storage_service = storage_service
        self.queue_service = queue_service
        self.settings = get_settings()

    async def upload_document(
        self,
        case_id: str,
        filename: str,
        content_type: str,
        file_content: bytes,
        user_id: str,
    ) -> DocumentUploadResponse:
        """
        Upload a document for a case.

        Args:
            case_id: Case identifier
            filename: Original filename
            content_type: MIME type
            file_content: File content bytes
            user_id: User performing upload

        Returns:
            Upload response with document details

        Raises:
            NotFoundError: If case not found
            BadRequestError: If validation fails
        """
        # Verify case exists
        case = await self.case_repo.get_case(case_id)
        if not case or case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        # Validate content type
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise BadRequestError(
                f"Invalid content type '{content_type}'. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        # Validate file size
        max_size = self.settings.max_upload_size_bytes
        if len(file_content) > max_size:
            raise BadRequestError(
                f"File size {len(file_content)} exceeds maximum {max_size} bytes"
            )

        # Check document count limit (50 per case)
        existing_docs = await self.document_repo.list_documents_for_case(case_id)
        if len(existing_docs) >= 50:
            raise BadRequestError(
                f"Case {case_id} has reached the maximum of 50 documents"
            )

        # Generate document ID and blob path
        document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        blob_path = f"{case_id}/{document_id}/{filename}"

        # Upload to blob storage
        await self.storage_service.upload_document(blob_path, file_content, content_type)
        logger.info(f"Document uploaded to storage: {blob_path}")

        # Create document record
        now = datetime.utcnow()
        document_data = {
            "id": document_id,
            "document_id": document_id,
            "case_id": case_id,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_content),
            "blob_path": blob_path,
            "processing_status": ProcessingStatus.PENDING.value,
            "classification": None,
            "confidence_score": None,
            "extracted_text": None,
            "summary": None,
            "metadata": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": user_id,
            "processing_started_at": None,
            "processing_completed_at": None,
            "processing_error": None,
        }

        created = await self.document_repo.create_document(document_data)
        logger.info(f"Document record created: {document_id}")

        # Send message to processing queue
        await self.queue_service.send_document_uploaded_event(
            document_id=document_id,
            case_id=case_id,
            blob_path=blob_path,
            content_type=content_type,
        )
        logger.info(f"Document processing event sent for: {document_id}")

        return DocumentUploadResponse(
            document_id=created["document_id"],
            case_id=created["case_id"],
            filename=created["filename"],
            content_type=created["content_type"],
            size_bytes=created["size_bytes"],
            processing_status=ProcessingStatus(created["processing_status"]),
            created_at=datetime.fromisoformat(created["created_at"]),
            created_by=created["created_by"],
        )

    async def get_document(self, case_id: str, document_id: str) -> DocumentDetailResponse:
        """
        Get document details.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            Document details

        Raises:
            NotFoundError: If document not found
        """
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(f"Document {document_id} not found in case {case_id}")

        return self._to_detail_response(document)

    async def update_document(
        self,
        case_id: str,
        document_id: str,
        request: DocumentMetadataUpdateRequest,
        user_id: str,
    ) -> DocumentDetailResponse:
        """
        Update document metadata.

        Args:
            case_id: Case identifier
            document_id: Document identifier
            request: Update request
            user_id: User making the update

        Returns:
            Updated document details

        Raises:
            NotFoundError: If document not found
        """
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(f"Document {document_id} not found in case {case_id}")

        updates: dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}

        if request.classification is not None:
            updates["classification"] = request.classification.value

        if request.metadata is not None:
            updates["metadata"] = request.metadata

        updated = await self.document_repo.update_document(document_id, case_id, updates)
        logger.info(f"Document {document_id} metadata updated")

        return self._to_detail_response(updated)

    async def delete_document(
        self,
        case_id: str,
        document_id: str,
        user_id: str,
    ) -> None:
        """
        Delete a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier
            user_id: User performing deletion

        Raises:
            NotFoundError: If document not found
        """
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(f"Document {document_id} not found in case {case_id}")

        # Delete from blob storage
        blob_path = document.get("blob_path")
        if blob_path:
            await self.storage_service.delete_document(blob_path)
            logger.info(f"Document deleted from storage: {blob_path}")

        # Delete from database
        await self.document_repo.delete_document(document_id, case_id)
        logger.info(f"Document record deleted: {document_id}")

    async def list_documents(self, case_id: str) -> DocumentListResponse:
        """
        List all documents for a case.

        Args:
            case_id: Case identifier

        Returns:
            List of documents

        Raises:
            NotFoundError: If case not found
        """
        # Verify case exists
        case = await self.case_repo.get_case(case_id)
        if not case or case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        documents = await self.document_repo.list_documents_for_case(case_id)

        items = [self._to_summary_response(doc) for doc in documents]

        return DocumentListResponse(
            items=items,
            total=len(items),
            case_id=case_id,
        )

    async def get_download_url(
        self,
        case_id: str,
        document_id: str,
    ) -> DocumentDownloadResponse:
        """
        Get a pre-signed download URL for a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            Download response with SAS URL

        Raises:
            NotFoundError: If document not found
        """
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(f"Document {document_id} not found in case {case_id}")

        blob_path = document["blob_path"]
        expiry_hours = 1
        download_url = await self.storage_service.get_download_url(
            blob_path, expiry_hours=expiry_hours
        )

        return DocumentDownloadResponse(
            document_id=document_id,
            filename=document["filename"],
            download_url=download_url,
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
            content_type=document["content_type"],
            size_bytes=document["size_bytes"],
        )

    async def get_entities(
        self,
        case_id: str,
        document_id: str,
    ) -> DocumentEntitiesResponse:
        """
        Get extracted entities for a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            Extracted entities

        Raises:
            NotFoundError: If document not found
        """
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(f"Document {document_id} not found in case {case_id}")

        entities = await self.entity_repo.get_entities_for_document(document_id)

        entity_list = [
            ExtractedEntity(
                entity_id=e["entity_id"],
                entity_type=e["entity_type"],
                value=e["value"],
                confidence=e.get("confidence", 0.0),
                source_location=e.get("source_location"),
            )
            for e in entities
        ]

        extraction_completed = document.get("processing_completed_at")
        return DocumentEntitiesResponse(
            document_id=document_id,
            entities=entity_list,
            extraction_completed_at=(
                datetime.fromisoformat(extraction_completed)
                if extraction_completed
                else None
            ),
        )

    def _to_detail_response(self, document: dict[str, Any]) -> DocumentDetailResponse:
        """Convert document data to detail response."""
        return DocumentDetailResponse(
            document_id=document["document_id"],
            case_id=document["case_id"],
            filename=document["filename"],
            content_type=document["content_type"],
            size_bytes=document["size_bytes"],
            blob_path=document["blob_path"],
            processing_status=ProcessingStatus(document["processing_status"]),
            classification=(
                DocumentType(document["classification"])
                if document.get("classification")
                else None
            ),
            confidence_score=document.get("confidence_score"),
            extracted_text=document.get("extracted_text"),
            summary=document.get("summary"),
            metadata=document.get("metadata", {}),
            created_at=datetime.fromisoformat(document["created_at"]),
            updated_at=datetime.fromisoformat(document["updated_at"]),
            created_by=document["created_by"],
            processing_started_at=(
                datetime.fromisoformat(document["processing_started_at"])
                if document.get("processing_started_at")
                else None
            ),
            processing_completed_at=(
                datetime.fromisoformat(document["processing_completed_at"])
                if document.get("processing_completed_at")
                else None
            ),
            processing_error=document.get("processing_error"),
        )

    def _to_summary_response(self, document: dict[str, Any]) -> DocumentSummaryResponse:
        """Convert document data to summary response."""
        return DocumentSummaryResponse(
            document_id=document["document_id"],
            case_id=document["case_id"],
            filename=document["filename"],
            content_type=document["content_type"],
            size_bytes=document["size_bytes"],
            processing_status=ProcessingStatus(document["processing_status"]),
            classification=(
                DocumentType(document["classification"])
                if document.get("classification")
                else None
            ),
            created_at=datetime.fromisoformat(document["created_at"]),
            updated_at=datetime.fromisoformat(document["updated_at"]),
        )
