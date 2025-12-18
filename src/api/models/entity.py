"""
Entity extraction models.

Pydantic models for entity extraction API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityBase(BaseModel):
    """Base entity model."""

    entity_type: str = Field(..., description="Type of extracted entity")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )


class EntityResponse(EntityBase):
    """Response model for a single entity."""

    entity_id: str = Field(..., description="Unique entity identifier")
    document_id: str = Field(..., description="Source document identifier")
    case_id: str = Field(..., description="Parent case identifier")
    source_location: Optional[str] = Field(
        default=None, description="Location in source document (page, coordinates)"
    )
    normalized_value: Optional[str] = Field(
        default=None, description="Normalized/standardized value"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional entity metadata"
    )
    created_at: datetime = Field(..., description="Extraction timestamp")

    model_config = ConfigDict(from_attributes=True)


class EntityListResponse(BaseModel):
    """Response containing list of entities for a document."""

    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Case identifier")
    entities: list[EntityResponse] = Field(
        default_factory=list, description="List of extracted entities"
    )
    total: int = Field(..., ge=0, description="Total number of entities")
    extraction_status: str = Field(..., description="Extraction status")
    extraction_completed_at: Optional[datetime] = Field(
        default=None, description="When extraction completed"
    )


class EntityExplainResponse(BaseModel):
    """Response containing explanation for an entity extraction."""

    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Type of entity")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    explanation: str = Field(
        ..., description="Human-readable explanation of why this entity was extracted"
    )
    source_text: Optional[str] = Field(
        default=None, description="Original text from which entity was extracted"
    )
    extraction_method: str = Field(
        ..., description="Method used for extraction (e.g., 'NER', 'regex', 'LLM')"
    )
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative values considered during extraction",
    )


class EntityTypeCount(BaseModel):
    """Count of entities by type."""

    entity_type: str = Field(..., description="Entity type")
    count: int = Field(..., ge=0, description="Number of entities of this type")


class EntityAggregateResponse(BaseModel):
    """Aggregated entity statistics for a case."""

    case_id: str = Field(..., description="Case identifier")
    total_entities: int = Field(..., ge=0, description="Total entities across all documents")
    documents_processed: int = Field(..., ge=0, description="Documents with completed extraction")
    documents_pending: int = Field(..., ge=0, description="Documents with pending extraction")
    by_type: list[EntityTypeCount] = Field(
        default_factory=list, description="Entity counts by type"
    )
