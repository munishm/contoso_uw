"""
Document repository for Cosmos DB operations.

Handles all data access for documents with partition key /case_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from src.api.models.enums import ProcessingStatus
from src.api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[dict[str, Any]]):
    """Repository for document data access."""

    CONTAINER_NAME = "documents"
    PARTITION_KEY = "/case_id"

    def __init__(self):
        """Initialize the document repository."""
        super().__init__(self.CONTAINER_NAME, self.PARTITION_KEY)

    async def create_document(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new document record.

        Args:
            document_data: Document metadata

        Returns:
            The created document record
        """
        now = datetime.now(timezone.utc).isoformat()
        document_data.setdefault("created_at", now)
        document_data.setdefault("updated_at", now)
        document_data.setdefault("processing_status", ProcessingStatus.PENDING.value)
        document_data.setdefault("processing_history", [])

        # Add initial processing history entry
        document_data["processing_history"].append({
            "status": ProcessingStatus.PENDING.value,
            "timestamp": now,
        })

        return await self.create(document_data)

    async def get_document(
        self, document_id: str, case_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            document_id: The document identifier
            case_id: The parent case identifier (partition key)

        Returns:
            The document record if found, None otherwise
        """
        return await self.get_by_id(document_id, case_id)

    async def update_document(
        self,
        document_id: str,
        case_id: str,
        updates: dict[str, Any],
        etag: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Update a document record.

        Args:
            document_id: The document identifier
            case_id: The parent case identifier
            updates: Fields to update
            etag: Optional ETag for optimistic concurrency

        Returns:
            The updated document record
        """
        document = await self.get_document(document_id, case_id)
        if not document:
            return None

        now = datetime.now(timezone.utc).isoformat()

        # Track processing status changes
        if "processing_status" in updates:
            new_status = updates["processing_status"]
            if new_status != document.get("processing_status"):
                document.setdefault("processing_history", []).append({
                    "status": new_status,
                    "timestamp": now,
                })

        # Apply updates
        for key, value in updates.items():
            if value is not None:
                document[key] = value

        document["updated_at"] = now

        return await self.update(document, etag)

    async def delete_document(self, document_id: str, case_id: str) -> bool:
        """
        Delete a document record.

        Args:
            document_id: The document identifier
            case_id: The parent case identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.delete(document_id, case_id)

    async def list_documents_for_case(
        self, case_id: str
    ) -> list[dict[str, Any]]:
        """
        List all documents for a case.

        Args:
            case_id: The case identifier

        Returns:
            List of document records
        """
        query = "SELECT * FROM c WHERE c.case_id = @case_id ORDER BY c.created_at DESC"
        parameters = [{"name": "@case_id", "value": case_id}]

        return await self.query(query, parameters, partition_key=case_id)

    async def count_documents_for_case(self, case_id: str) -> int:
        """
        Count documents for a case.

        Args:
            case_id: The case identifier

        Returns:
            Number of documents
        """
        return await self.count(
            "c.case_id = @case_id",
            [{"name": "@case_id", "value": case_id}],
            partition_key=case_id,
        )

    async def update_processing_status(
        self,
        document_id: str,
        case_id: str,
        status: ProcessingStatus,
        error: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Update the processing status of a document.

        Args:
            document_id: The document identifier
            case_id: The parent case identifier
            status: The new processing status
            error: Optional error message (for failed status)

        Returns:
            The updated document record
        """
        updates: dict[str, Any] = {"processing_status": status.value}
        if error:
            updates["processing_error"] = error
        elif status == ProcessingStatus.COMPLETED:
            updates["processing_error"] = None

        return await self.update_document(document_id, case_id, updates)

    async def set_classification(
        self,
        document_id: str,
        case_id: str,
        classification: str,
        confidence: float,
    ) -> Optional[dict[str, Any]]:
        """
        Set the classification for a document.

        Args:
            document_id: The document identifier
            case_id: The parent case identifier
            classification: The document type classification
            confidence: Classification confidence score

        Returns:
            The updated document record
        """
        return await self.update_document(
            document_id,
            case_id,
            {
                "classification": classification,
                "classification_confidence": confidence,
            },
        )
