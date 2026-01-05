"""Adapters package initialization."""

from .base import ExtractionModelAdapter
from .azure_openai_vision import AzureOpenAIVisionAdapter

__all__ = [
    "ExtractionModelAdapter",
    "AzureOpenAIVisionAdapter",
]
