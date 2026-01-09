"""Document Summarization Package.

This package provides modular tools for generating natural language summaries
from extracted document entities using LLM-based approaches.
"""

from .summarization_service import SummarizationService
from .summarizers.base_summarizer import BaseSummarizer, SummaryResult
from .summarizers.llm_summarizer import LLMSummarizer
from .utils.entity_loader import EntityLoader
from .utils.prompt_builder import PromptBuilder
from .utils.llm_client import LLMClient

__all__ = [
    "SummarizationService",
    "BaseSummarizer",
    "SummaryResult",
    "LLMSummarizer",
    "EntityLoader",
    "PromptBuilder",
    "LLMClient",
]
