# LLM Client Integration Guide

## Overview

The `LLMClient` provides a unified interface for Azure OpenAI interactions with built-in token tracking, flexible authentication, and support for structured outputs.

## Key Features

- **Dual Authentication**: API key or Azure managed identity (DefaultAzureCredential)
- **Token Tracking**: Automatic logging of prompt, completion, and total tokens
- **Structured Output**: Pydantic schema support for type-safe responses
- **Multiple Formats**: Text, JSON, Markdown, or Pydantic output
- **Flexible Input**: Accept strings, dictionaries, lists, or pre-formatted messages
- **Error Handling**: Comprehensive exception handling with detailed logging

## Architecture

```
SummarizationService
    └── LLMSummarizer
        └── LLMClient
            └── AzureOpenAI
```

## Entry Points

### Using SummarizationService (Recommended)

High-level interface for document summarization:

```python
from document_summarization import SummarizationService, EntityLoader
from azure.identity import DefaultAzureCredential

# Load entities
entities = EntityLoader.load_and_extract("data/labels.json")

# Initialize service with token-based auth
service = SummarizationService(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4-deployment",
    api_version="2024-02-01",
    credential=DefaultAzureCredential(),
    temperature=0.3,
    max_tokens=1000
)

# Generate summary
result = service.generate_summary(
    entities=entities,
    context="Insurance Application Form"
)

print(result['summary'])
print(f"Tokens: {result['metadata']['total_tokens']}")
```

### Using LLMClient Directly

```python
from document_summarization.utils.llm_client import LLMClient

client = LLMClient(
    model_name="gpt-4",
    azure_endpoint=endpoint,
    azure_deployment=deployment,
    api_version=version,
    credential=DefaultAzureCredential(),
    system_prompt="You are a helpful assistant."
)

# Simple generation
response = client.generate_output(
    context="Your prompt here",
    output_format="text",
    temperature=0.3
)

# With token tracking
result = client.generate_output_with_token_count(
    context="Your prompt here",
    output_format="text"
)
print(result['output'])
print(f"Tokens: {result['total_tokens']}")
```

### Using LLMSummarizer

For programmatic summarization control:

```python
from document_summarization.summarizers import LLMSummarizer
from azure.identity import DefaultAzureCredential

summarizer = LLMSummarizer(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4-deployment",
    api_version="2024-02-01",
    credential=DefaultAzureCredential(),
    temperature=0.3,
    max_tokens=1000
)

result = summarizer.summarize(
    entities={"name": "John Doe", "age": "35"},
    context="Insurance Application"
)

print(result.summary)
print(result.metadata)
```

## Authentication Options

### Token-Based Authentication (Recommended)

Uses Azure managed identities or service principals:

```python
from azure.identity import DefaultAzureCredential

service = SummarizationService(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4",
    api_version="2024-02-01",
    credential=DefaultAzureCredential()
)
```

### Key-Based Authentication

For development or scenarios requiring API keys:

```python
service = SummarizationService(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4",
    api_version="2024-02-01",
    api_key="your-api-key-here"
)
```

## Token Usage Tracking

All LLM calls automatically log token usage:

```
INFO: LLM Token Usage - Prompt: 245, Completion: 189, Total: 434
DEBUG: LLM Metrics: {'prompt_tokens': 245, 'completion_tokens': 189, 'total_tokens': 434}
```

Access token counts in result metadata:

```python
result = service.generate_summary(entities=entities)
print(f"Prompt tokens: {result['metadata']['prompt_tokens']}")
print(f"Completion tokens: {result['metadata']['completion_tokens']}")
print(f"Total tokens: {result['metadata']['total_tokens']}")
```

## Best Practices

1. **Use Token-Based Auth in Production**: More secure and eliminates credential management
2. **Monitor Token Usage**: Track token consumption for cost optimization
3. **Set Appropriate max_tokens**: Balance between completeness and cost
4. **Use Lower Temperature for Consistency**: 0.0-0.3 for deterministic outputs
5. **Validate Entity Data**: Ensure entities are properly formatted before summarization

## See Also

- [LLMClient Usage Examples](llm_client_usage.md) - Detailed usage patterns and examples
- API Reference - Complete API documentation (coming soon)
