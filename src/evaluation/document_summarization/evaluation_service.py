"""
Evaluation service wrapper for summary quality assessment.

This module provides a unified interface to run multiple evaluators
for generated summaries against source entities.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging

from .evaluators.base_evaluator import BaseEvaluator, EvaluationResult


logger = logging.getLogger(__name__)


class EvaluatorType(str, Enum):
    """Supported evaluator types."""
    # Placeholder for future evaluators
    # COMPLETENESS = "completeness"
    # ACCURACY = "accuracy"
    # RELEVANCE = "relevance"
    ALL = "all"


class SummaryEvaluationService:
    """
    Unified evaluation service for summary quality assessment.
    
    This service provides a single interface to run multiple evaluators and return
    structured results in JSON format.
    
    Example:
        >>> service = SummaryEvaluationService(
        ...     azure_endpoint="https://...",
        ...     deployment_name="gpt-4",
        ...     api_version="2024-08-01-preview"
        ... )
        >>> 
        >>> result = service.evaluate(
        ...     summary="John Doe is a 35-year-old software engineer...",
        ...     entities={"name": "John Doe", "age": "35", "occupation": "Software Engineer"},
        ...     evaluators=["all"]
        ... )
    """
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
        credential: Optional[Any] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the evaluation service.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint (required for LLM-based evaluators)
            deployment_name: Azure OpenAI deployment name (required for LLM-based evaluators)
            api_version: Azure OpenAI API version (required for LLM-based evaluators)
            credential: Azure credential object (optional, use either credential or api_key)
            api_key: API key for authentication (optional, use either credential or api_key)
        """
        self.azure_endpoint = azure_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.credential = credential
        self.api_key = api_key
        
        # Dictionary to store evaluator instances
        self.evaluators: Dict[str, BaseEvaluator] = {}
        
        logger.info("SummaryEvaluationService initialized (no evaluators registered yet)")
    
    def register_evaluator(self, evaluator: BaseEvaluator) -> None:
        """
        Register a new evaluator with the service.
        
        Args:
            evaluator: Instance of BaseEvaluator to register
        """
        evaluator_name = evaluator.get_evaluator_name()
        if evaluator_name in self.evaluators:
            logger.warning(f"Overwriting existing evaluator: {evaluator_name}")
        self.evaluators[evaluator_name] = evaluator
        logger.info(f"Registered evaluator: {evaluator_name}")
    
    def evaluate(
        self,
        summary: str,
        entities: Dict[str, str],
        context: Optional[str] = None,
        evaluators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a generated summary using specified evaluators.
        
        Args:
            summary: The generated summary text to evaluate
            entities: Dictionary of entity names and values used to generate the summary
            context: Optional context (e.g., document type)
            evaluators: List of evaluator names to run. If None, runs all registered evaluators.
            
        Returns:
            Dictionary containing evaluation results:
            {
                "summary": str,
                "overall_score": float,
                "evaluations": {
                    "evaluator_name": {
                        "score": float,
                        "feedback": str,
                        "metadata": dict
                    }
                },
                "success": bool,
                "error_message": str (if error occurred)
            }
        """
        try:
            # Log input details
            logger.info("=" * 80)
            logger.info("SUMMARIZATION EVALUATION - Starting evaluation")
            logger.info("=" * 80)
            logger.info(f"Context: {context or 'Not provided'}")
            logger.info(f"Summary length: {len(summary)} characters")
            logger.info(f"Summary preview: {summary[:200]}..." if len(summary) > 200 else f"Summary: {summary}")
            logger.info(f"Number of entities: {len(entities)}")
            logger.info("-" * 40)
            logger.info("ENTITIES TO EVALUATE:")
            for entity_name, entity_value in entities.items():
                value_preview = str(entity_value)[:100] + "..." if len(str(entity_value)) > 100 else str(entity_value)
                logger.info(f"  • {entity_name}: {value_preview}")
            logger.info("-" * 40)
            
            # Validate inputs
            if not summary or not isinstance(summary, str):
                logger.error("Validation failed: Summary must be a non-empty string")
                raise ValueError("Summary must be a non-empty string")
            
            if not entities or not isinstance(entities, dict):
                logger.error("Validation failed: Entities must be a non-empty dictionary")
                raise ValueError("Entities must be a non-empty dictionary")
            
            # Determine which evaluators to run
            if evaluators is None or "all" in evaluators:
                evaluators_to_run = list(self.evaluators.keys())
            else:
                evaluators_to_run = evaluators
            
            logger.info(f"Evaluators to run: {evaluators_to_run}")
            
            # Check if we have any evaluators
            if not evaluators_to_run or not self.evaluators:
                logger.warning("No evaluators registered or specified")
                return {
                    "summary": summary,
                    "overall_score": 0.0,
                    "evaluations": {},
                    "success": False,
                    "error_message": "No evaluators available"
                }
            
            # Run evaluations
            evaluation_results = {}
            scores = []
            
            logger.info("=" * 80)
            logger.info("RUNNING EVALUATORS")
            logger.info("=" * 80)
            
            for evaluator_name in evaluators_to_run:
                if evaluator_name not in self.evaluators:
                    logger.warning(f"Evaluator '{evaluator_name}' not found, skipping")
                    continue
                
                evaluator = self.evaluators[evaluator_name]
                logger.info(f"\n┌{'─' * 78}┐")
                logger.info(f"│ Running evaluator: {evaluator_name:<58}│")
                logger.info(f"└{'─' * 78}┘")
                
                try:
                    result = evaluator.evaluate(
                        summary=summary,
                        entities=entities,
                        context=context
                    )
                    
                    evaluation_results[evaluator_name] = {
                        "score": result.score,
                        "feedback": result.feedback,
                        "metadata": result.metadata,
                        "success": result.success
                    }
                    
                    # Log detailed evaluator results
                    logger.info(f"  ├─ Score: {result.score:.4f} ({result.score * 100:.1f}%)")
                    logger.info(f"  ├─ Success: {result.success}")
                    if result.feedback:
                        # Log feedback with proper formatting for multi-line
                        feedback_lines = result.feedback.split('\n')
                        logger.info(f"  ├─ Feedback:")
                        for line in feedback_lines[:10]:  # Limit to first 10 lines
                            logger.info(f"  │    {line}")
                        if len(feedback_lines) > 10:
                            logger.info(f"  │    ... ({len(feedback_lines) - 10} more lines)")
                    
                    if result.metadata:
                        logger.info(f"  └─ Metadata:")
                        for key, value in result.metadata.items():
                            if isinstance(value, list):
                                logger.info(f"       • {key}: [{len(value)} items]")
                                for item in value[:5]:  # Show first 5 items
                                    logger.info(f"         - {item}")
                                if len(value) > 5:
                                    logger.info(f"         ... ({len(value) - 5} more items)")
                            elif isinstance(value, dict):
                                logger.info(f"       • {key}: {json.dumps(value, indent=2)[:200]}")
                            else:
                                logger.info(f"       • {key}: {value}")
                    
                    if result.success:
                        scores.append(result.score)
                        logger.info(f"  ✓ Evaluator completed successfully")
                    else:
                        logger.warning(f"  ✗ Evaluator completed but marked as unsuccessful")
                
                except Exception as e:
                    logger.error(f"Error running evaluator '{evaluator_name}': {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    evaluation_results[evaluator_name] = {
                        "score": 0.0,
                        "feedback": None,
                        "metadata": {},
                        "success": False,
                        "error_message": str(e)
                    }
            
            # Calculate overall score
            overall_score = sum(scores) / len(scores) if scores else 0.0
            
            # Log summary of results
            logger.info("\n" + "=" * 80)
            logger.info("EVALUATION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Total evaluators run: {len(scores)}/{len(evaluators_to_run)}")
            logger.info(f"Individual scores:")
            for eval_name, eval_result in evaluation_results.items():
                status = "✓" if eval_result.get("success") else "✗"
                logger.info(f"  {status} {eval_name}: {eval_result['score']:.4f} ({eval_result['score'] * 100:.1f}%)")
            logger.info(f"\n  ★ OVERALL SCORE: {overall_score:.4f} ({overall_score * 100:.1f}%)")
            logger.info("=" * 80)
            
            return {
                "summary": summary,
                "entities": entities,
                "context": context,
                "overall_score": overall_score,
                "evaluations": evaluation_results,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            return {
                "summary": summary,
                "overall_score": 0.0,
                "evaluations": {},
                "success": False,
                "error_message": str(e)
            }
    
    def evaluate_batch(
        self,
        summaries: List[Dict[str, Any]],
        evaluators: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple summaries in batch.
        
        Args:
            summaries: List of dictionaries containing 'summary', 'entities', and optionally 'context'
            evaluators: List of evaluator names to run
            
        Returns:
            List of evaluation result dictionaries
        """
        results = []
        
        for item in summaries:
            result = self.evaluate(
                summary=item.get("summary", ""),
                entities=item.get("entities", {}),
                context=item.get("context"),
                evaluators=evaluators
            )
            results.append(result)
        
        return results
    
    def get_registered_evaluators(self) -> List[str]:
        """
        Get list of registered evaluator names.
        
        Returns:
            List of evaluator names
        """
        return list(self.evaluators.keys())
    
    def to_json(self, result: Dict[str, Any], indent: int = 2) -> str:
        """
        Convert evaluation result to JSON string.
        
        Args:
            result: Evaluation result dictionary
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        return json.dumps(result, indent=indent, ensure_ascii=False)
