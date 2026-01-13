from typing import Any
from evaluators.base_evaluator import BaseEvaluator, EvaluationResult
from utils.text_utils import clean_text, normalize_value


class ExtractionCorrectnessEvaluator(BaseEvaluator):
    """
    Evaluates whether an extracted field value is present in the OCR source text.

    Logic:
    - Tokenize extracted value and source text
    - Measure token-level containment
    - Extraction is correct ONLY if all extracted tokens appear in source text
    - Score reflects token coverage (diagnostic, not decision)
    """

    def __init__(self):
        pass

    def evaluate_field(
        self,
        field_name: str,
        extracted_value: Any,
        source_text: str,
        **kwargs
    ) -> EvaluationResult:
        # Normalize inputs
        normalized_extracted_value = normalize_value(extracted_value).lower().strip()
        normalized_source_text = clean_text(source_text).lower().strip()

        # Handle empty extracted value
        if not normalized_extracted_value:
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "token_coverage_ratio": 0.0,
                    "extraction_correct": False,
                    "reason": "Empty extracted value"
                }
            )

        # Handle empty source text
        if not normalized_source_text:
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "token_coverage_ratio": 0.0,
                    "extraction_correct": False,
                    "reason": "Empty source text"
                }
            )

        # Tokenize extracted value and source text
        extracted_value_tokens = set(normalized_extracted_value.split())
        source_text_tokens = set(normalized_source_text.split())

        # Compute token-level coverage
        if not extracted_value_tokens:
            token_coverage_ratio = 0.0
        else:
            matched_tokens = extracted_value_tokens.intersection(source_text_tokens)
            token_coverage_ratio = len(matched_tokens) / len(extracted_value_tokens)

        # Strict correctness: all tokens must be present
        extraction_correct = token_coverage_ratio == 1.0

        return EvaluationResult(
            field_name=field_name,
            entity_value=extracted_value,
            score=token_coverage_ratio,
            metadata={
                "token_coverage_ratio": token_coverage_ratio,
                "extraction_correct": extraction_correct,
                "normalized_extracted_value": normalized_extracted_value,
                "extracted_token_count": len(extracted_value_tokens),
                "source_token_count": len(source_text_tokens)
            }
        )
