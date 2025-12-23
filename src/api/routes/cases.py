"""
Case management API endpoints.

Provides CRUD operations for underwriting cases.
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from src.api.dependencies import (
    get_case_repository,
    get_counter_repository,
    get_document_repository,
    get_storage_service,
)
from src.api.models.case import (
    CaseDetailResponse,
    CaseListResponse,
    CaseUpdateRequest,
    StatusHistoryResponse,
)
from src.api.models.common import ErrorResponse
from src.api.models.enums import CaseStatus
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.counter_repository import CounterRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.services.case_service import CaseService
from src.api.services.storage_service import StorageService

router = APIRouter(prefix="/cases", tags=["Cases"])


def get_case_service(
    case_repo: CaseRepository = Depends(get_case_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    counter_repo: CounterRepository = Depends(get_counter_repository),
    storage_service: StorageService = Depends(get_storage_service),
) -> CaseService:
    """Dependency to get case service instance."""
    return CaseService(case_repo, document_repo, counter_repo, storage_service)


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List cases",
    description="Retrieve a paginated list of cases with optional filtering.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
    },
)
async def list_cases(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    ),
    status_filter: Optional[CaseStatus] = Query(
        default=None, alias="status", description="Filter by case status"
    ),
    client_name: Optional[str] = Query(
        default=None, description="Search by client name (partial match)"
    ),
    include_deleted: bool = Query(
        default=False, description="Include soft-deleted cases"
    ),
    service: CaseService = Depends(get_case_service),
) -> CaseListResponse:
    """
    List cases with pagination and filtering.

    - **page**: Page number starting from 1
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by case status
    - **client_name**: Search by client name (partial match)
    - **include_deleted**: Include soft-deleted cases (default: false)
    """
    return await service.list_cases(
        page=page,
        page_size=page_size,
        status=status_filter,
        client_name_search=client_name,
        include_deleted=include_deleted,
    )


@router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="Create a new underwriting case with an optional main document upload.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
    },
)
async def create_case(
    client_name: str = Form(..., description="Name of the client"),
    policy_type: str = Form(..., description="Type of insurance policy"),
    submission_date: date = Form(..., description="Date the case was submitted"),
    metadata: Optional[str] = Form(
        default=None, description="Additional case metadata as JSON string"
    ),
    main_document: Optional[UploadFile] = File(
        default=None, description="Main document file to upload (PDF, DOCX, etc.)"
    ),
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Create a new underwriting case.

    The case will be created with status DRAFT and a unique case ID
    in the format CASE-YYYYMM-NNNNNN.

    Optionally upload a main document during case creation. The main document
    will be stored in blob storage. Documents array will remain empty until
    the main document is processed and individual documents are extracted.
    """
    import json
    import logging

    logger = logging.getLogger(__name__)
    user_id = "system"

    # Parse metadata if provided (skip empty strings and common placeholder values)
    parsed_metadata: dict[str, Any] = {}
    # Skip common placeholder values from Swagger UI or empty values
    placeholder_values = {"string", "null", "none", "undefined", ""}
    if metadata and metadata.strip().lower() not in placeholder_values:
        try:
            parsed_metadata = json.loads(metadata)
            if not isinstance(parsed_metadata, dict):
                from src.api.middleware.error_handler import BadRequestError
                raise BadRequestError("Metadata must be a JSON object (e.g., '{\"key\": \"value\"}')")
        except json.JSONDecodeError as e:
            from src.api.middleware.error_handler import BadRequestError
            logger.warning(f"Invalid metadata JSON: {metadata[:100]}... Error: {e}")
            raise BadRequestError(
                f"Invalid JSON in metadata field. Expected JSON object like '{{\"key\": \"value\"}}'. "
                f"Error: {e.msg} at position {e.pos}"
            )

    # Read file content if provided
    file_content: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    if main_document and main_document.filename:
        filename = main_document.filename
        content_type = main_document.content_type or "application/octet-stream"
        file_content = await main_document.read()

    return await service.create_case(
        client_name=client_name,
        policy_type=policy_type,
        submission_date=submission_date,
        metadata=parsed_metadata,
        user_id=user_id,
        main_document_content=file_content,
        main_document_filename=filename,
        main_document_content_type=content_type,
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get case details",
    description="Retrieve detailed information about a specific case.",
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Get detailed information about a case.

    Returns case details including attached documents and metadata.
    """
    return await service.get_case(case_id)


@router.put(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Update case",
    description="Update an existing case's information.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        404: {"model": ErrorResponse, "description": "Case not found"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Update an existing case.

    Only provided fields will be updated. Status changes must follow
    valid transition rules:
    - SUBMITTED → DOCUMENTS_PENDING, IN_REVIEW
    - DOCUMENTS_PENDING → IN_REVIEW, SUBMITTED
    - IN_REVIEW → APPROVED, REJECTED, DOCUMENTS_PENDING
    - APPROVED → CLOSED
    - REJECTED → CLOSED, IN_REVIEW
    """
    user_id = "system"
    return await service.update_case(case_id, request, user_id)


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete case",
    description="Soft delete a case (can be restored).",
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def delete_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> None:
    """
    Soft delete a case.

    The case is marked as deleted but not permanently removed.
    It can be restored using the restore endpoint.
    """
    user_id = "system"
    await service.delete_case(case_id, user_id)


@router.post(
    "/{case_id}/restore",
    response_model=CaseDetailResponse,
    summary="Restore deleted case",
    description="Restore a previously soft-deleted case.",
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
        409: {"model": ErrorResponse, "description": "Case is not deleted"},
    },
)
async def restore_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Restore a soft-deleted case.

    Returns 409 Conflict if the case is not currently deleted.
    """
    user_id = "system"
    return await service.restore_case(case_id, user_id)


@router.get(
    "/{case_id}/status-history",
    response_model=StatusHistoryResponse,
    summary="Get case status history",
    description="Retrieve the complete status change history for a case.",
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_status_history(
    case_id: str,
    service: CaseService = Depends(get_case_service),
) -> StatusHistoryResponse:
    """
    Get status change history for a case.

    Returns all status transitions with timestamps and user information.
    """
    return await service.get_status_history(case_id)
