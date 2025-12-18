"""
Entity repository for Cosmos DB operations.

Handles all data access for extracted entities with partition key /document_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EntityRepository(BaseRepository[dict[str, Any]]):
    """Repository for entity data access."""

    CONTAINER_NAME = "entities"
    PARTITION_KEY = "/document_id"

    def __init__(self):
        """Initialize the entity repository."""
        super().__init__(self.CONTAINER_NAME, self.PARTITION_KEY)

    async def create_entity(self, entity_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new entity record.

        Args:
            entity_data: Entity data

        Returns:
            The created entity record
        """
        now = datetime.now(timezone.utc).isoformat()
        entity_data.setdefault("created_at", now)

        return await self.create(entity_data)

    async def create_entities_batch(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Create multiple entities in batch.

        Args:
            entities: List of entity data

        Returns:
            List of created entity records
        """
        created = []
        for entity in entities:
            result = await self.create_entity(entity)
            created.append(result)
        return created

    async def get_entity(
        self, entity_id: str, document_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Get an entity by ID.

        Args:
            entity_id: The entity identifier
            document_id: The parent document identifier (partition key)

        Returns:
            The entity record if found, None otherwise
        """
        return await self.get_by_id(entity_id, document_id)

    async def list_entities_for_document(
        self,
        document_id: str,
        entity_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """
        List all entities for a document.

        Args:
            document_id: The document identifier
            entity_type: Optional entity type filter
            min_confidence: Optional minimum confidence filter

        Returns:
            List of entity records
        """
        conditions = ["c.document_id = @document_id"]
        parameters: list[dict[str, Any]] = [
            {"name": "@document_id", "value": document_id}
        ]

        if entity_type:
            conditions.append("c.entity_type = @entity_type")
            parameters.append({"name": "@entity_type", "value": entity_type})

        if min_confidence is not None:
            conditions.append("c.confidence >= @min_confidence")
            parameters.append({"name": "@min_confidence", "value": min_confidence})

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.page_number, c.confidence DESC"

        return await self.query(query, parameters, partition_key=document_id)

    async def count_entities_for_document(self, document_id: str) -> int:
        """
        Count entities for a document.

        Args:
            document_id: The document identifier

        Returns:
            Number of entities
        """
        return await self.count(
            "c.document_id = @document_id",
            [{"name": "@document_id", "value": document_id}],
            partition_key=document_id,
        )

    async def delete_entities_for_document(self, document_id: str) -> int:
        """
        Delete all entities for a document.

        Args:
            document_id: The document identifier

        Returns:
            Number of entities deleted
        """
        entities = await self.list_entities_for_document(document_id)
        count = 0
        for entity in entities:
            if await self.delete(entity["id"], document_id):
                count += 1
        return count

    async def get_entity_types_for_document(
        self, document_id: str
    ) -> list[str]:
        """
        Get distinct entity types for a document.

        Args:
            document_id: The document identifier

        Returns:
            List of distinct entity types
        """
        query = """
            SELECT DISTINCT VALUE c.entity_type
            FROM c
            WHERE c.document_id = @document_id
        """
        parameters = [{"name": "@document_id", "value": document_id}]

        return await self.query(query, parameters, partition_key=document_id)
