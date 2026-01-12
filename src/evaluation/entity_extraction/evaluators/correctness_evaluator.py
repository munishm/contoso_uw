from typing import Any
from rapidfuzz import fuzz
from .base_evaluator import BaseEvaluator, EvaluationResult
from ..utils.text_utils import clean_text, normalize_value



class ExtractionCorrectnessEvaluator(BaseEvaluator):
    """
    Evaluator that computes fuzzy similarity between extracted entities and OCR text from Azure Document Intelligence.
    
    Returns the fuzzy token set ratio score (0-1). Extraction is considered correct only if score is 1.0,
    indicating the extracted value is exactly present in the source text.
    """
    
    def __init__(self):
        """Initialize the fuzzy similarity evaluator."""
        pass
    
    def evaluate_field(
        self,
        field_name: str,
        extracted_value: Any,
        source_text: str,
        **kwargs
    ) -> EvaluationResult:
        """
        Check if extracted value is present in the OCR source text.
        
        Args:
            field_name: Name of the extracted field
            extracted_value: The extracted value to evaluate
         ompute fuzzy similarity between extracted value and OCR source text.
        
        Args:
            field_name: Name of the extracted field
            extracted_value: The extracted value to evaluate
            source_text: The OCR text from Azure Document Intelligence
            **kwargs: Additional parameters (unused)
            
        Returns:
            EvaluationResult with fuzzy similarity score (0-1) and metadata indicating if extraction is correct
        """
        # Normalize inputs
        entity_value = normalize_value(extracted_value)
        cleaned_source = clean_text(source_text)
        
        # Handle empty values
        if not entity_value:
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "fuzzy_score": 0.0,
                    "extraction_correct": False,
                    "reason": "Empty extracted value"
                }
            )
        
        if not cleaned_source:
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "fuzzy_score": 0.0,
                    "extraction_correct": False,
                    "reason": "Empty source text"
                }
            )
        
        # Compute fuzzy similarity using token set ratio
        # This is robust to word order and partial matches
        fuzzy_score = fuzz.token_set_ratio(entity_value, cleaned_source) / 100.0
        
        # Extraction is correct only if fuzzy score is exactly 1.0
        extraction_correct = fuzzy_score == 1.0
        
        return EvaluationResult(
            field_name=field_name,
            entity_value=extracted_value,
            score=fuzzy_score,
            metadata={
                "fuzzy_score": fuzzy_score,
                "extraction_correct": extraction_correct,
                "normalized_entity": entity_value,
                "cleaned_source_length": len(cleaned_source)
            }
        )
