"""Entity extraction module for Contoso Bank underwriting automation.

This module provides schema-based document extraction capabilities with:
- Configurable document type schemas with versioning
- Multi-model extraction support (GPT-4 Vision, Azure Document Intelligence)
- Citation tracking at page or bounding-box level
- Human-in-the-loop review for low-confidence extractions
"""

from .config import get_config, get_cosmos_client
from .models import (
    BoundingBox,
    Citation,
    CitationLevel,
    DocumentType,
    DocumentTypeVersion,
    ExtractedField,
    ExtractionModel,
    ExtractionResult,
    ExtractionStatus,
    ModelType,
)
from .services import (
    SchemaService,
    SchemaExtractionService,
    extract_document_for_workflow,
    get_extraction_status,
)

__version__ = "0.2.0"

__all__ = [
    # Configuration
    "get_config",
    "get_cosmos_client",
    # Models
    "BoundingBox",
    "Citation",
    "CitationLevel",
    "DocumentType",
    "DocumentTypeVersion",
    "ExtractedField",
    "ExtractionModel",
    "ExtractionResult",
    "ExtractionStatus",
    "ModelType",
    # Services
    "SchemaService",
    "SchemaExtractionService",
    # Orchestration Interface
    "extract_document_for_workflow",
    "get_extraction_status",
]
