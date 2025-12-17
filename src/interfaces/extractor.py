"""Entity extraction interface."""

from typing import Protocol, Any
from abc import abstractmethod


class IEntityExtractor(Protocol):
    """
    Interface for entity extraction components.
    
    Implementations must extract structured entities from documents
    and provide confidence scores for each extraction.
    """
    
    @abstractmethod
    def extract(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract entities from a document.
        
        Args:
            document: Document object to extract entities from
            
        Returns:
            List of extracted entities, each containing:
            - type: Entity type (e.g., 'policy_number', 'person_name')
            - value: Extracted value
            - confidence: Confidence score (0.0 to 1.0)
            - start: Start position in text
            - end: End position in text
            - metadata: Additional metadata
            
        Raises:
            ExtractionError: If extraction fails
        """
        ...
    
    @abstractmethod
    def get_entity_types(self) -> list[str]:
        """
        Get list of entity types this extractor supports.
        
        Returns:
            List of entity type identifiers
        """
        ...
    
    @abstractmethod
    def extract_by_type(
        self, 
        document: dict[str, Any], 
        entity_type: str
    ) -> list[dict[str, Any]]:
        """
        Extract only entities of a specific type.
        
        Args:
            document: Document to extract from
            entity_type: Specific entity type to extract
            
        Returns:
            List of entities of the specified type
        """
        ...
    
    @abstractmethod
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Set minimum confidence threshold for extraction.
        
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
