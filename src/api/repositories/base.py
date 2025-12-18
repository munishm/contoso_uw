"""
Base repository with async Cosmos DB client.

Provides common functionality for all Cosmos DB repositories including
client initialization, partition key handling, and standard CRUD operations.
"""

import logging
from typing import Any, Generic, Optional, TypeVar

from azure.cosmos import PartitionKey
from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

from src.api.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=dict[str, Any])


class CosmosDBClient:
    """Singleton Cosmos DB client manager."""

    _instance: Optional["CosmosDBClient"] = None
    _client: Optional[CosmosClient] = None
    _database: Optional[DatabaseProxy] = None

    def __new__(cls) -> "CosmosDBClient":
        """Ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, settings: Optional[Settings] = None) -> None:
        """Initialize the Cosmos DB client."""
        if self._client is not None:
            return

        settings = settings or get_settings()

        if not settings.cosmos_endpoint:
            raise ValueError("COSMOS_ENDPOINT is required")

        if settings.cosmos_key:
            # Use key-based authentication
            self._client = CosmosClient(
                url=settings.cosmos_endpoint,
                credential=settings.cosmos_key,
            )
        else:
            # Use Azure AD authentication
            credential = DefaultAzureCredential()
            self._client = CosmosClient(
                url=settings.cosmos_endpoint,
                credential=credential,
            )

        self._database = self._client.get_database_client(settings.cosmos_database_name)
        logger.info(f"Cosmos DB client initialized for database: {settings.cosmos_database_name}")

    async def close(self) -> None:
        """Close the Cosmos DB client."""
        if self._client:
            await self._client.close()
            self._client = None
            self._database = None
            logger.info("Cosmos DB client closed")

    def get_container(self, container_name: str) -> ContainerProxy:
        """Get a container proxy."""
        if self._database is None:
            raise RuntimeError("Cosmos DB client not initialized. Call initialize() first.")
        return self._database.get_container_client(container_name)

    @property
    def database(self) -> DatabaseProxy:
        """Get the database proxy."""
        if self._database is None:
            raise RuntimeError("Cosmos DB client not initialized. Call initialize() first.")
        return self._database


# Global client instance
cosmos_client = CosmosDBClient()


class BaseRepository(Generic[T]):
    """
    Base repository with common Cosmos DB operations.

    Type Parameters:
        T: The document type (typically a dict)
    """

    def __init__(self, container_name: str, partition_key_path: str):
        """
        Initialize the repository.

        Args:
            container_name: Name of the Cosmos DB container
            partition_key_path: Path to the partition key field (e.g., "/case_id")
        """
        self.container_name = container_name
        self.partition_key_path = partition_key_path
        self._partition_key_field = partition_key_path.lstrip("/")

    @property
    def container(self) -> ContainerProxy:
        """Get the container proxy."""
        return cosmos_client.get_container(self.container_name)

    def _get_partition_key(self, item: dict[str, Any]) -> str:
        """Extract partition key value from an item."""
        return str(item.get(self._partition_key_field, ""))

    async def create(self, item: T) -> T:
        """
        Create a new item in the container.

        Args:
            item: The item to create

        Returns:
            The created item with system properties
        """
        result = await self.container.create_item(body=item)
        logger.debug(f"Created item in {self.container_name}: {item.get('id')}")
        return result

    async def get_by_id(
        self, item_id: str, partition_key: str
    ) -> Optional[T]:
        """
        Get an item by ID.

        Args:
            item_id: The item's unique identifier
            partition_key: The partition key value

        Returns:
            The item if found, None otherwise
        """
        try:
            result = await self.container.read_item(
                item=item_id,
                partition_key=partition_key,
            )
            return result
        except CosmosResourceNotFoundError:
            return None

    async def update(
        self, item: T, etag: Optional[str] = None
    ) -> T:
        """
        Update an existing item.

        Args:
            item: The item to update (must include id and partition key)
            etag: Optional ETag for optimistic concurrency

        Returns:
            The updated item
        """
        kwargs: dict[str, Any] = {"body": item}
        if etag:
            kwargs["if_match"] = etag

        result = await self.container.replace_item(
            item=str(item.get("id")),
            **kwargs,
        )
        logger.debug(f"Updated item in {self.container_name}: {item.get('id')}")
        return result

    async def upsert(self, item: T) -> T:
        """
        Create or update an item.

        Args:
            item: The item to upsert

        Returns:
            The upserted item
        """
        result = await self.container.upsert_item(body=item)
        logger.debug(f"Upserted item in {self.container_name}: {item.get('id')}")
        return result

    async def delete(
        self, item_id: str, partition_key: str
    ) -> bool:
        """
        Delete an item.

        Args:
            item_id: The item's unique identifier
            partition_key: The partition key value

        Returns:
            True if deleted, False if not found
        """
        try:
            await self.container.delete_item(
                item=item_id,
                partition_key=partition_key,
            )
            logger.debug(f"Deleted item from {self.container_name}: {item_id}")
            return True
        except CosmosResourceNotFoundError:
            return False

    async def query(
        self,
        query: str,
        parameters: Optional[list[dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
        max_item_count: Optional[int] = None,
    ) -> list[T]:
        """
        Execute a query against the container.

        Args:
            query: The SQL query string
            parameters: Query parameters
            partition_key: Optional partition key for scoped queries
            max_item_count: Maximum number of items to return

        Returns:
            List of matching items
        """
        kwargs: dict[str, Any] = {
            "query": query,
            "enable_cross_partition_query": partition_key is None,
        }
        if parameters:
            kwargs["parameters"] = parameters
        if partition_key:
            kwargs["partition_key"] = partition_key
        if max_item_count:
            kwargs["max_item_count"] = max_item_count

        items: list[T] = []
        async for item in self.container.query_items(**kwargs):
            items.append(item)

        return items

    async def count(
        self,
        query: Optional[str] = None,
        parameters: Optional[list[dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
    ) -> int:
        """
        Count items matching a query.

        Args:
            query: Optional WHERE clause (without SELECT)
            parameters: Query parameters
            partition_key: Optional partition key for scoped queries

        Returns:
            Count of matching items
        """
        count_query = "SELECT VALUE COUNT(1) FROM c"
        if query:
            count_query += f" WHERE {query}"

        kwargs: dict[str, Any] = {
            "query": count_query,
            "enable_cross_partition_query": partition_key is None,
        }
        if parameters:
            kwargs["parameters"] = parameters
        if partition_key:
            kwargs["partition_key"] = partition_key

        async for result in self.container.query_items(**kwargs):
            return int(result)

        return 0
