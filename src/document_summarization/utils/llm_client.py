import json
import logging
import re
from typing import Optional, Union, Type, TypeVar, Literal, List, Dict, Any, Callable
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel


logger = logging.getLogger(__name__)


def get_llm_client_instance(
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    api_version: Optional[str] = None,
    azure_deployment: Optional[str] = None,
    azure_ad_token_provider: Optional[Callable[[], str]] = None,
) -> AzureOpenAI:
    """
    Create an Azure OpenAI client instance.
    
    Args:
        api_key: Azure OpenAI API key (for key-based auth)
        azure_endpoint: Azure OpenAI endpoint URL
        api_version: API version to use
        azure_deployment: Deployment name
        azure_ad_token_provider: Callable that returns Azure AD token (for token-based auth)
        
    Returns:
        AzureOpenAI client instance
    """
    if azure_ad_token_provider:
        # Token-based authentication
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            azure_ad_token_provider=azure_ad_token_provider,
        )
    else:
        # Key-based authentication
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )

    return client


T = TypeVar("T", bound=BaseModel)
ContextInput = Union[str, Dict[Any, Any], List[Dict[Any, Any]]]
OutputFormat = Literal["text", "markdown", "json", "pydantic"]


class LLMClient:
    """
    Unified client for Azure OpenAI LLM interactions.
    
    Supports both key-based and token-based authentication,
    structured output with Pydantic schemas, and comprehensive
    token usage tracking.
    """
    
    def __init__(
        self,
        model_name: str,
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        client: Optional[AzureOpenAI] = None,
        system_prompt: Optional[str] = None,
        credential: Optional[DefaultAzureCredential] = None,
    ) -> None:
        """
        Initialize the LLM client.
        
        Args:
            model_name: Name of the model to use
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: API key for authentication (optional if using token)
            azure_deployment: Deployment name
            api_version: API version
            client: Pre-configured AzureOpenAI client (optional)
            system_prompt: Default system prompt
            credential: Azure credential for token-based auth (optional)
        """
        # Set up token provider if using credential
        azure_ad_token_provider = None
        if credential:
            def get_azure_ad_token():
                return credential.get_token("https://cognitiveservices.azure.com/.default").token
            azure_ad_token_provider = get_azure_ad_token
        
        self.client = client or get_llm_client_instance(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            azure_deployment=azure_deployment,
            azure_ad_token_provider=azure_ad_token_provider,
        )
        
        self.model_name = model_name
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        
        logger.info(f"LLMClient initialized with model: {model_name}")

    def generate_output(
        self,
        context: Optional[ContextInput] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        schema: Optional[Type[T]] = None,
        metadata: Optional[dict] = None,
        output_format: OutputFormat = "json",
        max_tokens: int = 32768,
        temperature: float = 0.0,
        top_p: float = 1.0,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
    ) -> Union[str, T]:
        """
        Generate output from the LLM.
        
        Args:
            context: Context as string, dict, or list of dicts
            messages: Pre-formatted messages (if provided, context is ignored)
            schema: Pydantic model for structured output
            metadata: Additional metadata to include in prompt
            output_format: Format of output ("text", "markdown", "json", "pydantic")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            
        Returns:
            Generated output as string or Pydantic model
        """
        # Build messages if not provided
        if messages is None:
            messages = self._build_messages(context, metadata)

        # Generate with schema if provided
        if schema:
            response = self.client.beta.chat.completions.parse(
                messages=messages,
                model=self.model_name,
                response_format=schema,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            parsed = response.choices[0].message.parsed

            if output_format == "json":
                return json.loads(parsed.model_dump_json())
            
            return parsed

        # Generate without schema
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )

            raw_text = response.choices[0].message.content
        
            if output_format == "markdown":
                raw_text = re.sub(r'\\n', '\n', raw_text)
                raw_text = re.sub(r'\\t', '\t', raw_text)

            return raw_text

    def generate_output_with_token_count(
        self,
        context: Optional[ContextInput] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        schema: Optional[Type[T]] = None,
        metadata: Optional[dict] = None,
        output_format: OutputFormat = "json",
        max_tokens: int = 32768,
        temperature: float = 0.0,
        top_p: float = 1.0,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
    ) -> Dict[str, Union[str, T, int]]:
        """
        Generate output with token usage statistics.
        
        Args:
            context: Context as string, dict, or list of dicts
            messages: Pre-formatted messages (if provided, context is ignored)
            schema: Pydantic model for structured output
            metadata: Additional metadata to include in prompt
            output_format: Format of output ("text", "markdown", "json", "pydantic")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            
        Returns:
            Dictionary with output, prompt_tokens, completion_tokens, total_tokens
        """
        # Build messages if not provided
        if messages is None:
            messages = self._build_messages(context, metadata)

        # Generate with schema if provided
        if schema:
            response = self.client.beta.chat.completions.parse(
                messages=messages,
                model=self.model_name,
                response_format=schema,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            parsed = response.choices[0].message.parsed

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            if output_format == "json":
                parsed = json.loads(parsed.model_dump_json())
                
            self._log_llm_metrics(prompt_tokens, completion_tokens, total_tokens)

            return {
                "output": parsed,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }

        # Generate without schema
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )

            raw_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
        
            if output_format == "markdown":
                raw_text = re.sub(r'\\n', '\n', raw_text)
                raw_text = re.sub(r'\\t', '\t', raw_text)
            
            self._log_llm_metrics(prompt_tokens, completion_tokens, total_tokens)
            
            return {
                "output": raw_text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }

    def _build_messages(
        self,
        context: Optional[ContextInput],
        metadata: Optional[dict] = None
    ) -> List[Dict[str, str]]:
        """
        Build messages list from context and metadata.
        
        Args:
            context: Context input
            metadata: Additional metadata
            
        Returns:
            List of message dictionaries
        """
        if context is None:
            raise ValueError("Either 'context' or 'messages' must be provided.")
        
        # Convert context to text
        if isinstance(context, str):
            context_text = context
        else:
            context_text = json.dumps(context, indent=2)

        # Add metadata if provided
        metadata_text = (
            "\n".join(f"{k}: {v}" for k, v in metadata.items()) if metadata else ""
        )

        user_input = f"Context:\n{context_text}\n{metadata_text}".strip()

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
    
    def _log_llm_metrics(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> None:
        """
        Log LLM token usage metrics.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total number of tokens
        """
        metrics = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        
        logger.info(f"LLM Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        logger.debug(f"LLM Metrics: {metrics}")
