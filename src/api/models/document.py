"""
Document request and response models.

Pydantic models for document management API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.api.models.enums import DocumentType, ProcessingStatus


class DocumentUploadResponse(BaseModel):
    """Response after successful document upload."""

    document_id: str = Field(..., description="Unique document identifier")
    case_id: str = Field(..., description="Parent case identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current processing status",
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    created_by: str = Field(..., description="User who uploaded the document")

    model_config = ConfigDict(from_attributes=True)


class DocumentMetadataUpdateRequest(BaseModel):
    """Request model for updating document metadata."""

    classification: Optional[DocumentType] = Field(
        default=None, description="Document classification type"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Custom metadata"
    )


class DocumentSummaryResponse(BaseModel):
    """Summary response for document listings."""

    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Parent case identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    classification: Optional[DocumentType] = Field(
        default=None, description="Document classification"
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    """Detailed response for a single document."""

    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Parent case identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    blob_path: str = Field(..., description="Storage path")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    classification: Optional[DocumentType] = Field(
        default=None, description="Document classification"
    )
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Classification confidence"
    )
    extracted_text: Optional[str] = Field(
        default=None, description="OCR extracted text"
    )
    summary: Optional[str] = Field(
        default=None, description="AI-generated summary"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata"
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who uploaded")
    processing_started_at: Optional[datetime] = Field(
        default=None, description="When processing started"
    )
    processing_completed_at: Optional[datetime] = Field(
        default=None, description="When processing completed"
    )
    processing_error: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: list[DocumentSummaryResponse] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total number of documents")
    case_id: str = Field(..., description="Parent case identifier")


class DocumentDownloadResponse(BaseModel):
    """Response containing download URL."""

    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    download_url: str = Field(..., description="Pre-signed URL for download")
    expires_at: datetime = Field(..., description="URL expiration time")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size")


class ExtractedEntity(BaseModel):
    """Entity extracted from a document."""

    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Type of entity")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source_location: Optional[str] = Field(
        default=None, description="Location in document"
    )


class DocumentEntitiesResponse(BaseModel):
    """Response containing extracted entities for a document."""

    document_id: str = Field(..., description="Document identifier")
    entities: list[ExtractedEntity] = Field(
        default_factory=list, description="Extracted entities"
    )
    extraction_completed_at: Optional[datetime] = Field(
        default=None, description="When extraction completed"
    )
