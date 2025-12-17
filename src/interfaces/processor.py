"""Base document processor interface."""

from typing import Protocol, Any, Optional
from abc import abstractmethod


class IDocumentProcessor(Protocol):
    """
    Base interface for all document processing components.
    
    All components that process documents must implement this interface
    to ensure consistent behavior and enable plug-and-play architecture.
    """
    
    @abstractmethod
    def process(self, document: dict[str, Any]) -> dict[str, Any]:
        """
        Process a document and return results.
        
        Args:
            document: Document object containing id, name, content, etc.
            
        Returns:
            Processing results dictionary
            
        Raises:
            ProcessingError: If processing fails
        """
        ...
    
    @abstractmethod
    def validate_input(self, document: dict[str, Any]) -> bool:
        """
        Validate that document meets processing requirements.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid for processing
        """
        ...
    
    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """
        Get list of supported document types.
        
        Returns:
            List of MIME types this processor supports
        """
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get processor name.
        
        Returns:
            Human-readable processor name
        """
        ...
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get processor version.
        
        Returns:
            Semantic version string (e.g., "1.0.0")
        """
        ...
