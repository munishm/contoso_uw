"""Shared Pydantic models for the Contoso document processing system."""

from .classification import ClassificationResponse, PageClassification
from .document import *
from .entity import *

__all__ = [
    "ClassificationResponse",
    "PageClassification",
]