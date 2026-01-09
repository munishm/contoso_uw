"""Extraction result models."""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .citation import Citation
from .enums import ExtractionStatus


class Alternative(BaseModel):
    """Alternative extracted value from a different model."""
    
    value: Any = Field(..., description="Alternative extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    model_source: str = Field(..., description="Model that produced this alternative")


class ExtractedField(BaseModel):
    """A single extracted field with metadata."""
    
    field_name: str = Field(..., description="Name of the extracted field")
    value: Any = Field(None, description="Extracted value (null if not found)")
    value_type: str = Field(..., description="Data type of the value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    citations: List[Citation] = Field(default_factory=list, description="Source locations")
    needs_review: bool = Field(default=False, description="Whether human review is required")
    review_reason: Optional[str] = Field(None, description="Why review is needed")
    alternatives: List[Alternative] = Field(default_factory=list, description="Conflicting values from other models")
    model_source: str = Field(..., description="Model that produced the primary value")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "field_name": "account_number",
                    "value": "1234567890",
                    "value_type": "string",
                    "confidence": 0.95,
                    "citations": [
                        {
                            "type": "bounding_box",
                            "page": 1,
                            "bbox": {"x": 0.12, "y": 0.08, "width": 0.15, "height": 0.02},
                            "text_snippet": "Account No: 1234567890"
                        }
                    ],
                    "needs_review": False,
                    "model_source": "azure_gpt4_vision"
                }
            ]
        }
    )


class ExtractionResult(BaseModel):
    """Complete extraction result for a document."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    document_id: str = Field(..., description="Reference to source document")
    document_type_id: UUID = Field(..., description="Document type used")
    version_id: UUID = Field(..., description="Schema version used")
    status: ExtractionStatus = Field(default=ExtractionStatus.PENDING, description="Extraction status")
    models_used: List[str] = Field(default_factory=list, description="Models executed")
    fields: List[ExtractedField] = Field(default_factory=list, description="Extracted fields")
    processing_duration_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    evaluation: Optional[dict[str, Any]] = Field(None, description="Evaluation results if evaluation was performed")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_id": "doc-123-456",
                    "document_type_id": "123e4567-e89b-12d3-a456-426614174000",
                    "version_id": "223e4567-e89b-12d3-a456-426614174000",
                    "status": "completed",
                    "models_used": ["azure_gpt4_vision"],
                    "fields": [],
                    "processing_duration_ms": 4523
                }
            ]
        }
    )
