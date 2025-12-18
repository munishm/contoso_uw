"""Pydantic models for API request/response schemas."""

from src.api.models.case import (
    CaseCreateRequest,
    CaseDetailResponse,
    CaseListResponse,
    CaseSummaryResponse,
    CaseUpdateRequest,
    DocumentSummaryInCase,
    StatusHistoryEntry,
    StatusHistoryResponse,
)
from src.api.models.common import (
    ErrorResponse,
    HealthResponse,
    PaginationMeta,
    ValidationErrorResponse,
)
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
from src.api.models.enums import CaseStatus, DocumentType, ProcessingStatus

__all__ = [
    # Case models
    "CaseCreateRequest",
    "CaseUpdateRequest",
    "CaseSummaryResponse",
    "CaseDetailResponse",
    "CaseListResponse",
    "DocumentSummaryInCase",
    "StatusHistoryEntry",
    "StatusHistoryResponse",
    # Document models
    "DocumentUploadResponse",
    "DocumentMetadataUpdateRequest",
    "DocumentSummaryResponse",
    "DocumentDetailResponse",
    "DocumentListResponse",
    "DocumentDownloadResponse",
    "DocumentEntitiesResponse",
    "ExtractedEntity",
    # Common models
    "ErrorResponse",
    "ValidationErrorResponse",
    "HealthResponse",
    "PaginationMeta",
    # Enums
    "CaseStatus",
    "ProcessingStatus",
    "DocumentType",
]
