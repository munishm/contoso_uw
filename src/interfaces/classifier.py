"""Document classification interface and implementation."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Protocol, Any, Dict, List, Optional
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
    
    Supports both local file paths and Azure Blob Storage paths.
    """
    
    def __init__(self, storage_service: Optional[Any] = None):
        """
        Initialize the document classifier.
        
        Args:
            storage_service: Optional StorageService for blob storage access.
                           If provided, enables classify_from_blob() method.
        """
        # Load configuration from environment
        self.config = Config()
        
        # Create the appropriate classifier based on config
        self._classifier = create_classifier(self.config)
        
        # Store storage service for blob operations
        self._storage_service = storage_service
        
        logger.info(
            f"DocumentClassifier initialized with method: "
            f"{self.config.CLASSIFICATION_METHOD.value}"
        )
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document into a predefined type.
        
        Args:
            document: Document object to classify. Must contain:
                - 'path' or 'file_path': Path to the document file (local path)
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
    
    async def classify_from_blob(
        self, 
        blob_path: str,
        cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Classify a document from Azure Blob Storage.
        
        Downloads the document to a temporary file, runs classification,
        and optionally cleans up the temp file.
        
        Args:
            blob_path: Path to the document in blob storage
            cleanup: Whether to delete temp file after classification (default: True)
            
        Returns:
            Classification result containing:
            - document_type: Classified type
            - confidence: Confidence score (0.0 to 1.0)
            - alternatives: List of alternative classifications
            - segments: List of page-level segments (if available)
            - metadata: Additional metadata about classification
            
        Raises:
            RuntimeError: If storage service not configured
            ValueError: If blob download fails
        """
        if not self._storage_service:
            raise RuntimeError(
                "Storage service not configured. Pass storage_service to constructor "
                "or use classify() with a local file path."
            )
        
        # Download to temp file
        temp_path = await self._download_blob_to_temp(blob_path)
        
        try:
            # Run classification in executor (CPU-bound)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._classify_file,
                temp_path,
            )
            
            # Add blob path to metadata
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['blob_path'] = blob_path
            result['metadata']['source'] = 'blob_storage'
            
            return result
            
        finally:
            if cleanup and os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
    
    def classify_from_bytes(
        self,
        content: bytes,
        filename: str = "document.pdf",
        cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Classify a document from raw bytes.
        
        Writes content to a temporary file and runs classification.
        
        Args:
            content: Document content as bytes
            filename: Original filename (used for extension detection)
            cleanup: Whether to delete temp file after classification (default: True)
            
        Returns:
            Classification result
        """
        # Get extension from filename
        extension = Path(filename).suffix or ".pdf"
        
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=extension)
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        
        try:
            result = self._classify_file(temp_path)
            
            # Add source info to metadata
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['original_filename'] = filename
            result['metadata']['source'] = 'bytes'
            
            return result
            
        finally:
            if cleanup and os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
    
    def _classify_file(self, file_path: str) -> Dict[str, Any]:
        """
        Internal method to classify a local file.
        
        Args:
            file_path: Path to local file
            
        Returns:
            Classification result
        """
        document = {"path": file_path}
        return self._classifier.classify(document)
    
    async def _download_blob_to_temp(self, blob_path: str) -> str:
        """
        Download a document from blob storage to a temporary file.
        
        Args:
            blob_path: Blob storage path
            
        Returns:
            Path to the temporary file
        """
        # Get file extension from blob path
        extension = Path(blob_path).suffix or ".pdf"
        
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=extension)
        os.close(fd)
        
        try:
            # Download content from blob
            blob_client = self._storage_service.container.get_blob_client(blob_path)
            download_stream = await blob_client.download_blob()
            content = await download_stream.readall()
            
            # Write to temp file
            with open(temp_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Downloaded {blob_path} to {temp_path} ({len(content)} bytes)")
            return temp_path
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise RuntimeError(f"Failed to download blob {blob_path}: {e}") from e
    
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
def get_classifier(storage_service: Optional[Any] = None) -> DocumentClassifier:
    """
    Get a document classifier instance.
    
    Args:
        storage_service: Optional StorageService for blob storage access.
                        If provided, enables classify_from_blob() method.
    
    Returns:
        DocumentClassifier instance
    """
    return DocumentClassifier(storage_service=storage_service)

