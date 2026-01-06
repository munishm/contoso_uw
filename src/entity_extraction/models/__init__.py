"""Models package initialization."""

from .citation import BoundingBox, Citation
from .enums import CitationLevel, CombinationStrategy, ConflictResolution, ExtractionStatus, ModelType
from .extraction import Alternative, ExtractedField, ExtractionResult
from .schema import DocumentType, DocumentTypeVersion, ExtractionModel, ModelConfiguration

__all__ = [
    # Citation models
    "BoundingBox",
    "Citation",
    # Enums
    "CitationLevel",
    "CombinationStrategy",
    "ConflictResolution",
    "ExtractionStatus",
    "ModelType",
    # Extraction models
    "Alternative",
    "ExtractedField",
    "ExtractionResult",
    # Schema models
    "DocumentType",
    "DocumentTypeVersion",
    "ExtractionModel",
    "ModelConfiguration",
]
