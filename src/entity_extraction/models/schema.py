"""Schema models for document types and versions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .enums import CitationLevel, CombinationStrategy, ConflictResolution, ModelType


class DocumentType(BaseModel):
    """Represents a category of documents with specific structure patterns."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., min_length=3, max_length=100, description="Human-readable name (e.g., 'Bank Statement')")
    description: Optional[str] = Field(None, max_length=500, description="Purpose and usage notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(..., description="User who created the type")
    is_active: bool = Field(default=True, description="Soft delete flag")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Bank Statement",
                    "description": "Monthly bank account statements from major financial institutions",
                    "created_by": "admin@hsbc.com"
                }
            ]
        }
    )


class ModelConfiguration(BaseModel):
    """Configuration for a single model in the extraction pipeline."""
    
    model_id: UUID = Field(..., description="Reference to ExtractionModel")
    order: int = Field(..., ge=1, description="Execution order in pipeline")
    strategy: str = Field(..., pattern="^(primary|fallback|parallel)$", description="Model usage strategy")
    fields: List[str] = Field(..., description="Fields this model should extract ('*' for all)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model_id": "123e4567-e89b-12d3-a456-426614174000",
                    "order": 1,
                    "strategy": "primary",
                    "fields": ["*"]
                }
            ]
        }
    )


class DocumentTypeVersion(BaseModel):
    """Specific version of a document type with extraction configuration."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    document_type_id: UUID = Field(..., description="Parent document type")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$|^\d{4}$", description="Version string (semver or year)")
    input_schema: Dict[str, Any] = Field(..., description="Fields to extract (JSON Schema)")
    output_schema: Dict[str, Any] = Field(..., description="Output structure definition (JSON Schema)")
    extraction_config: Dict[str, Any] = Field(..., description="Extraction model configuration")
    citation_level: CitationLevel = Field(default=CitationLevel.BOUNDING_BOX, description="Citation detail level")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Fallback trigger threshold")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(..., description="User who created the version")
    is_active: bool = Field(default=True, description="Whether this version is usable")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_type_id": "123e4567-e89b-12d3-a456-426614174000",
                    "version": "2.0.0",
                    "input_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "account_number": {"type": "string"}
                        }
                    },
                    "output_schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "account_number": {"type": "object"}
                        }
                    },
                    "extraction_config": {
                        "models": [],
                        "combination_strategy": "sequential",
                        "conflict_resolution": "flag_for_review"
                    },
                    "citation_level": "bounding_box",
                    "confidence_threshold": 0.7,
                    "created_by": "admin@hsbc.com"
                }
            ]
        }
    )


class ExtractionModel(BaseModel):
    """Represents a model or algorithm used for extraction."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., min_length=3, max_length=100, description="Model identifier")
    type: ModelType = Field(..., description="Type of extraction model")
    endpoint: Optional[str] = Field(None, description="API endpoint or resource URI")
    version: str = Field(..., description="Model version")
    capabilities: List[str] = Field(default_factory=list, description="Supported capabilities")
    is_active: bool = Field(default=True, description="Whether model is available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "azure_gpt4_vision",
                    "type": "vision",
                    "endpoint": "https://hsbc-openai.openai.azure.com/",
                    "version": "gpt-4-vision-preview",
                    "capabilities": ["ocr", "structured_extraction", "spatial_understanding"]
                }
            ]
        }
    )
