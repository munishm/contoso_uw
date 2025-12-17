"""Document summarization interface."""

from typing import Protocol, Any, Optional
from abc import abstractmethod


class ISummarizer(Protocol):
    """
    Interface for document summarization components.
    
    Implementations must generate concise summaries of documents
    with configurable length and detail level.
    """
    
    @abstractmethod
    def summarize(
        self, 
        document: dict[str, Any], 
        max_length: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Generate a summary of the document.
        
        Args:
            document: Document object to summarize
            max_length: Maximum summary length in characters (optional)
            
        Returns:
            Summary result containing:
            - text: Summary text
            - key_points: List of key points
            - word_count: Number of words in summary
            - compression_ratio: Original to summary length ratio
            
        Raises:
            SummarizationError: If summarization fails
        """
        ...
    
    @abstractmethod
    def extract_key_points(
        self, 
        document: dict[str, Any], 
        num_points: int = 5
    ) -> list[str]:
        """
        Extract key points from document.
        
        Args:
            document: Document to extract key points from
            num_points: Number of key points to extract
            
        Returns:
            List of key point strings
        """
        ...
    
    @abstractmethod
    def get_summary_types(self) -> list[str]:
        """
        Get available summary types.
        
        Returns:
            List of summary type identifiers (e.g., 'extractive', 'abstractive')
        """
        ...
    
    @abstractmethod
    def set_summary_type(self, summary_type: str) -> None:
        """
        Set the type of summary to generate.
        
        Args:
            summary_type: Summary type identifier
            
        Raises:
            ValueError: If summary type is not supported
        """
        ...
    
    @property
    @abstractmethod
    def default_max_length(self) -> int:
        """
        Get default maximum summary length.
        
        Returns:
            Default max length in characters
        """
        ...
