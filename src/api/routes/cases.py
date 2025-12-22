"""
Case management API endpoints.

Provides CRUD operations for underwriting cases.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import (
    CurrentUser,
    get_case_repository,
    get_counter_repository,
    get_document_repository,
)
from src.api.models.case import (
    CaseCreateRequest,
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

router = APIRouter(prefix="/cases", tags=["Cases"])


def get_case_service(
    case_repo: CaseRepository = Depends(get_case_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    counter_repo: CounterRepository = Depends(get_counter_repository),
) -> CaseService:
    """Dependency to get case service instance."""
    return CaseService(case_repo, document_repo, counter_repo)


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List cases",
    description="Retrieve a paginated list of cases with optional filtering.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
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
    assigned_to: Optional[str] = Query(
        default=None, description="Filter by assigned underwriter email"
    ),
    include_deleted: bool = Query(
        default=False, description="Include soft-deleted cases"
    ),
    current_user: CurrentUser = None,
    service: CaseService = Depends(get_case_service),
) -> CaseListResponse:
    """
    List cases with pagination and filtering.

    - **page**: Page number starting from 1
    - **page_size**: Number of items per page (1-100)
    - **status**: Filter by case status
    - **client_name**: Search by client name (partial match)
    - **assigned_to**: Filter by assigned underwriter
    - **include_deleted**: Include soft-deleted cases (default: false)
    """
    return await service.list_cases(
        page=page,
        page_size=page_size,
        status=status_filter,
        client_name_search=client_name,
        assigned_to=assigned_to,
        include_deleted=include_deleted,
    )


@router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="Create a new underwriting case.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def create_case(
    request: CaseCreateRequest,
    current_user: CurrentUser = None,
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Create a new underwriting case.

    The case will be created with status SUBMITTED and a unique case ID
    in the format CASE-YYYYMM-NNNNNN.
    """
    user_id = current_user.user_id if current_user else "anonymous"
    return await service.create_case(request, user_id)


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get case details",
    description="Retrieve detailed information about a specific case.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_case(
    case_id: str,
    current_user: CurrentUser = None,
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    current_user: CurrentUser = None,
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
    user_id = current_user.user_id if current_user else "anonymous"
    return await service.update_case(case_id, request, user_id)


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete case",
    description="Soft delete a case (can be restored).",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def delete_case(
    case_id: str,
    current_user: CurrentUser = None,
    service: CaseService = Depends(get_case_service),
) -> None:
    """
    Soft delete a case.

    The case is marked as deleted but not permanently removed.
    It can be restored using the restore endpoint.
    """
    user_id = current_user.user_id if current_user else "anonymous"
    await service.delete_case(case_id, user_id)


@router.post(
    "/{case_id}/restore",
    response_model=CaseDetailResponse,
    summary="Restore deleted case",
    description="Restore a previously soft-deleted case.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
        409: {"model": ErrorResponse, "description": "Case is not deleted"},
    },
)
async def restore_case(
    case_id: str,
    current_user: CurrentUser = None,
    service: CaseService = Depends(get_case_service),
) -> CaseDetailResponse:
    """
    Restore a soft-deleted case.

    Returns 409 Conflict if the case is not currently deleted.
    """
    user_id = current_user.user_id if current_user else "anonymous"
    return await service.restore_case(case_id, user_id)


@router.get(
    "/{case_id}/status-history",
    response_model=StatusHistoryResponse,
    summary="Get case status history",
    description="Retrieve the complete status change history for a case.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_status_history(
    case_id: str,
    current_user: CurrentUser = None,
    service: CaseService = Depends(get_case_service),
) -> StatusHistoryResponse:
    """
    Get status change history for a case.

    Returns all status transitions with timestamps and user information.
    """
    return await service.get_status_history(case_id)
