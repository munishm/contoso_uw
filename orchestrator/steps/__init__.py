"""Step auto-registration: import all step modules so decorators fire."""

from .classification_step import ClassificationStep
from .ocr_step import OcrStep
from .ner_step import NerStep
from .send_step import SendStep

__all__ = [
    "ClassificationStep",
    "OcrStep",
    "NerStep",
    "SendStep",
]
