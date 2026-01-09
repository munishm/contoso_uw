import logging
from typing import Dict, Optional
from azure.identity import DefaultAzureCredential

from .base_summarizer import BaseSummarizer, SummaryResult
from ..utils.prompt_builder import PromptBuilder
from ..utils.llm_client import LLMClient


logger = logging.getLogger(__name__)


class LLMSummarizer(BaseSummarizer):
    """
    LLM-based document summarizer using Azure OpenAI.
    
    This summarizer generates natural language summaries from extracted
    entities using GPT models.
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str,
        credential: Optional[DefaultAzureCredential] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 5000
    ):
        """
        Initialize the LLM summarizer.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            deployment_name: Name of the GPT deployment
            api_version: API version to use
            credential: Azure credential for token-based auth (if None, will create DefaultAzureCredential)
            api_key: API key for key-based auth (optional, use either credential or api_key)
            temperature: Sampling temperature (0-1), lower for more consistent outputs
            max_tokens: Maximum tokens in the response
        """
        self.azure_endpoint = azure_endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize credential if not using API key
        if not api_key:
            credential = credential or DefaultAzureCredential()
        
        # Get system prompt
        prompt_builder = PromptBuilder()
        system_prompt = prompt_builder.get_system_prompt()
        
        # Initialize LLM client
        try:
            self.llm_client = LLMClient(
                model_name=deployment_name,
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                azure_deployment=deployment_name,
                api_version=api_version,
                credential=credential,
                system_prompt=system_prompt
            )
            logger.info(f"LLM Summarizer initialized with deployment: {deployment_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
    def validate_entities(self, entities: Dict[str, str]) -> bool:
        """
        Validate that entities dictionary is properly formatted.
        
        Args:
            entities: Dictionary of entity names and values
            
        Returns:
            True if valid, False otherwise
        """
        if not entities:
            logger.warning("Empty entities dictionary provided")
            return False
        
        if not isinstance(entities, dict):
            logger.warning("Entities must be a dictionary")
            return False
        
        # Check that all values are strings
        for key, value in entities.items():
            if not isinstance(key, str) or not isinstance(value, str):
                logger.warning(f"Invalid entity format: {key}={value}")
                return False
            if not value.strip():
                logger.warning(f"Empty value for entity: {key}")
                return False
        
        return True
    
    def summarize(
        self,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> SummaryResult:
        """
        Generate a natural language summary using Azure OpenAI.
        
        Args:
            entities: Dictionary of entity names and values
            context: Optional additional context or document type
            **kwargs: Additional parameters (e.g., custom_instructions)
            
        Returns:
            SummaryResult with generated summary and metadata
        """
        try:
            # Validate entities
            if not self.validate_entities(entities):
                return SummaryResult(
                    summary="",
                    success=False,
                    error_message="Invalid entities provided",
                    metadata={"entity_count": len(entities) if entities else 0}
                )
            
            # Build the prompt
            prompt_builder = PromptBuilder()
            prompt = prompt_builder.build_summary_prompt(
                entities=entities,
                context=context,
                custom_instructions=kwargs.get("custom_instructions")
            )
            
            logger.info(f"Generating summary for {len(entities)} entities...")
            
            # Prepare messages for LLM client
            messages = [
                {
                    "role": "system",
                    "content": prompt_builder.get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Call LLM client with token tracking
            result = self.llm_client.generate_output_with_token_count(
                messages=messages,
                output_format="text",
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
            
            # Extract summary and tokens
            summary_text = result["output"].strip()
            prompt_tokens = result["prompt_tokens"]
            completion_tokens = result["completion_tokens"]
            total_tokens = result["total_tokens"]
            
            # Prepare metadata
            metadata = {
                "entity_count": len(entities),
                "summary_length": len(summary_text),
                "summary_words": len(summary_text.split()),
                "temperature": kwargs.get("temperature", self.temperature),
                "model": kwargs.get("model", self.deployment_name),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            
            logger.info(f"Summary generated successfully ({len(summary_text)} characters)")
            
            return SummaryResult(
                summary=summary_text,
                success=True,
                metadata=metadata
            )
            
        except Exception as e:
            error_msg = f"Error generating summary: {str(e)}"
            logger.error(error_msg)
            return SummaryResult(
                summary="",
                success=False,
                error_message=error_msg,
                metadata={"entity_count": len(entities) if entities else 0}
            )
