"""Factory for creating document classifiers."""

import logging
from typing import Any

from .config import Config, ClassificationMethod
from ..acu_classifier import ACUClassifier
from ..acu_llm_text_classifier import ACULLMTextClassifier
from ..llm_image_classifier import LLMImageClassifier


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
    
    if method == ClassificationMethod.ACU_ONLY:
        return ACUClassifier(config)
    elif method == ClassificationMethod.ACU_LLM_TEXT:
        return ACULLMTextClassifier(config)
    elif method == ClassificationMethod.LLM_IMAGE:
        return LLMImageClassifier(config)
    else:
        raise ValueError(f"Unknown classification method: {method}")
