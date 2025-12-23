"""
Document management API endpoints.

Provides download, and management operations for case documents.
Note: Document upload is handled during case creation. Individual documents
are extracted from the main document by background processing.
"""

from fastapi import APIRouter, Depends, status

from src.api.dependencies import (
    get_case_repository,
    get_document_repository,
    get_entity_repository,
    get_queue_service,
    get_storage_service,
)
from src.api.models.common import ErrorResponse
from src.api.models.document import (
    DocumentDetailResponse,
    DocumentDownloadResponse,
    DocumentEntitiesResponse,
    DocumentListResponse,
    DocumentMetadataUpdateRequest,
)
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.services.document_service import DocumentService
from src.api.services.queue_service import QueueService
from src.api.services.storage_service import StorageService

router = APIRouter(tags=["Documents"])


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    case_repo: CaseRepository = Depends(get_case_repository),
    entity_repo: EntityRepository = Depends(get_entity_repository),
    storage_service: StorageService = Depends(get_storage_service),
    queue_service: QueueService = Depends(get_queue_service),
) -> DocumentService:
    """Dependency to get document service instance."""
    return DocumentService(
        document_repo, case_repo, entity_repo, storage_service, queue_service
    )


@router.get(
    "/cases/{case_id}/documents",
    response_model=DocumentListResponse,
    summary="List case documents",
    description="Retrieve all documents attached to a case. Documents are populated by background processing that extracts individual documents from the main document.",
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def list_documents(
    case_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """
    List all documents for a case.

    Returns document summaries including processing status.
    Documents are populated by background processing that extracts
    individual documents from the main document uploaded during case creation.
    """
    return await service.list_documents(case_id)


# Note: Document upload endpoint removed. Main document is now uploaded
# during case creation. Individual documents are extracted from the main
# document by background processing and stored under case_id folder.


@router.get(
    "/cases/{case_id}/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Retrieve detailed information about a specific document.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document(
    case_id: str,
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDetailResponse:
    """
    Get detailed information about a document.

    Returns document details including processing results, extracted text, and summary.
    """
    return await service.get_document(case_id, document_id)


@router.put(
    "/cases/{case_id}/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Update document metadata",
    description="Update document classification or custom metadata.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def update_document(
    case_id: str,
    document_id: str,
    request: DocumentMetadataUpdateRequest,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDetailResponse:
    """
    Update document metadata.

    Only classification and custom metadata can be updated.
    """
    user_id = "system"
    return await service.update_document(case_id, document_id, request, user_id)


@router.delete(
    "/cases/{case_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Permanently delete a document and its associated data.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def delete_document(
    case_id: str,
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> None:
    """
    Delete a document.

    This permanently removes the document from storage and database.
    Associated entities and summaries are also deleted.
    """
    user_id = "system"
    await service.delete_document(case_id, document_id, user_id)


@router.get(
    "/cases/{case_id}/documents/{document_id}/download",
    response_model=DocumentDownloadResponse,
    summary="Get download URL",
    description="Generate a temporary download URL for a document.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_download_url(
    case_id: str,
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDownloadResponse:
    """
    Get a pre-signed download URL for a document.

    The URL is valid for 1 hour.
    """
    return await service.get_download_url(case_id, document_id)
