"""Document classification interface."""

from typing import Protocol, Any
from abc import abstractmethod


class IClassifier(Protocol):
    """
    Interface for document classification components.
    
    Implementations must classify documents into predefined types
    and provide confidence scores.
    """
    
    @abstractmethod
    def classify(self, document: dict[str, Any]) -> dict[str, Any]:
        """
        Classify a document into a predefined type.
        
        Args:
            document: Document object to classify
            
        Returns:
            Classification result containing:
            - document_type: Classified type
            - confidence: Confidence score (0.0 to 1.0)
            - alternatives: List of alternative classifications
            
        Raises:
            ClassificationError: If classification fails
        """
        ...
    
    @abstractmethod
    def get_document_types(self) -> list[str]:
        """
        Get list of possible document types.
        
        Returns:
            List of document type identifiers
        """
        ...
    
    @abstractmethod
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Set minimum confidence threshold for classification.
        
        Args:
            threshold: Minimum confidence (0.0 to 1.0)
        """
        ...
    
    @property
    @abstractmethod
    def confidence_threshold(self) -> float:
        """
        Get current confidence threshold.
        
        Returns:
            Current confidence threshold
        """
        ...
