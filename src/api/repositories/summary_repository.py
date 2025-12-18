"""
Summary repository for Cosmos DB operations.

Handles all data access for document summaries with partition key /document_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SummaryRepository(BaseRepository[dict[str, Any]]):
    """Repository for summary data access."""

    CONTAINER_NAME = "summaries"
    PARTITION_KEY = "/document_id"

    def __init__(self):
        """Initialize the summary repository."""
        super().__init__(self.CONTAINER_NAME, self.PARTITION_KEY)

    async def create_summary(self, summary_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new summary record.

        Args:
            summary_data: Summary data

        Returns:
            The created summary record
        """
        now = datetime.now(timezone.utc).isoformat()
        summary_data.setdefault("created_at", now)

        return await self.create(summary_data)

    async def get_summary(
        self, summary_id: str, document_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Get a summary by ID.

        Args:
            summary_id: The summary identifier
            document_id: The parent document identifier (partition key)

        Returns:
            The summary record if found, None otherwise
        """
        return await self.get_by_id(summary_id, document_id)

    async def get_summary_for_document(
        self, document_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Get the summary for a document (one summary per document).

        Args:
            document_id: The document identifier

        Returns:
            The summary record if found, None otherwise
        """
        query = "SELECT * FROM c WHERE c.document_id = @document_id"
        parameters = [{"name": "@document_id", "value": document_id}]

        summaries = await self.query(query, parameters, partition_key=document_id)
        return summaries[0] if summaries else None

    async def upsert_summary(self, summary_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create or update a summary for a document.

        Args:
            summary_data: Summary data including document_id

        Returns:
            The upserted summary record
        """
        now = datetime.now(timezone.utc).isoformat()
        summary_data.setdefault("created_at", now)
        summary_data["updated_at"] = now

        return await self.upsert(summary_data)

    async def delete_summary_for_document(self, document_id: str) -> bool:
        """
        Delete the summary for a document.

        Args:
            document_id: The document identifier

        Returns:
            True if deleted, False if not found
        """
        summary = await self.get_summary_for_document(document_id)
        if not summary:
            return False
        return await self.delete(summary["id"], document_id)

    async def get_summaries_for_case(
        self, document_ids: list[str]
    ) -> list[dict[str, Any]]:
        """
        Get summaries for multiple documents (for case summary aggregation).

        Args:
            document_ids: List of document identifiers

        Returns:
            List of summary records
        """
        if not document_ids:
            return []

        # Cosmos DB doesn't support IN queries efficiently across partitions,
        # so we fetch each summary individually
        summaries = []
        for doc_id in document_ids:
            summary = await self.get_summary_for_document(doc_id)
            if summary:
                summaries.append(summary)
        return summaries
