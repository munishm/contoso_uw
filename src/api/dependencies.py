"""
FastAPI dependency injection module.

Provides dependencies for database clients and services.
"""

from typing import Annotated

from fastapi import Depends

from src.api.config.settings import Settings, get_settings
from src.api.middleware.correlation import get_correlation_id
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.counter_repository import CounterRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.repositories.summary_repository import SummaryRepository
from src.api.services.queue_service import QueueService, queue_service
from src.api.services.storage_service import StorageService, storage_service


# Type aliases for cleaner dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
CorrelationId = Annotated[str, Depends(get_correlation_id)]


# Repository dependencies
def get_counter_repository() -> CounterRepository:
    """Get counter repository instance."""
    return CounterRepository()


def get_case_repository() -> CaseRepository:
    """Get case repository instance."""
    return CaseRepository()


def get_document_repository() -> DocumentRepository:
    """Get document repository instance."""
    return DocumentRepository()


def get_entity_repository() -> EntityRepository:
    """Get entity repository instance."""
    return EntityRepository()


def get_summary_repository() -> SummaryRepository:
    """Get summary repository instance."""
    return SummaryRepository()


CounterRepoDep = Annotated[CounterRepository, Depends(get_counter_repository)]
CaseRepoDep = Annotated[CaseRepository, Depends(get_case_repository)]
DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repository)]
EntityRepoDep = Annotated[EntityRepository, Depends(get_entity_repository)]
SummaryRepoDep = Annotated[SummaryRepository, Depends(get_summary_repository)]


# Service dependencies
def get_storage_service() -> StorageService:
    """Get storage service instance."""
    return storage_service


def get_queue_service() -> QueueService:
    """Get queue service instance."""
    return queue_service


StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]
QueueServiceDep = Annotated[QueueService, Depends(get_queue_service)]
