import json
import logging
import os
from typing import Dict, Optional
from azure.identity import DefaultAzureCredential

from .summarizers.llm_summarizer import LLMSummarizer
from .summarizers.base_summarizer import SummaryResult


logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Unified service for document summarization.
    
    This service provides a high-level interface for generating summaries
    from extracted entities using various summarization strategies.
    """
    
    def __init__(
        self,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str,
        credential: Optional[DefaultAzureCredential] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ):
        """
        Initialize the summarization service.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            deployment_name: Name of the GPT deployment
            api_version: API version to use
            credential: Azure credential for token-based auth (if None, will create DefaultAzureCredential)
            api_key: API key for key-based auth (optional, use either credential or api_key)
            temperature: Sampling temperature for LLM
            max_tokens: Maximum tokens in response
        """
        try:
            self.llm_summarizer = LLMSummarizer(
                azure_endpoint=azure_endpoint,
                deployment_name=deployment_name,
                api_version=api_version,
                credential=credential,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info("SummarizationService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SummarizationService: {e}")
            raise
    
    def generate_summary(
        self,
        entities: Dict[str, str],
        context: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Generate a summary from extracted entities.
        
        Args:
            entities: Dictionary of entity names and values
            context: Optional document context
            **kwargs: Additional parameters passed to summarizer
            
        Returns:
            Dictionary containing summary, metadata, and status
        """
        try:
            # Generate summary
            result = self.llm_summarizer.summarize(
                entities=entities,
                context=context,
                **kwargs
            )
            
            # Convert to dictionary format
            return {
                "summary": result.summary,
                "success": result.success,
                "error_message": result.error_message,
                "metadata": result.metadata
            }
            
        except Exception as e:
            logger.error(f"Error in generate_summary: {e}")
            return {
                "summary": "",
                "success": False,
                "error_message": str(e),
                "metadata": {"entity_count": len(entities) if entities else 0}
            }
    
    def save_summary(
        self,
        summary: str,
        entities: Dict[str, str],
        output_dir: str = "output",
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Save summary and entities to files.
        
        Args:
            summary: The generated summary text
            entities: Dictionary of extracted entities
            output_dir: Directory to save output files
            metadata: Optional metadata to include in JSON
            
        Returns:
            Dictionary with paths to saved files
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Save summary as text file
            summary_path = os.path.join(output_dir, "application_summary.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Summary saved to: {summary_path}")
            
            # Save entities and summary as JSON
            json_path = os.path.join(output_dir, "summarization_results.json")
            results = {
                "summary": summary,
                "extracted_entities": entities,
                "metadata": metadata or {
                    "total_entities": len(entities),
                    "summary_length": len(summary),
                    "summary_words": len(summary.split())
                }
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {json_path}")
            
            return {
                "summary_file": summary_path,
                "json_file": json_path
            }
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
    
    @staticmethod
    def to_json(result: Dict, indent: int = 2) -> str:
        """
        Convert result dictionary to JSON string.
        
        Args:
            result: Result dictionary from generate_summary
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        try:
            return json.dumps(result, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            raise
