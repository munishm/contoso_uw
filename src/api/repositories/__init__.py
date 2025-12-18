"""Data access layer for Cosmos DB operations."""

from src.api.repositories.base import BaseRepository, CosmosDBClient, cosmos_client
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.counter_repository import CounterRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.repositories.summary_repository import SummaryRepository

__all__ = [
    # Base classes
    "BaseRepository",
    "CosmosDBClient",
    "cosmos_client",
    # Repositories
    "CaseRepository",
    "CounterRepository",
    "DocumentRepository",
    "EntityRepository",
    "SummaryRepository",
]
