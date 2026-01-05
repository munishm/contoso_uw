"""Enumeration types for schema-based document extraction."""

from enum import Enum


class ModelType(str, Enum):
    """Type of extraction model."""
    
    OCR = "ocr"
    LAYOUT = "layout"
    LLM = "llm"
    CUSTOM = "custom"
    VISION = "vision"


class CitationLevel(str, Enum):
    """Level of citation detail to include."""
    
    PAGE = "page"
    BOUNDING_BOX = "bounding_box"
    BOTH = "both"


class ExtractionStatus(str, Enum):
    """Status of an extraction operation."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class CombinationStrategy(str, Enum):
    """Strategy for combining results from multiple models."""
    
    SEQUENTIAL = "sequential"  # Model B processes Model A output
    PARALLEL = "parallel"      # Models run concurrently, results merged
    ENSEMBLE = "ensemble"      # Voting/averaging across models
    HYBRID = "hybrid"          # Custom combination logic


class ConflictResolution(str, Enum):
    """Strategy for resolving conflicting extraction values."""
    
    HIGHEST_CONFIDENCE = "highest_confidence"  # Use value with highest confidence
    FLAG_FOR_REVIEW = "flag_for_review"       # Return all values, mark for human review
    AVERAGE = "average"                       # Average numeric values
    VOTE = "vote"                             # Use most common value
