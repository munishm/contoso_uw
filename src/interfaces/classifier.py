"""Document classification interface and implementation."""

import logging
from typing import Protocol, Any, Dict, List
from abc import abstractmethod

# Import the classifier factory from document_classification module
from src.document_classification import create_classifier, Config


logger = logging.getLogger(__name__)


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


class DocumentClassifier:
    """
    Document classifier that implements IClassifier protocol.
    
    This is the main entry point for document classification,
    delegating to the appropriate classifier based on configuration.
    """
    
    def __init__(self):
        """Initialize the document classifier."""
        # Load configuration from environment
        self.config = Config()
        
        # Create the appropriate classifier based on config
        self._classifier = create_classifier(self.config)
        
        logger.info(
            f"DocumentClassifier initialized with method: "
            f"{self.config.CLASSIFICATION_METHOD.value}"
        )
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document into a predefined type.
        
        Args:
            document: Document object to classify. Must contain:
                - 'path' or 'file_path': Path to the document file
                - Other optional metadata
            
        Returns:
            Classification result containing:
            - document_type: Classified type
            - confidence: Confidence score (0.0 to 1.0)
            - alternatives: List of alternative classifications
            - segments: List of page-level segments (if available)
            - metadata: Additional metadata about classification
            
        Raises:
            ValueError: If document format is invalid
            FileNotFoundError: If document file not found
        """
        return self._classifier.classify(document)
    
    def get_document_types(self) -> List[str]:
        """
        Get list of possible document types.
        
        Returns:
            List of document type identifiers
        """
        return self._classifier.get_document_types()
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Set minimum confidence threshold for classification.
        
        Args:
            threshold: Minimum confidence (0.0 to 1.0)
        """
        self._classifier.set_confidence_threshold(threshold)
    
    @property
    def confidence_threshold(self) -> float:
        """
        Get current confidence threshold.
        
        Returns:
            Current confidence threshold
        """
        return self._classifier.confidence_threshold


# Factory function for backward compatibility
def get_classifier() -> DocumentClassifier:
    """
    Get a document classifier instance.
    
    Returns:
        DocumentClassifier instance
    """
    return DocumentClassifier()

