from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel



class EvaluationResult(BaseModel):
    """Base evaluation result model."""
    
    field_name: str
    entity_value: Any
    score: float
    metadata: Dict[str, Any] = {}



class BaseEvaluator(ABC):
    """Abstract base class for entity extraction evaluators."""
    
    @abstractmethod
    def evaluate_field(
        self,
        field_name: str,
        extracted_value: Any,
        source_text: str,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate a single extracted field.
        
        Args:
            field_name: Name of the extracted field
            extracted_value: The extracted value to evaluate
            source_text: The source text from which the entity was extracted
            **kwargs: Additional evaluator-specific parameters
            
        Returns:
            EvaluationResult with score and metadata
        """
        pass
    
    def evaluate_batch(
        self,
        fields: List[Dict[str, Any]],
        source_text: str,
        **kwargs
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple fields in batch.
        
        Args:
            fields: List of dicts with 'field_name' and 'value' keys
            source_text: The source text from which entities were extracted
            **kwargs: Additional evaluator-specific parameters
            
        Returns:
            List of EvaluationResult objects
        """
        return [
            self.evaluate_field(
                field_name=field['field_name'],
                extracted_value=field['value'],
                source_text=source_text,
                **kwargs
            )
            for field in fields
        ]
