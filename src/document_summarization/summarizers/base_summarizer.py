from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from pydantic import BaseModel


class SummaryResult(BaseModel):
    """Base summary result model."""
    
    summary: str
    metadata: Dict[str, Any] = {}
    success: bool = True
    error_message: Optional[str] = None


class BaseSummarizer(ABC):
    """Abstract base class for document summarizers."""
    
    @abstractmethod
    def summarize(
        self,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> SummaryResult:
        """
        Generate a summary from extracted entities.
        
        Args:
            entities: Dictionary of entity names and values
            context: Optional additional context
            **kwargs: Additional summarizer-specific parameters
            
        Returns:
            SummaryResult with summary text and metadata
        """
        pass
    
    @abstractmethod
    def validate_entities(self, entities: Dict[str, str]) -> bool:
        """
        Validate that entities are in the correct format.
        
        Args:
            entities: Dictionary of entity names and values
            
        Returns:
            True if valid, False otherwise
        """
        pass
