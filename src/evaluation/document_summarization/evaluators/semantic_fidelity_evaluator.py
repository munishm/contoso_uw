"""
Semantic Expression Fidelity (SEF) Evaluator.

Measures how faithfully entity values are expressed in a generated summary.
Allows natural language variation while penalizing abstraction, dilution,
and incorrect numeric grounding.

Core idea:
- Each entity value is compared independently against the full summary.
- Similarity scores are averaged across entities.
- No ground truth summaries or LLM judges required.
"""

import logging
import re
from typing import Dict, Optional

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from .base_evaluator import BaseEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class SemanticFidelityEvaluator(BaseEvaluator):
    """
    Evaluates how well the semantic content of entity values
    is preserved in the generated summary.
    """

    def __init__(
        self,
        use_rapidfuzz: bool = True,
        verbosity_dampening_exponent: float = 0.3  # kept for API compatibility
    ):
        """
        Initialize the SEF evaluator.

        Args:
            use_rapidfuzz: Whether to use rapidfuzz for fuzzy matching
            verbosity_dampening_exponent: kept for API consistency; no longer applied aggressively
        """
        self.use_rapidfuzz = use_rapidfuzz and RAPIDFUZZ_AVAILABLE
        self.verbosity_dampening_exponent = verbosity_dampening_exponent

        if use_rapidfuzz and not RAPIDFUZZ_AVAILABLE:
            logger.warning(
                "rapidfuzz not installed. Falling back to token overlap similarity."
            )

    @staticmethod
    def is_numeric_heavy_entity(entity_value: str) -> bool:
        """
        Determine if an entity contains numeric content.

        Numeric-heavy entities require stricter evaluation.
        """
        return bool(re.search(r"\d", entity_value))

    @staticmethod
    def basic_token_overlap_similarity(
        entity_value: str,
        summary_text: str
    ) -> float:
        """
        Fallback similarity metric using token overlap.

        Args:
            entity_value: Entity string
            summary_text: Summary string

        Returns:
            Fraction of entity tokens present in summary
        """
        entity_tokens = set(re.findall(r"\w+", entity_value.lower()))
        summary_tokens = set(re.findall(r"\w+", summary_text.lower()))

        if not entity_tokens:
            return 0.0

        return len(entity_tokens & summary_tokens) / len(entity_tokens)

    def compute_verbosity_dampening_factor(
        self,
        entity_value: str,
        summary_text: str
    ) -> float:
        """
        Verbosity dampening factor.

        Previously penalized long summaries for short entities.
        Now neutralized for structured summaries.
        """
        return 1.0

    def compute_entity_similarity(
        self,
        entity_value: str,
        summary_text: str
    ) -> float:
        """
        Compute similarity between an entity value and the summary text.

        Logic:
        - Numeric-heavy entities:
            - Exact substring match → 1.0
            - Else → partial_ratio (fuzzy)
        - Textual entities:
            - Fuzzy token set ratio
        - Without RapidFuzz → basic token overlap

        Returns:
            Similarity score in [0.0, 1.0]
        """
        if not entity_value or not summary_text:
            return 0.0

        # Clean text: lowercase + remove punctuation
        cleaned_entity_value = re.sub(r"[^\w\s]", "", entity_value.lower()).strip()
        cleaned_summary_text = re.sub(r"[^\w\s]", "", summary_text.lower()).strip()

        # Base similarity score
        if self.use_rapidfuzz:
            if self.is_numeric_heavy_entity(cleaned_entity_value):
                # Strict numeric grounding
                if cleaned_entity_value in cleaned_summary_text:
                    base_similarity_score = 1.0
                else:
                    base_similarity_score = (
                        fuzz.partial_ratio(
                            cleaned_entity_value,
                            cleaned_summary_text
                        ) / 100.0
                    )
            else:
                # Textual entities: token set ratio
                base_similarity_score = (
                    fuzz.token_set_ratio(
                        cleaned_entity_value,
                        cleaned_summary_text
                    ) / 100.0
                )
        else:
            # Fallback: token overlap
            base_similarity_score = self.basic_token_overlap_similarity(
                cleaned_entity_value,
                cleaned_summary_text
            )

        # Apply verbosity dampening (neutralized)
        verbosity_dampening_factor = self.compute_verbosity_dampening_factor(
            cleaned_entity_value,
            cleaned_summary_text
        )

        return base_similarity_score * verbosity_dampening_factor

    def evaluate(
        self,
        summary: str,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate semantic expression fidelity.

        Returns:
            EvaluationResult with average semantic fidelity and per-entity scores
        """
        try:
            if not self.validate_inputs(summary, entities):
                return EvaluationResult(
                    summary=summary,
                    score=0.0,
                    feedback="Invalid inputs provided",
                    success=False,
                    error_message="Summary or entities are empty or invalid",
                )

            # Keep only non-empty entities
            valid_entities = {k: v for k, v in entities.items() if v and str(v).strip()}
            
            if not valid_entities:
                return EvaluationResult(
                    summary=summary,
                    score=1.0,
                    feedback="No valid entities to evaluate - vacuously satisfied",
                    metadata={},
                    success=True
                )

            entity_similarity_scores: Dict[str, float] = {}
            all_entity_similarity_scores = []

            for entity_name, entity_value in valid_entities.items():
                similarity_score = self.compute_entity_similarity(
                    entity_value,
                    summary
                )
                entity_similarity_scores[entity_name] = similarity_score
                all_entity_similarity_scores.append(similarity_score)

            average_semantic_fidelity = sum(all_entity_similarity_scores) / len(all_entity_similarity_scores)

            # Human-readable feedback
            if average_semantic_fidelity >= 0.9:
                feedback_text = "Excellent semantic fidelity"
            elif average_semantic_fidelity >= 0.7:
                feedback_text = "Good semantic fidelity with minor abstraction"
            elif average_semantic_fidelity >= 0.5:
                feedback_text = "Moderate fidelity; some entities are loosely expressed"
            else:
                feedback_text = "Low semantic fidelity; significant meaning loss detected"

            return EvaluationResult(
                summary=summary,
                score=average_semantic_fidelity,
                feedback=f"{feedback_text} ({average_semantic_fidelity:.3f})",
                metadata={
                    "entity_similarity_scores": entity_similarity_scores,
                    "average_semantic_fidelity": average_semantic_fidelity,
                    "minimum_entity_similarity": min(all_entity_similarity_scores),
                    "maximum_entity_similarity": max(all_entity_similarity_scores),
                    "using_rapidfuzz": self.use_rapidfuzz,
                    "verbosity_dampening_exponent": self.verbosity_dampening_exponent,
                    "total_entities_evaluated": len(valid_entities),
                    "filtered_entities": len(entities) - len(valid_entities),
                },
                success=True,
            )

        except Exception as evaluation_error:
            logger.error(f"Error during semantic fidelity evaluation: {evaluation_error}")
            return EvaluationResult(
                summary=summary,
                score=0.0,
                feedback="Evaluation failed",
                success=False,
                error_message=str(evaluation_error),
            )

    def get_evaluator_name(self) -> str:
        """Return evaluator identifier."""
        return "semantic_fidelity"