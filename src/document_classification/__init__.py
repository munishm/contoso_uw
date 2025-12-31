"""Document classification module."""

from .utils.config import Config, ClassificationMethod
from .utils.factory import create_classifier
from .document_classifier import DirectDocumentClassifier


__all__ = [
    'Config',
    'ClassificationMethod', 
    'create_classifier',
    'DirectDocumentClassifier',
]
