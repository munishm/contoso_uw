"""
Case request and response models.

Pydantic models for case management API endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.api.models.enums import CaseProcessingStatus, CaseStatus


class CaseCreateRequest(BaseModel):
    """Request model for creating a new case."""

    client_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the client",
        examples=["John Smith"],
    )
    policy_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of insurance policy",
        examples=["Life Insurance - HNW"],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional case metadata",
    )


class CaseUpdateRequest(BaseModel):
    """Request model for updating an existing case."""

    client_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated client name",
    )
    policy_type: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated policy type",
    )
    status: Optional[CaseStatus] = Field(
        default=None,
        description="New case status (must follow valid transition rules)",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Updated metadata",
    )


class CaseSummaryResponse(BaseModel):
    """Summary response for case listings."""

    case_id: str = Field(..., description="Unique case identifier")
    client_name: str = Field(..., description="Client name")
    policy_type: str = Field(..., description="Policy type")
    status: CaseStatus = Field(..., description="Current case status")
    document_count: int = Field(default=0, description="Number of documents")
    documents_processed: int = Field(default=0, description="Documents with completed processing")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentSummaryInCase(BaseModel):
    """Minimal document summary for case detail response."""

    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")


class CaseDetailResponse(BaseModel):
    """Detailed response for a single case."""

    case_id: str = Field(..., description="Unique case identifier")
    client_name: str = Field(..., description="Client name")
    policy_type: str = Field(..., description="Policy type")
    submission_date: date = Field(..., description="Submission date")
    status: CaseStatus = Field(..., description="Current case status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who created the case")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Case metadata")
    main_document_blob_path: Optional[str] = Field(
        default=None, description="Blob storage path of the uploaded main document"
    )
    # Processing tracking fields
    processing_status: Optional[str] = Field(
        default="not_started",
        description="Overall processing status (not_started, extracting_documents, processing_documents, generating_case_summary, completed, failed)",
    )
    total_documents_expected: Optional[int] = Field(
        default=None, description="Total documents expected after extraction"
    )
    documents_processed_count: int = Field(
        default=0, description="Number of documents that have been processed"
    )
    processing_started_at: Optional[datetime] = Field(
        default=None, description="When processing started"
    )
    processing_completed_at: Optional[datetime] = Field(
        default=None, description="When processing completed"
    )
    processing_error: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )
    documents: list[DocumentSummaryInCase] = Field(
        default_factory=list, description="Documents attached to this case"
    )
    case_summary: Optional[str] = Field(
        default=None, description="AI-generated summary of all documents"
    )
    case_summary_updated_at: Optional[datetime] = Field(
        default=None, description="When case summary was last updated"
    )

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    """Paginated list of cases."""

    items: list[CaseSummaryResponse] = Field(..., description="List of cases")
    total: int = Field(..., ge=0, description="Total number of cases")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class StatusHistoryEntry(BaseModel):
    """Single entry in case status history."""

    previous_status: Optional[CaseStatus] = Field(
        default=None, description="Previous status"
    )
    new_status: CaseStatus = Field(..., description="New status")
    changed_by: str = Field(..., description="User who made the change")
    changed_at: datetime = Field(..., description="When the change occurred")
    reason: Optional[str] = Field(default=None, description="Reason for change")


class StatusHistoryResponse(BaseModel):
    """Status history for a case."""

    case_id: str = Field(..., description="Case identifier")
    history: list[StatusHistoryEntry] = Field(
        default_factory=list, description="List of status changes"
    )
