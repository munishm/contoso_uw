"""Factory for creating document classifiers."""

import logging
from typing import Any

from .config import Config, ClassificationMethod
from ..document_classifier import DirectDocumentClassifier


logger = logging.getLogger(__name__)


def create_classifier(config: Config = None) -> Any:
    """
    Create a document classifier based on configuration.
    
    Args:
        config: Configuration object (uses default if None)
        
    Returns:
        Classifier instance implementing IClassifier protocol
    """
    if config is None:
        config = Config()
    
    method = config.CLASSIFICATION_METHOD
    
    logger.info(f"Creating classifier with method: {method.value}")
    
    if method == ClassificationMethod.DIRECT_CLASSIFICATION:
        return DirectDocumentClassifier(config)
    else:
        raise ValueError(f"Unknown classification method: {method}")
