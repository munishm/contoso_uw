"""
Evaluation service wrapper for entity extraction quality assessment.

This module provides a unified interface to run correctness and completeness evaluators
for extracted entities against source OCR text.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging

from .evaluators.correctness_evaluator import ExtractionCorrectnessEvaluator
from .evaluators.completeness_evaluator import ExtractionCompletenessEvaluator

# Configure logger
logger = logging.getLogger(__name__)


class EvaluatorType(str, Enum):
    """Supported evaluator types."""
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    ALL = "all"


class EvaluationService:
    """
    Unified evaluation service for entity extraction quality assessment.
    
    This service provides a single interface to run multiple evaluators and return
    structured results in JSON format.
    
    Example:
        >>> service = EvaluationService(
        ...     azure_endpoint="https://...",
        ...     deployment_name="gpt-4",
        ...     api_version="2024-08-01-preview"
        ... )
        >>> 
        >>> result = service.evaluate(
        ...     field_name="invoice_number",
        ...     extracted_value="INV-123",
        ...     source_text="Invoice: INV-123",
        ...     evaluators=["correctness"]
        ... )
    """
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
        credential: Optional[Any] = None
    ):
        """
        Initialize the evaluation service.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint (required for completeness evaluator)
            deployment_name: Azure OpenAI deployment name (required for completeness evaluator)
            api_version: Azure OpenAI API version (required for completeness evaluator)
            credential: Azure credential object (required for completeness evaluator)
        """
        # Initialize correctness evaluator (no dependencies)
        try:
            self.correctness_evaluator = ExtractionCorrectnessEvaluator()
            logger.info("Correctness evaluator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize correctness evaluator: {e}")
            raise RuntimeError(f"Failed to initialize correctness evaluator: {e}") from e
        
        # Initialize completeness evaluator only if credentials provided
        self.completeness_evaluator = None
        logger.info(f"Checking completeness evaluator credentials - endpoint: {bool(azure_endpoint)}, deployment: {bool(deployment_name)}, api_version: {bool(api_version)}, credential: {bool(credential)}")
        
        if all([azure_endpoint, deployment_name, api_version, credential]):
            try:
                logger.info(f"Initializing completeness evaluator with endpoint: {azure_endpoint}, deployment: {deployment_name}")
                self.completeness_evaluator = ExtractionCompletenessEvaluator(
                    azure_endpoint=azure_endpoint,
                    deployment_name=deployment_name,
                    api_version=api_version,
                    credential=credential
                )
                logger.info("Completeness evaluator initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize completeness evaluator: {e}")
                # Don't raise, just log warning - completeness evaluator is optional
        else:
            missing = []
            if not azure_endpoint: missing.append("azure_endpoint")
            if not deployment_name: missing.append("deployment_name")
            if not api_version: missing.append("api_version")
            if not credential: missing.append("credential")
            logger.warning(f"Completeness evaluator NOT initialized - missing credentials: {missing}")
    
    def evaluate(
        self,
        field_name: str,
        extracted_value: str,
        source_text: str,
        evaluators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate an extracted field using specified evaluators.
        
        Args:
            field_name: Name of the extracted field (e.g., "invoice_number")
            extracted_value: The extracted value to evaluate
            source_text: Source OCR text to evaluate against
            evaluators: List of evaluators to run. Options: ["correctness", "completeness"]
                       If None or empty, runs all available evaluators.
        
        Returns:
            Dict containing evaluation results in JSON-serializable format:
            {
                "field_name": str,
                "extracted_value": str,
                "evaluations": {
                    "correctness": {...} or None,
                    "completeness": {...} or None
                },
                "summary": {
                    "overall_score": float,
                    "evaluators_run": List[str],
                    "warnings": List[str],
                    "errors": List[str]
                }
            }
        
        Raises:
            ValueError: If an invalid evaluator name is provided or invalid input
        """
        # Input validation
        if not field_name:
            raise ValueError("field_name cannot be empty")
        if not extracted_value:
            raise ValueError("extracted_value cannot be empty")
        if not source_text:
            raise ValueError("source_text cannot be empty")
        
        # Determine which evaluators to run
        if evaluators is None or len(evaluators) == 0:
            evaluators = [EvaluatorType.ALL.value]
        
        run_correctness = False
        run_completeness = False
        
        for evaluator in evaluators:
            if evaluator == EvaluatorType.ALL.value:
                run_correctness = True
                run_completeness = True
            elif evaluator == EvaluatorType.CORRECTNESS.value:
                run_correctness = True
            elif evaluator == EvaluatorType.COMPLETENESS.value:
                run_completeness = True
            else:
                raise ValueError(
                    f"Invalid evaluator: {evaluator}. "
                    f"Valid options: {[e.value for e in EvaluatorType]}"
                )
        
        # Initialize results structure
        results = {
            "field_name": field_name,
            "extracted_value": extracted_value,
            "evaluations": {
                "correctness": None,
                "completeness": None
            },
            "summary": {
                "overall_score": None,
                "evaluators_run": [],
                "warnings": [],
                "errors": []
            }
        }
        
        scores = []
        
        # Run correctness evaluation
        if run_correctness:
            try:
                correctness_result = self.correctness_evaluator.evaluate_field(
                    field_name=field_name,
                    extracted_value=extracted_value,
                    source_text=source_text
                )
                
                results["evaluations"]["correctness"] = {
                    "score": correctness_result.score,
                    "fuzzy_score": correctness_result.metadata["fuzzy_score"],
                    "extraction_correct": correctness_result.metadata["extraction_correct"],
                    "normalized_entity": correctness_result.metadata.get("normalized_entity"),
                    "cleaned_source_length": correctness_result.metadata.get("cleaned_source_length")
                }
                scores.append(correctness_result.score)
                results["summary"]["evaluators_run"].append("correctness")
            except Exception as e:
                error_msg = f"Correctness evaluation failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["summary"]["errors"].append(error_msg)
                results["evaluations"]["correctness"] = {"error": error_msg}
        
        # Run completeness evaluation
        if run_completeness:
            if self.completeness_evaluator is None:
                warning_msg = "Completeness evaluator not initialized. Azure OpenAI credentials required."
                results["summary"]["warnings"].append(warning_msg)
                logger.warning(f"COMPLETENESS SKIPPED for field '{field_name}': {warning_msg}")
            else:
                logger.info(f"Running completeness evaluation for field '{field_name}'")
                try:
                    completeness_result = self.completeness_evaluator.evaluate_field(
                        field_name=field_name,
                        extracted_value=extracted_value,
                        source_text=source_text
                    )
                    
                    results["evaluations"]["completeness"] = {
                        "score": completeness_result.score,
                        "is_relevant": completeness_result.metadata["is_relevant"],
                        "is_complete": completeness_result.metadata["is_complete"],
                        "missing_info": completeness_result.metadata.get("missing_info", []),
                        "reasoning": completeness_result.metadata.get("reasoning", "")
                    }
                    scores.append(completeness_result.score)
                    results["summary"]["evaluators_run"].append("completeness")
                    logger.info(f"Completeness evaluation SUCCESS for '{field_name}': score={completeness_result.score}, is_complete={completeness_result.metadata.get('is_complete')}")
                except Exception as e:
                    error_msg = f"Completeness evaluation failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results["summary"]["errors"].append(error_msg)
                    results["evaluations"]["completeness"] = {"error": error_msg}
        
        # Calculate overall score (average of all evaluator scores)
        if scores:
            results["summary"]["overall_score"] = sum(scores) / len(scores)
        
        return results
    
    def evaluate_batch(
        self,
        fields: List[Dict[str, str]],
        source_text: str,
        evaluators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate multiple extracted fields using specified evaluators.
        
        Args:
            fields: List of field dictionaries with "field_name" and "value" keys
            source_text: Source OCR text to evaluate against
            evaluators: List of evaluators to run. If None, runs all available.
        
        Returns:
            Dict containing batch evaluation results:
            {
                "total_fields": int,
                "results": List[Dict],
                "aggregate_summary": {
                    "average_overall_score": float,
                    "average_correctness_score": float,
                    "average_completeness_score": float,
                    "fields_correct": int,
                    "fields_complete": int,
                    "evaluators_run": List[str],
                    "failed_evaluations": int
                }
            }
        """
        batch_results = {
            "total_fields": len(fields),
            "results": [],
            "aggregate_summary": {
                "average_overall_score": None,
                "average_correctness_score": None,
                "average_completeness_score": None,
                "fields_correct": 0,
                "fields_complete": 0,
                "fields_not_extracted": 0,
                "evaluators_run": [],
                "failed_evaluations": 0
            }
        }
        
        overall_scores = []
        correctness_scores = []
        completeness_scores = []
        
        # Evaluate each field
        for field in fields:
            field_name = field.get("field_name")
            extracted_value = field.get("value")
            
            if not field_name:
                logger.warning(f"Skipping field with missing field_name: {field}")
                continue
            
            # Handle fields with null/empty values - give them a score of 0
            if not extracted_value or extracted_value.strip() == "":
                logger.info(f"Field '{field_name}' has no extracted value - scoring as 0")
                result = {
                    "field_name": field_name,
                    "extracted_value": extracted_value,
                    "evaluations": {
                        "correctness": {
                            "score": 0.0,
                            "fuzzy_score": 0.0,
                            "extraction_correct": False,
                            "normalized_entity": None,
                            "reason": "No value extracted"
                        },
                        "completeness": {
                            "score": 0.0,
                            "is_relevant": True,
                            "is_complete": False,
                            "missing_info": ["Field value not extracted"],
                            "reason": "No value extracted"
                        }
                    },
                    "summary": {
                        "overall_score": 0.0,
                        "evaluators_run": ["correctness", "completeness"],
                        "warnings": ["Field has no extracted value - scored as 0"],
                        "errors": []
                    }
                }
                batch_results["results"].append(result)
                batch_results["aggregate_summary"]["fields_not_extracted"] += 1
                overall_scores.append(0.0)
                correctness_scores.append(0.0)
                completeness_scores.append(0.0)
                continue
            
            try:
                result = self.evaluate(
                    field_name=field_name,
                    extracted_value=extracted_value,
                    source_text=source_text,
                    evaluators=evaluators
                )
                
                # Track if evaluation had errors
                if result["summary"]["errors"]:
                    batch_results["aggregate_summary"]["failed_evaluations"] += 1
                
            except Exception as e:
                # If individual evaluation completely fails, create error result
                logger.error(f"Failed to evaluate field {field_name}: {e}", exc_info=True)
                result = {
                    "field_name": field_name,
                    "extracted_value": extracted_value,
                    "evaluations": {
                        "correctness": None,
                        "completeness": None
                    },
                    "summary": {
                        "overall_score": None,
                        "evaluators_run": [],
                        "warnings": [],
                        "errors": [f"Evaluation failed: {str(e)}"]
                    }
                }
                batch_results["aggregate_summary"]["failed_evaluations"] += 1
            
            batch_results["results"].append(result)
            
            # Collect scores for aggregation
            if result["summary"]["overall_score"] is not None:
                overall_scores.append(result["summary"]["overall_score"])
            
            if result["evaluations"]["correctness"] and "score" in result["evaluations"]["correctness"]:
                correctness_scores.append(result["evaluations"]["correctness"]["score"])
                if result["evaluations"]["correctness"].get("extraction_correct"):
                    batch_results["aggregate_summary"]["fields_correct"] += 1
            
            if result["evaluations"]["completeness"] and "score" in result["evaluations"]["completeness"]:
                completeness_scores.append(result["evaluations"]["completeness"]["score"])
                if result["evaluations"]["completeness"].get("is_complete"):
                    batch_results["aggregate_summary"]["fields_complete"] += 1
        
        # Calculate aggregate metrics
        if overall_scores:
            batch_results["aggregate_summary"]["average_overall_score"] = sum(overall_scores) / len(overall_scores)
        
        if correctness_scores:
            batch_results["aggregate_summary"]["average_correctness_score"] = sum(correctness_scores) / len(correctness_scores)
        
        if completeness_scores:
            batch_results["aggregate_summary"]["average_completeness_score"] = sum(completeness_scores) / len(completeness_scores)
        
        # Record which evaluators were run
        if batch_results["results"]:
            batch_results["aggregate_summary"]["evaluators_run"] = batch_results["results"][0]["summary"]["evaluators_run"]
        
        return batch_results
    
    def to_json(self, result: Dict[str, Any], indent: int = 4) -> str:
        """
        Convert evaluation result to JSON string.
        
        Args:
            result: Evaluation result dictionary from evaluate() or evaluate_batch()
            indent: JSON indentation level
        
        Returns:
            JSON string representation of the result
        """
        return json.dumps(result, indent=indent, ensure_ascii=False)
