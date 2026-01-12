from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvaluationResult(BaseModel):
    """Base evaluation result model for summary quality assessment."""
    
    summary: str
    score: float
    metadata: Dict[str, Any] = {}
    feedback: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class BaseEvaluator(ABC):
    """Abstract base class for summary evaluators."""
    
    @abstractmethod
    def evaluate(
        self,
        summary: str,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate a generated summary.
        
        Args:
            summary: The generated summary text to evaluate
            entities: Dictionary of entity names and values used to generate the summary
            context: Optional additional context (e.g., document type)
            **kwargs: Additional evaluator-specific parameters
            
        Returns:
            EvaluationResult with score, feedback, and metadata
        """
        pass
    
    def evaluate_batch(
        self,
        summaries: List[Dict[str, Any]],
        **kwargs
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple summaries in batch.
        
        Args:
            summaries: List of dictionaries containing summary, entities, and context
            **kwargs: Additional evaluator-specific parameters
            
        Returns:
            List of EvaluationResult objects
        """
        results = []
        for item in summaries:
            result = self.evaluate(
                summary=item.get("summary", ""),
                entities=item.get("entities", {}),
                context=item.get("context"),
                **kwargs
            )
            results.append(result)
        
        return results
    
    @abstractmethod
    def get_evaluator_name(self) -> str:
        """
        Get the name of this evaluator.
        
        Returns:
            String identifier for this evaluator
        """
        pass
    
    def validate_inputs(
        self,
        summary: str,
        entities: Dict[str, str]
    ) -> bool:
        """
        Validate that inputs are in correct format.
        
        Args:
            summary: The summary text
            entities: Dictionary of entities
            
        Returns:
            True if valid, False otherwise
        """
        if not summary or not isinstance(summary, str):
            return False
        
        if not entities or not isinstance(entities, dict):
            return False
        
        return True
