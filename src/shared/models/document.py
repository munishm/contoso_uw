"""Shared document data model."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class Document(BaseModel):
    """
    Represents a document in the underwriting system.
    
    Attributes:
        id: Unique document identifier
        name: Document filename
        content: Document content (binary or text)
        content_type: MIME type of the document
        size_bytes: Size of document in bytes
        created_at: Document creation timestamp
        metadata: Additional metadata about the document
        classification: Document type classification result
        confidence: Classification confidence score
    """
    
    id: str = Field(..., description="Unique document identifier")
    name: str = Field(..., description="Document filename")
    content: Optional[bytes] = Field(None, description="Document binary content")
    content_type: str = Field(..., description="MIME type (e.g., application/pdf)")
    size_bytes: int = Field(..., ge=0, description="Document size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Processing results
    classification: Optional[str] = Field(None, description="Document type classification")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Classification confidence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-12345",
                "name": "policy_application.pdf",
                "content_type": "application/pdf",
                "size_bytes": 102400,
                "created_at": "2025-12-15T10:30:00Z",
                "metadata": {
                    "source": "customer_portal",
                    "uploaded_by": "user@example.com"
                },
                "classification": "policy_application",
                "confidence": 0.95
            }
        }


class DocumentMetadata(BaseModel):
    """
    Extended metadata for a document.
    
    Attributes:
        document_id: Reference to parent document
        page_count: Number of pages
        language: Document language (ISO 639-1 code)
        has_images: Whether document contains images
        has_tables: Whether document contains tables
        processing_status: Current processing status
        error_message: Error message if processing failed
    """
    
    document_id: str = Field(..., description="Parent document ID")
    page_count: Optional[int] = Field(None, ge=1, description="Number of pages")
    language: Optional[str] = Field(None, description="Document language (e.g., 'en', 'fr')")
    has_images: bool = Field(default=False, description="Contains images")
    has_tables: bool = Field(default=False, description="Contains tables")
    processing_status: str = Field(default="pending", description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-12345",
                "page_count": 3,
                "language": "en",
                "has_images": True,
                "has_tables": False,
                "processing_status": "completed"
            }
        }
