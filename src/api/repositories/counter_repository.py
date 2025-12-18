"""
Counter repository for atomic case ID generation.

Uses Cosmos DB stored procedure pattern for atomic increment operations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from src.api.repositories.base import BaseRepository, cosmos_client

logger = logging.getLogger(__name__)


class CounterRepository(BaseRepository[dict[str, Any]]):
    """Repository for managing atomic counters."""

    CONTAINER_NAME = "counters"
    PARTITION_KEY = "/counter_id"

    def __init__(self):
        """Initialize the counter repository."""
        super().__init__(self.CONTAINER_NAME, self.PARTITION_KEY)

    async def get_next_case_id(self) -> str:
        """
        Get the next case ID with atomic increment.

        Format: CASE-YYYYMM-NNNNNN

        Returns:
            The next case ID string
        """
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y%m")
        counter_id = f"case-counter-{year_month}"

        # Try to increment existing counter
        try:
            counter_doc = await self.container.read_item(
                item=counter_id,
                partition_key=counter_id,
            )
            new_value = counter_doc.get("current_value", 0) + 1
            counter_doc["current_value"] = new_value
            counter_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Update with optimistic concurrency
            await self.container.replace_item(
                item=counter_id,
                body=counter_doc,
                if_match=counter_doc.get("_etag"),
            )
        except CosmosResourceNotFoundError:
            # Create new counter for this month
            new_value = 1
            counter_doc = {
                "id": counter_id,
                "counter_id": counter_id,
                "year_month": year_month,
                "current_value": new_value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await self.container.create_item(body=counter_doc)

        case_id = f"CASE-{year_month}-{new_value:06d}"
        logger.info(f"Generated case ID: {case_id}")
        return case_id

    async def get_current_value(self, year_month: str) -> int:
        """
        Get the current counter value for a given month.

        Args:
            year_month: The year-month string (YYYYMM)

        Returns:
            The current counter value, or 0 if not found
        """
        counter_id = f"case-counter-{year_month}"
        try:
            counter_doc = await self.container.read_item(
                item=counter_id,
                partition_key=counter_id,
            )
            return counter_doc.get("current_value", 0)
        except CosmosResourceNotFoundError:
            return 0
