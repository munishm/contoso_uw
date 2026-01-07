"""
Document request and response models.

Pydantic models for document management API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.api.models.enums import DocumentType, ProcessingStatus


# =============================================================================
# Extraction Models (embedded in documents)
# =============================================================================

class ExtractionBoundingBox(BaseModel):
    """Bounding box coordinates using normalized values (0.0-1.0)."""
    
    x: float = Field(..., ge=0.0, le=1.0, description="X coordinate (left) as percentage of page width")
    y: float = Field(..., ge=0.0, le=1.0, description="Y coordinate (top) as percentage of page height")
    width: float = Field(..., ge=0.0, le=1.0, description="Width as percentage of page width")
    height: float = Field(..., ge=0.0, le=1.0, description="Height as percentage of page height")


class ExtractionCitation(BaseModel):
    """Source location citation for an extracted field value."""
    
    type: str = Field(..., description="Citation type (page, bounding_box)")
    page: int = Field(..., ge=1, description="Page number (1-indexed)")
    bbox: Optional[ExtractionBoundingBox] = Field(None, description="Bounding box coordinates")
    text_snippet: Optional[str] = Field(None, description="Text excerpt from citation location")


class ExtractionFieldAlternative(BaseModel):
    """Alternative extracted value from a different model."""
    
    value: Any = Field(..., description="Alternative extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    model_source: str = Field(..., description="Model that produced this alternative")


class ExtractedFieldResult(BaseModel):
    """A single extracted field with metadata."""
    
    field_name: str = Field(..., description="Name of the extracted field")
    value: Any = Field(None, description="Extracted value (null if not found)")
    value_type: str = Field(default="str", description="Data type of the value")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    citations: List[ExtractionCitation] = Field(default_factory=list, description="Source locations")
    needs_review: bool = Field(default=False, description="Whether human review is required")
    review_reason: Optional[str] = Field(None, description="Why review is needed")
    alternatives: List[ExtractionFieldAlternative] = Field(default_factory=list, description="Conflicting values from other models")
    model_source: Optional[str] = Field(None, description="Model that produced the primary value")


class DocumentExtractionResult(BaseModel):
    """Extraction results embedded in a document."""
    
    extraction_id: Optional[str] = Field(None, description="Unique extraction identifier")
    document_type_id: Optional[str] = Field(None, description="Document type used for extraction")
    version_id: Optional[str] = Field(None, description="Schema version used")
    status: str = Field(default="pending", description="Extraction status (pending, in_progress, completed, failed, review_required)")
    models_used: List[str] = Field(default_factory=list, description="Models executed")
    fields: List[ExtractedFieldResult] = Field(default_factory=list, description="Extracted fields")
    processing_duration_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    needs_review: bool = Field(default=False, description="Whether any field needs human review")
    extraction_started_at: Optional[datetime] = Field(None, description="When extraction started")
    extraction_completed_at: Optional[datetime] = Field(None, description="When extraction completed")


# =============================================================================
# Document API Models
# =============================================================================


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
    classification: Optional[str] = Field(
        default=None, description="Document classification (from ACU classifier)"
    )
    has_extraction: bool = Field(
        default=False, description="Whether extraction results are available"
    )
    extraction_status: Optional[str] = Field(
        default=None, description="Extraction status (completed, skipped, error, etc.)"
    )
    extraction_needs_review: bool = Field(
        default=False, description="Whether extraction needs human review"
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
    classification: Optional[str] = Field(
        default=None, description="Document classification (from ACU classifier)"
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
    # Extraction results embedded in document
    extraction: Optional[DocumentExtractionResult] = Field(
        default=None, description="Entity extraction results"
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


class FieldColorInfo(BaseModel):
    """Color information for a single field."""
    
    color: str = Field(..., description="RGB color string (e.g., 'rgb(255, 0, 0)')")
    hex: str = Field(..., description="Hex color code (e.g., '#ff0000')")
    needs_review: bool = Field(default=False, description="Whether field needs review")


class FieldColorsResponse(BaseModel):
    """Response containing field color mappings for UI legend."""
    
    document_id: str = Field(..., description="Document identifier")
    fields: dict[str, FieldColorInfo] = Field(
        default_factory=dict, 
        description="Mapping of field names to their color info"
    )


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
