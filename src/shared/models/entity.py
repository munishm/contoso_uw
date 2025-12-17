"""Shared entity data model."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    Represents an extracted entity from a document.
    
    Attributes:
        type: Entity type (e.g., 'policy_number', 'person_name', 'date')
        value: Extracted entity value
        confidence: Extraction confidence score
        start: Start position in source text
        end: End position in source text
        metadata: Additional metadata about the entity
        normalized_value: Normalized/standardized value
    """
    
    type: str = Field(..., description="Entity type")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    start: int = Field(..., ge=0, description="Start position in text")
    end: int = Field(..., ge=0, description="End position in text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    normalized_value: Optional[str] = Field(None, description="Normalized value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "policy_number",
                "value": "POL-12345",
                "confidence": 0.95,
                "start": 0,
                "end": 9,
                "metadata": {
                    "page": 1,
                    "section": "header"
                },
                "normalized_value": "POL-12345"
            }
        }


class EntityRelationship(BaseModel):
    """
    Represents a relationship between two entities.
    
    Attributes:
        source_entity_id: ID of source entity
        target_entity_id: ID of target entity
        relationship_type: Type of relationship (e.g., 'issued_to', 'dated_on')
        confidence: Confidence score for the relationship
        metadata: Additional metadata
    """
    
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Relationship type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_entity_id": "entity-001",
                "target_entity_id": "entity-002",
                "relationship_type": "issued_to",
                "confidence": 0.90,
                "metadata": {
                    "context": "Policy POL-12345 issued to John Doe"
                }
            }
        }


class EntityCollection(BaseModel):
    """
    Collection of entities extracted from a document.
    
    Attributes:
        document_id: Reference to source document
        entities: List of extracted entities
        relationships: List of entity relationships
        extraction_timestamp: When extraction was performed
    """
    
    document_id: str = Field(..., description="Source document ID")
    entities: list[Entity] = Field(default_factory=list, description="Extracted entities")
    relationships: list[EntityRelationship] = Field(default_factory=list, description="Entity relationships")
    extraction_timestamp: str = Field(..., description="Extraction timestamp (ISO 8601)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-12345",
                "entities": [
                    {
                        "type": "policy_number",
                        "value": "POL-12345",
                        "confidence": 0.95,
                        "start": 0,
                        "end": 9
                    }
                ],
                "relationships": [],
                "extraction_timestamp": "2025-12-15T10:30:00Z"
            }
        }
