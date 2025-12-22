"""
Case repository for Cosmos DB operations.

Handles all data access for underwriting cases with partition key /case_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.api.models.enums import CaseStatus
from src.api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CaseRepository(BaseRepository[dict[str, Any]]):
    """Repository for case data access."""

    CONTAINER_NAME = "cases"
    PARTITION_KEY = "/case_id"

    def __init__(self):
        """Initialize the case repository."""
        super().__init__(self.CONTAINER_NAME, self.PARTITION_KEY)

    async def create_case(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new case.

        Args:
            case_data: Case data including case_id

        Returns:
            The created case document
        """
        now = datetime.now(timezone.utc).isoformat()
        case_data.setdefault("created_at", now)
        case_data.setdefault("updated_at", now)
        case_data.setdefault("status", CaseStatus.DRAFT.value)
        case_data.setdefault("deleted_at", None)
        case_data.setdefault("status_history", [])

        # Add initial status history entry
        case_data["status_history"].append({
            "previous_status": None,
            "new_status": case_data["status"],
            "changed_by": case_data.get("created_by", "system"),
            "changed_at": now,
            "reason": "Case created",
        })

        return await self.create(case_data)

    async def get_case(self, case_id: str) -> Optional[dict[str, Any]]:
        """
        Get a case by ID.

        Args:
            case_id: The case identifier

        Returns:
            The case document if found, None otherwise
        """
        return await self.get_by_id(case_id, case_id)

    async def update_case(
        self,
        case_id: str,
        updates: dict[str, Any],
        user_id: str,
        etag: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Update a case with status history tracking.

        Args:
            case_id: The case identifier
            updates: Fields to update
            user_id: ID of the user making the update
            etag: Optional ETag for optimistic concurrency

        Returns:
            The updated case document
        """
        case = await self.get_case(case_id)
        if not case:
            return None

        now = datetime.now(timezone.utc).isoformat()

        # Track status changes
        if "status" in updates and updates["status"] != case.get("status"):
            status_entry = {
                "previous_status": case.get("status"),
                "new_status": updates["status"],
                "changed_by": user_id,
                "changed_at": now,
                "reason": updates.pop("status_reason", None),
            }
            case.setdefault("status_history", []).append(status_entry)
            case["previous_status"] = case.get("status")

        # Apply updates
        for key, value in updates.items():
            if value is not None:
                case[key] = value

        case["updated_at"] = now

        return await self.update(case, etag)

    async def soft_delete_case(
        self, case_id: str, user_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Soft delete a case by setting deleted_at and status.

        Args:
            case_id: The case identifier
            user_id: ID of the user performing deletion

        Returns:
            The updated case document
        """
        return await self.update_case(
            case_id=case_id,
            updates={
                "status": CaseStatus.DELETED.value,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "status_reason": "Soft deleted",
            },
            user_id=user_id,
        )

    async def restore_case(
        self, case_id: str, user_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Restore a soft-deleted case.

        Args:
            case_id: The case identifier
            user_id: ID of the user restoring the case

        Returns:
            The restored case document
        """
        case = await self.get_case(case_id)
        if not case or case.get("status") != CaseStatus.DELETED.value:
            return None

        # Restore to previous status or draft
        previous_status = case.get("previous_status", CaseStatus.DRAFT.value)

        return await self.update_case(
            case_id=case_id,
            updates={
                "status": previous_status,
                "deleted_at": None,
                "status_reason": "Restored from deletion",
            },
            user_id=user_id,
        )

    async def list_cases(
        self,
        filters: Optional[dict[str, Any]] = None,
        client_name_search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List cases with pagination and filtering.

        Args:
            filters: Optional dictionary of field filters (e.g., {"status": "active", "is_deleted": False})
            client_name_search: Optional search string for client name
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Tuple of (list of cases, total count)
        """
        # Build query conditions
        conditions = []
        parameters: list[dict[str, Any]] = []

        if filters:
            if "is_deleted" in filters:
                if not filters["is_deleted"]:
                    conditions.append("(c.status != @deleted_status OR NOT IS_DEFINED(c.status))")
                    parameters.append({"name": "@deleted_status", "value": CaseStatus.DELETED.value})

            if "status" in filters:
                conditions.append("c.status = @status")
                parameters.append({"name": "@status", "value": filters["status"]})

            if "assigned_to" in filters:
                conditions.append("c.assigned_to = @assigned_to")
                parameters.append({"name": "@assigned_to", "value": filters["assigned_to"]})

        if client_name_search:
            conditions.append("CONTAINS(LOWER(c.client_name), LOWER(@client_name_search))")
            parameters.append({"name": "@client_name_search", "value": client_name_search})

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        total = await self.count(where_clause, parameters)

        # Get paginated results
        query = f"""
            SELECT * FROM c
            WHERE {where_clause}
            ORDER BY c.created_at DESC
            OFFSET {offset} LIMIT {limit}
        """

        cases = await self.query(query, parameters)

        return cases, total

    async def get_status_history(self, case_id: str) -> list[dict[str, Any]]:
        """
        Get the status history for a case.

        Args:
            case_id: The case identifier

        Returns:
            List of status history entries
        """
        case = await self.get_case(case_id)
        if not case:
            return []
        return case.get("status_history", [])
