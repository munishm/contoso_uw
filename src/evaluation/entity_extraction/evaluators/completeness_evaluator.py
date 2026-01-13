"""Completeness evaluator for entity extraction using LLM."""

import json
import logging
import traceback
from typing import Any, Dict, Optional
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from pydantic import BaseModel
from .base_evaluator import BaseEvaluator, EvaluationResult
from ..utils.text_utils import clean_text, normalize_value


logger = logging.getLogger(__name__)


class CompletenessAssessment(BaseModel):
    """Structured output from LLM completeness evaluation."""
    
    is_relevant: bool
    is_complete: bool
    missing_info: list[str]
    reasoning: str



class ExtractionCompletenessEvaluator(BaseEvaluator):
    """
    Evaluator that assesses completeness of extracted entities using Azure OpenAI.
    
    Uses GPT-4 Vision to determine if extracted entities are relevant and complete,
    and identifies any missing information.
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-08-01-preview",
        credential: Optional[DefaultAzureCredential] = None
    ):
        """
        Initialize the completeness evaluator.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            deployment_name: Name of the GPT-4 Vision deployment
            api_version: Azure OpenAI API version
            credential: Azure credential (defaults to DefaultAzureCredential)
        """
        logger.info("=" * 60)
        logger.info("COMPLETENESS EVALUATOR - Initializing")
        logger.info("=" * 60)
        logger.info(f"  Azure endpoint: {azure_endpoint}")
        logger.info(f"  Deployment name: {deployment_name}")
        logger.info(f"  API version: {api_version}")
        logger.info(f"  Credential provided: {credential is not None}")
        
        self.azure_endpoint = azure_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.credential = credential or DefaultAzureCredential()
        
        # Initialize Azure OpenAI client
        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
                azure_ad_token_provider=self._get_token_provider()
            )
            logger.info("  ✓ Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"  ✗ Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def _get_token_provider(self):
        """Create token provider for Azure AD authentication."""
        def token_provider():
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        return token_provider
    
    def _create_prompt(self, field_name: str, extracted_value: Any, source_text: str) -> str:
        """
        Create evaluation prompt for LLM.
        
        Args:
            field_name: Name of the field being evaluated
            extracted_value: The extracted value
            source_text: The source text
            
        Returns:
            Formatted prompt string
        """
        return f"""You are evaluating the completeness of an extracted entity from a document.

                **Field Name:** {field_name}
                **Extracted Value:** {extracted_value}

                **Source Text:**
                {source_text}

                Evaluate the extracted value against the source text and provide:
                1. **is_relevant**: Is the extracted value relevant to the field name? (true/false)
                2. **is_complete**: Does the extracted value contain all necessary information from the source? (true/false)
                3. **missing_info**: List any important information that is missing from the extracted value but present in the source (empty list if none)
                    - If only the chinese translation is missing, still consider it complete.
                4. **reasoning**: Brief explanation of your assessment

                Return your response as a JSON object with the following structure:
                {{
                    "is_relevant": true/false,
                    "is_complete": true/false,
                    "missing_info": ["item1", "item2", ...],
                    "reasoning": "Your explanation here"
                }}"""
    
    def _calculate_score(self, assessment: CompletenessAssessment) -> float:
        """
        Calculate numeric completeness score from assessment.
        
        Args:
            assessment: The completeness assessment from LLM
            
        Returns:
            Score between 0 and 1
        """
        # Start with base score
        score = 0.0
        
        # Relevance check (50% of score)
        if assessment.is_relevant:
            score += 0.5
        
        # Completeness check (50% of score)
        if assessment.is_complete:
            score += 0.5
        else:
            # Partial credit based on missing information count
            missing_count = len(assessment.missing_info)
            if missing_count == 0:
                score += 0.5
            elif missing_count == 1:
                score += 0.3
            elif missing_count == 2:
                score += 0.2
            else:
                score += 0.1
        
        return score
    
    def evaluate_field(
        self,
        field_name: str,
        extracted_value: Any,
        source_text: str,
        **kwargs
    ) -> EvaluationResult:
        """
        Evaluate completeness of extracted value using Azure OpenAI.
        
        Args:
            field_name: Name of the extracted field
            extracted_value: The extracted value to evaluate
            source_text: The source text from which the entity was extracted
            **kwargs: Additional parameters
                - temperature: LLM temperature (default: 0.0)
                - max_tokens: Maximum response tokens (default: 500)
            
        Returns:
            EvaluationResult with completeness score (0-1) and detailed metadata
        """
        logger.info(f"[Completeness] Evaluating field: {field_name}")
        logger.info(f"[Completeness]   Extracted value: {extracted_value}")
        logger.info(f"[Completeness]   Source text length: {len(source_text) if source_text else 0}")
        
        # Normalize inputs
        entity_value = normalize_value(extracted_value)
        cleaned_source = clean_text(source_text)
        
        logger.info(f"[Completeness]   Normalized value: {entity_value}")
        logger.info(f"[Completeness]   Cleaned source length: {len(cleaned_source) if cleaned_source else 0}")
        
        # Handle empty values
        if not entity_value:
            logger.warning(f"[Completeness]   Empty entity value - returning score 0")
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "reason": "Empty extracted value",
                    "is_relevant": False,
                    "is_complete": False,
                    "missing_info": ["No value extracted"]
                }
            )
        
        if not cleaned_source:
            logger.warning(f"[Completeness]   Empty source text - returning score 0")
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "reason": "Empty source text",
                    "is_relevant": False,
                    "is_complete": False,
                    "missing_info": ["No source text available"]
                }
            )
        
        # Create prompt
        prompt = self._create_prompt(field_name, entity_value, cleaned_source)
        
        # Get LLM parameters
        temperature = kwargs.get('temperature', 0.0)
        max_tokens = kwargs.get('max_tokens', 500)
        
        try:
            logger.info(f"[Completeness]   Calling Azure OpenAI for field '{field_name}'...")
            logger.info(f"[Completeness]   Model: {self.deployment_name}")
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at evaluating extracted entities for completeness and relevance. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            logger.info(f"[Completeness]   ✓ Azure OpenAI call successful")
            
            # Parse response
            content = response.choices[0].message.content
            logger.info(f"[Completeness]   Response: {content[:200]}..." if len(content) > 200 else f"[Completeness]   Response: {content}")
            
            assessment_dict = json.loads(content)
            assessment = CompletenessAssessment(**assessment_dict)
            
            # Calculate score
            score = self._calculate_score(assessment)
            logger.info(f"[Completeness]   Score: {score}, is_relevant: {assessment.is_relevant}, is_complete: {assessment.is_complete}")
            
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=score,
                metadata={
                    "is_relevant": assessment.is_relevant,
                    "is_complete": assessment.is_complete,
                    "missing_info": assessment.missing_info,
                    "reasoning": assessment.reasoning,
                    "llm_response": content
                }
            )
            
        except Exception as e:
            error_details = str(e)
            tb = traceback.format_exc()
            logger.error(f"COMPLETENESS EVALUATOR ERROR for field '{field_name}':")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Error message: {error_details}")
            logger.error(f"  Extracted value: {extracted_value}")
            logger.error(f"  Source text length: {len(cleaned_source) if cleaned_source else 0}")
            logger.error(f"  Traceback: {tb}")
            
            return EvaluationResult(
                field_name=field_name,
                entity_value=extracted_value,
                score=0.0,
                metadata={
                    "error": error_details,
                    "error_type": type(e).__name__,
                    "reason": "Failed to evaluate with LLM",
                    "is_relevant": False,
                    "is_complete": False,
                    "missing_info": ["Evaluation failed"]
                }
            )
