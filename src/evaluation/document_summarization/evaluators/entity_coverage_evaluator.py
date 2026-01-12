"""
Entity Coverage Score (ECS) Evaluator.

Measures how much of the extracted entities are present in a generated summary,
weighted by information density (token count + character density).

Score Formula:
    ECS = Σ(weights of covered entities) / Σ(weights of all entities)
    Weight for entity:
        w_e = log(1 + token_count) + alpha * log(1 + chars_per_token)

Fully automated, schema-agnostic, no entropy or pattern heuristics.
"""

import math
import logging
from typing import Dict, Optional, Any

from .base_evaluator import BaseEvaluator, EvaluationResult
from ..utils.evaluation_utils import normalize_text


logger = logging.getLogger(__name__)


class EntityCoverageEvaluator(BaseEvaluator):
    """
    Evaluates entity coverage in generated summaries.
    
    Uses fully automated weighting based on token count and character density.
    Coverage is determined by token overlap (tolerates rewording and reordering).
    
    Score Formula:
        Weighted ECS = Σ(wᵢ for covered eᵢ) / Σ(wᵢ for all eᵢ)
        where wᵢ = log(1 + token_count) + alpha * log(1 + chars_per_token)
    """
    
    def __init__(self, alpha: float = 0.5, token_threshold: float = 0.7):
        """
        Initialize the evaluator.
        
        Args:
            alpha: Scaling factor for density contribution (default: 0.5)
            token_threshold: Fraction of tokens that must overlap for coverage (default: 0.7)
        """
        self.alpha = alpha
        self.token_threshold = token_threshold
    
    def is_entity_covered(self, entity_value: str, summary: str) -> bool:
        """
        Checks if an entity value is sufficiently expressed in the summary
        using token overlap.
        
        Args:
            entity_value: String of entity value
            summary: Generated summary string
            
        Returns:
            True if covered (overlap >= threshold), False otherwise
        """
        entity_tokens = set(normalize_text(entity_value))
        summary_tokens = set(normalize_text(summary))
        
        if not entity_tokens:
            return False
        
        overlap_ratio = len(entity_tokens & summary_tokens) / len(entity_tokens)
        return overlap_ratio >= self.token_threshold
    
    def compute_entity_weights(self, entity_values: Dict[str, str]) -> Dict[str, float]:
        """
        Compute automated weights for entities based on token count and character density.
        
        Weight formula:
            w = log(1 + token_count) + alpha * log(1 + chars_per_token)
        
        Args:
            entity_values: Dictionary of entity names and values
            
        Returns:
            Dictionary mapping entity names to weights
        """
        weights = {}
        
        for entity_name, value in entity_values.items():
            value_clean = value.strip()
            token_count = len(value_clean.split())
            char_count = len(value_clean.replace(' ', ''))
            chars_per_token = char_count / max(token_count, 1)
            
            # Fully automated weight calculation
            weight = math.log(1 + token_count) + self.alpha * math.log(1 + chars_per_token)
            weights[entity_name] = weight
        
        return weights
    
    def evaluate(
        self,
        summary: str,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate entity coverage in the summary.
        
        Uses token overlap to determine coverage and automated weighting
        based on token count and character density.
        
        Args:
            summary: Generated summary text
            entities: Dictionary of entity names and values
            context: Optional context (unused)
            **kwargs: Additional parameters (alpha, token_threshold)
            
        Returns:
            EvaluationResult with coverage score and metadata
        """
        try:
            # Validate inputs
            if not self.validate_inputs(summary, entities):
                return EvaluationResult(
                    summary=summary,
                    score=0.0,
                    feedback="Invalid inputs provided",
                    success=False,
                    error_message="Summary or entities are empty or invalid"
                )
            
            # Vacuum-safe: no entities = perfect score
            if not entities:
                return EvaluationResult(
                    summary=summary,
                    score=1.0,
                    feedback="No entities to evaluate - vacuously perfect",
                    metadata={},
                    success=True
                )
            
            # Filter out None values
            valid_entities = {k: v for k, v in entities.items() if v is not None and str(v).strip()}
            
            if not valid_entities:
                return EvaluationResult(
                    summary=summary,
                    score=1.0,
                    feedback="No valid entities to evaluate - vacuously perfect",
                    metadata={},
                    success=True
                )
            
            # Compute entity weights
            weights = self.compute_entity_weights(valid_entities)
            
            # Calculate coverage using token overlap
            covered_weight = 0.0
            total_weight = sum(weights.values())
            covered_entities = []
            missing_entities = []
            entity_overlaps = {}
            
            for entity_name, value in valid_entities.items():
                # Check coverage using token overlap
                if self.is_entity_covered(value, summary):
                    covered_weight += weights[entity_name]
                    covered_entities.append(entity_name)
                    
                    # Calculate actual overlap ratio for metadata
                    entity_tokens = set(normalize_text(value))
                    summary_tokens = set(normalize_text(summary))
                    overlap_ratio = len(entity_tokens & summary_tokens) / len(entity_tokens) if entity_tokens else 0.0
                    entity_overlaps[entity_name] = overlap_ratio
                else:
                    missing_entities.append(entity_name)
                    entity_overlaps[entity_name] = 0.0
            
            # Calculate score
            score = covered_weight / total_weight if total_weight > 0 else 0.0
            
            # Generate feedback
            coverage_pct = (len(covered_entities) / len(entities)) * 100
            feedback = f"Covered {len(covered_entities)}/{len(entities)} entities ({coverage_pct:.1f}%)"
            
            if missing_entities:
                feedback += f". Missing: {', '.join(missing_entities[:3])}"
                if len(missing_entities) > 3:
                    feedback += f" and {len(missing_entities) - 3} more"
            
            return EvaluationResult(
                summary=summary,
                score=score,
                feedback=feedback,
                metadata={
                    "covered_entities": covered_entities,
                    "missing_entities": missing_entities,
                    "covered_count": len(covered_entities),
                    "total_count": len(entities),
                    "weights": weights,
                    "covered_weight": covered_weight,
                    "total_weight": total_weight,
                    "alpha": self.alpha,
                    "token_threshold": self.token_threshold,
                    "entity_overlaps": entity_overlaps
                },
                success=True
            )
        
        except Exception as e:
            logger.error(f"Error in entity coverage evaluation: {e}")
            return EvaluationResult(
                summary=summary,
                score=0.0,
                feedback="Evaluation failed",
                success=False,
                error_message=str(e)
            )
    
    def get_evaluator_name(self) -> str:
        """Get evaluator identifier."""
        return "entity_coverage"
