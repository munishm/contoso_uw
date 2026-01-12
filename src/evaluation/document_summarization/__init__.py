"""Document Summarization Evaluation Package.

This package provides tools for evaluating the quality of generated summaries
from document entity extraction using various metrics and LLM-based approaches.
"""

from .evaluation_service import SummaryEvaluationService, EvaluatorType
from .evaluators import (
    BaseEvaluator,
    EvaluationResult,
    EntityCoverageEvaluator,
    GroundednessEvaluator,
    SemanticFidelityEvaluator,
)
from .utils import (
    calculate_average_score,
    format_evaluation_report,
    save_evaluation_results,
    split_summary_into_sentences,
    extract_numeric_values,
    normalize_text,
)

__all__ = [
    "SummaryEvaluationService",
    "EvaluatorType",
    "BaseEvaluator",
    "EvaluationResult",
    "EntityCoverageEvaluator",
    "GroundednessEvaluator",
    "SemanticFidelityEvaluator",
    "calculate_average_score",
    "format_evaluation_report",
    "save_evaluation_results",
    "split_summary_into_sentences",
    "extract_numeric_values",
    "normalize_text",
]
