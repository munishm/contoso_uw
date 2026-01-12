import logging
from typing import Dict, List, Optional

from .base_evaluator import BaseEvaluator, EvaluationResult
from ..utils.evaluation_utils import (
    split_summary_into_sentences,
    extract_numeric_values,
    normalize_text,
)

logger = logging.getLogger(__name__)


class GroundednessEvaluator(BaseEvaluator):
    """
    Evaluates factual groundedness of generated summaries.

    Principles:
    - Numeric entities → relative deviation penalty
    - Textual entities → sentence-level token containment
    - Weighted average of entity grounding scores
    - Sentence-level matching avoids dilution for long summaries
    """

    def __init__(self, entity_importance_weights: Optional[Dict[str, float]] = None):
        self.entity_importance_weights = entity_importance_weights or {}

    # ------------------------------------------------------------------
    # Numeric grounding
    # ------------------------------------------------------------------
    def compute_numeric_grounding_score(
        self, extracted_entity_value: str, summary_text: str
    ) -> Optional[float]:
        """
        Compute grounding score for numeric entities using relative deviation.

        Returns:
            Score in [0.0, 1.0], or None if entity is not numeric.
        """
        source_numbers = extract_numeric_values(extracted_entity_value)
        if not source_numbers:
            return None  # Not numeric

        summary_numbers = extract_numeric_values(summary_text)
        if not summary_numbers:
            return 0.0  # Numeric entity missing in summary

        source_value = source_numbers[0]
        closest_summary_value = min(
            summary_numbers, key=lambda candidate: abs(candidate - source_value)
        )

        relative_error = abs(closest_summary_value - source_value) / max(
            abs(source_value), 1e-6
        )
        return max(0.0, 1.0 - relative_error)

    # ------------------------------------------------------------------
    # Textual grounding
    # ------------------------------------------------------------------
    def compute_textual_grounding_score(
        self, extracted_entity_value: str, summary_text: str
    ) -> float:
        """
        Compute grounding score for textual entities via token containment.

        - Normalize entity and summary text.
        - Split summary into sentences.
        - For each sentence, compute fraction of entity tokens present.
        - Return maximum fraction across sentences (1.0 = fully supported).

        Returns:
            Score in [0.0, 1.0]
        """
        entity_tokens = set(normalize_text(extracted_entity_value))
        if not entity_tokens:
            return 0.0

        summary_sentences = split_summary_into_sentences(summary_text)
        max_support_score = 0.0

        for sentence in summary_sentences:
            sentence_tokens = set(normalize_text(sentence))
            if not sentence_tokens:
                continue

            token_overlap = entity_tokens.intersection(sentence_tokens)
            support_score = len(token_overlap) / len(entity_tokens)

            max_support_score = max(max_support_score, support_score)

            if max_support_score == 1.0:
                break  # Early exit if fully supported

        return max_support_score

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def evaluate(
        self, summary: str, entities: Dict[str, str], context: Optional[str] = None, **kwargs
    ) -> EvaluationResult:
        """
        Evaluate groundedness of a summary.

        - Computes numeric and textual grounding scores.
        - Uses weighted average if entity weights are provided.
        - Provides entity-level scores and feedback.
        """
        try:
            if not self.validate_inputs(summary, entities):
                return EvaluationResult(
                    summary=summary,
                    score=0.0,
                    feedback="Invalid inputs",
                    success=False
                )

            valid_entities = {name: value for name, value in entities.items() if value and str(value).strip()}
            if not valid_entities:
                return EvaluationResult(
                    summary=summary,
                    score=1.0,
                    feedback="No entities to evaluate - vacuously grounded",
                    success=True
                )

            entity_weights = kwargs.get("entity_importance_weights", self.entity_importance_weights)

            weighted_score_sum = 0.0
            total_weight = 0.0
            entity_scores = {}
            numeric_entities = []
            textual_entities = []
            poorly_grounded = []
            well_grounded = []

            for entity_name, extracted_value in valid_entities.items():
                numeric_score = self.compute_numeric_grounding_score(extracted_value, summary)
                if numeric_score is not None:
                    grounding_score = numeric_score
                    numeric_entities.append(entity_name)
                else:
                    grounding_score = self.compute_textual_grounding_score(extracted_value, summary)
                    textual_entities.append(entity_name)

                weight = entity_weights.get(entity_name, 1.0)
                entity_scores[entity_name] = grounding_score
                weighted_score_sum += grounding_score * weight
                total_weight += weight

                if grounding_score < 0.5:
                    poorly_grounded.append((entity_name, grounding_score))
                elif grounding_score > 0.8:
                    well_grounded.append((entity_name, grounding_score))

            overall_score = weighted_score_sum / total_weight if total_weight > 0 else 1.0

            # Feedback string
            feedback = (
                "Excellent groundedness" if overall_score >= 0.9 else
                "Good groundedness" if overall_score >= 0.7 else
                "Moderate groundedness" if overall_score >= 0.5 else
                "Poor groundedness"
            )
            feedback += f" ({overall_score:.3f})"

            if poorly_grounded:
                weak_entities = [name for name, _ in poorly_grounded[:2]]
                feedback += f". Weak: {', '.join(weak_entities)}"
                if len(poorly_grounded) > 2:
                    feedback += f" (+{len(poorly_grounded) - 2} more)"

            return EvaluationResult(
                summary=summary,
                score=overall_score,
                feedback=feedback,
                metadata={
                    "entity_scores": entity_scores,
                    "numeric_entities": numeric_entities,
                    "textual_entities": textual_entities,
                    "well_grounded_entities": [e for e, _ in well_grounded],
                    "poorly_grounded_entities": [e for e, _ in poorly_grounded],
                    "total_entities": len(valid_entities)
                },
                success=True
            )

        except Exception as exc:
            logger.error(f"Groundedness evaluation failed: {exc}")
            return EvaluationResult(
                summary=summary,
                score=0.0,
                feedback="Evaluation failed",
                success=False,
                error_message=str(exc)
            )

    def get_evaluator_name(self) -> str:
        return "groundedness"