"""
Processing results API endpoints.

Provides access to entity extraction results and document summaries.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    CurrentUser,
    get_case_repository,
    get_document_repository,
    get_entity_repository,
    get_queue_service,
    get_summary_repository,
)
from src.api.models.common import ErrorResponse
from src.api.models.entity import (
    EntityAggregateResponse,
    EntityExplainResponse,
    EntityListResponse,
)
from src.api.models.summary import (
    CaseSummaryDetailResponse,
    DocumentSummaryDetailResponse,
    ReprocessRequest,
    ReprocessResponse,
    SummaryExplainResponse,
)
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.repositories.summary_repository import SummaryRepository
from src.api.services.processing_service import ProcessingService
from src.api.services.queue_service import QueueService

router = APIRouter(tags=["Processing"])


def get_processing_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    case_repo: CaseRepository = Depends(get_case_repository),
    entity_repo: EntityRepository = Depends(get_entity_repository),
    summary_repo: SummaryRepository = Depends(get_summary_repository),
    queue_service: QueueService = Depends(get_queue_service),
) -> ProcessingService:
    """Dependency to get processing service instance."""
    return ProcessingService(
        document_repo, case_repo, entity_repo, summary_repo, queue_service
    )


@router.get(
    "/cases/{case_id}/documents/{document_id}/entities",
    response_model=EntityListResponse,
    summary="Get document entities",
    description="Retrieve all entities extracted from a document.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document_entities(
    case_id: str,
    document_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> EntityListResponse:
    """
    Get entities extracted from a document.

    Returns all entities identified during document processing,
    including entity type, value, and confidence score.
    """
    return await service.get_document_entities(case_id, document_id)


@router.get(
    "/cases/{case_id}/documents/{document_id}/entities/{entity_id}/explain",
    response_model=EntityExplainResponse,
    summary="Explain entity extraction",
    description="Get explanation for why an entity was extracted.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Entity not found"},
    },
)
async def explain_entity(
    case_id: str,
    document_id: str,
    entity_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> EntityExplainResponse:
    """
    Get explanation for an entity extraction.

    Provides human-readable explanation of why the entity was
    extracted and the confidence level.
    """
    return await service.explain_entity(case_id, document_id, entity_id)


@router.get(
    "/cases/{case_id}/documents/{document_id}/summary",
    response_model=DocumentSummaryDetailResponse,
    summary="Get document summary",
    description="Retrieve AI-generated summary for a document.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document_summary(
    case_id: str,
    document_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> DocumentSummaryDetailResponse:
    """
    Get AI-generated summary for a document.

    Returns the document summary with key points and confidence.
    """
    return await service.get_document_summary(case_id, document_id)


@router.get(
    "/cases/{case_id}/documents/{document_id}/summary/explain",
    response_model=SummaryExplainResponse,
    summary="Explain summary generation",
    description="Get explanation of how document summary was generated.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document or summary not found"},
    },
)
async def explain_summary(
    case_id: str,
    document_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> SummaryExplainResponse:
    """
    Get explanation for document summary generation.

    Explains how the summary was created, including the
    sections used and AI model information.
    """
    return await service.explain_summary(case_id, document_id)


@router.post(
    "/cases/{case_id}/documents/{document_id}/reprocess",
    response_model=ReprocessResponse,
    summary="Reprocess document",
    description="Request reprocessing of a document.",
    responses={
        400: {"model": ErrorResponse, "description": "Document is currently processing"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def reprocess_document(
    case_id: str,
    document_id: str,
    request: ReprocessRequest = ReprocessRequest(),
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> ReprocessResponse:
    """
    Request reprocessing of a document.

    Queues the document for reprocessing. By default, all stages
    (classification, extraction, summarization) are rerun.
    """
    user_id = current_user.sub if current_user else "anonymous"
    return await service.reprocess_document(case_id, document_id, request, user_id)


# Case-level aggregation endpoints


@router.get(
    "/cases/{case_id}/entities",
    response_model=EntityAggregateResponse,
    summary="Get case entities aggregate",
    description="Get aggregated entity statistics for a case.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_case_entities_aggregate(
    case_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> EntityAggregateResponse:
    """
    Get aggregated entity statistics for a case.

    Returns total entity counts and breakdown by type across
    all documents in the case.
    """
    return await service.get_case_entities_aggregate(case_id)


@router.get(
    "/cases/{case_id}/summary",
    response_model=CaseSummaryDetailResponse,
    summary="Get case summary",
    description="Get comprehensive summary of all documents in a case.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_case_summary(
    case_id: str,
    current_user: CurrentUser = None,
    service: ProcessingService = Depends(get_processing_service),
) -> CaseSummaryDetailResponse:
    """
    Get comprehensive case summary.

    Returns overall case summary, individual document summaries,
    key findings, and risk indicators.
    """
    return await service.get_case_summary(case_id)
