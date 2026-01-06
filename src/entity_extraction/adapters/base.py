"""Base adapter interface for extraction models."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models import Citation, DocumentTypeVersion


class ExtractionModelAdapter(ABC):
    """Base interface for all extraction model adapters."""
    
    @abstractmethod
    async def extract(
        self,
        document_content: bytes,
        document_type: str,
        schema_version: DocumentTypeVersion,
        field_names: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data from a document.
        
        Args:
            document_content: Raw document bytes (PDF, image, etc.)
            document_type: Type of document being processed
            schema_version: Schema version defining extraction rules
            field_names: Specific fields to extract (or ["*"] for all)
        
        Returns:
            Dictionary mapping field names to extraction results with structure:
            {
                "field_name": {
                    "value": extracted_value,
                    "confidence": float (0.0-1.0),
                    "citations": List[Citation]
                }
            }
        """
        pass
    
    @abstractmethod
    def get_confidence(self, extraction_result: Dict[str, Any], field_name: str) -> float:
        """
        Get confidence score for a specific extracted field.
        
        Args:
            extraction_result: Result from extract() method
            field_name: Name of the field to get confidence for
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def supports_document_type(self, document_type: str) -> bool:
        """
        Check if this adapter can handle the given document type.
        
        Args:
            document_type: Type of document to check
        
        Returns:
            True if this adapter supports the document type
        """
        pass
    
    @abstractmethod
    def get_model_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this extraction model.
        
        Returns:
            Dictionary with model information:
            {
                "name": str,
                "version": str,
                "type": str,
                "capabilities": List[str]
            }
        """
        pass
