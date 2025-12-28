"""Document classification module."""

from .utils.config import Config, ClassificationMethod
from .utils.factory import create_classifier
from .acu_classifier import ACUClassifier
from .acu_llm_text_classifier import ACULLMTextClassifier
from .llm_image_classifier import LLMImageClassifier

# Optional import - handle gracefully if not available
try:
    from .di_page_llm_classifier import DIPageLLMClassifier
    _DI_PAGE_LLM_AVAILABLE = True
except ImportError:
    DIPageLLMClassifier = None
    _DI_PAGE_LLM_AVAILABLE = False

__all__ = [
    'Config',
    'ClassificationMethod', 
    'create_classifier',
    'ACUClassifier',
    'ACULLMTextClassifier',
    'LLMImageClassifier',
]

# Only add if available
if _DI_PAGE_LLM_AVAILABLE:
    __all__.append('DIPageLLMClassifier')
