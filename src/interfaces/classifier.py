"""Document classification interface and implementation."""

import logging
from typing import Protocol, Any
from abc import abstractmethod

from src.document_classification import create_classifier, Config
from src.shared.models.classification import ClassificationResponse

logger = logging.getLogger(__name__)

from typing import Protocol, Any
import logging

logger = logging.getLogger(__name__)

class IClassifier(Protocol):
    def classify(self, document: dict[str, Any]) -> ClassificationResponse:
        ...

    def get_document_types(self) -> list[str]:
        ...

    def set_confidence_threshold(self, threshold: float) -> None:
        ...

    @property
    def confidence_threshold(self) -> float:
        ...


class DocumentClassifier:
    def __init__(self):
        self.config = Config()
        self._classifier: IClassifier = create_classifier(self.config)

        logger.info(
            f"DocumentClassifier initialized with method: "
            f"{self.config.CLASSIFICATION_METHOD.value}"
        )

    def classify(self, document: dict[str, Any]) -> ClassificationResponse:
        return self._classifier.classify(document)

    def get_document_types(self) -> list[str]:
        return self._classifier.get_document_types()

    def set_confidence_threshold(self, threshold: float) -> None:
        self._classifier.set_confidence_threshold(threshold)

    @property
    def confidence_threshold(self) -> float:
        return self._classifier.confidence_threshold
