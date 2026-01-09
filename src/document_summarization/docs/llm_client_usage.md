# LLMClient Usage Examples

This document demonstrates various ways to use the `LLMClient` for Azure OpenAI interactions.

## Basic Setup

### Token-based Authentication (Recommended for Production)
```python
from azure.identity import DefaultAzureCredential
from document_summarization.utils.llm_client import LLMClient

# Initialize with token-based auth
client = LLMClient(
    model_name="gpt-4",
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="gpt-4-deployment",
    api_version="2024-02-01",
    credential=DefaultAzureCredential(),
    system_prompt="You are a helpful AI assistant."
)
```

### Key-based Authentication
```python
from document_summarization.utils.llm_client import LLMClient

# Initialize with API key
client = LLMClient(
    model_name="gpt-4",
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="gpt-4-deployment",
    api_version="2024-02-01",
    api_key="your-api-key",
    system_prompt="You are a helpful AI assistant."
)
```

## Simple Text Generation

```python
# Generate response from text context
response = client.generate_output(
    context="What is the capital of France?",
    output_format="text",
    temperature=0.3,
    max_tokens=100
)

print(response)
# Output: "The capital of France is Paris."
```

## Generation with Token Tracking

```python
# Get response with token usage statistics
result = client.generate_output_with_token_count(
    context="Explain quantum computing in simple terms.",
    output_format="text",
    temperature=0.5,
    max_tokens=200
)

print(f"Response: {result['output']}")
print(f"Prompt tokens: {result['prompt_tokens']}")
print(f"Completion tokens: {result['completion_tokens']}")
print(f"Total tokens: {result['total_tokens']}")
```

## Using Dictionary Context

```python
# Pass context as dictionary
context = {
    "name": "John Doe",
    "age": 35,
    "occupation": "Software Engineer",
    "hobbies": ["reading", "hiking", "coding"]
}

response = client.generate_output(
    context=context,
    metadata={"task": "Generate a professional bio"},
    output_format="text",
    temperature=0.7
)

print(response)
```

## Custom Messages Format

```python
# Use pre-formatted messages for more control
messages = [
    {"role": "system", "content": "You are a medical documentation assistant."},
    {"role": "user", "content": "Summarize this patient record: Age 45, BP 120/80, no allergies."}
]

response = client.generate_output(
    messages=messages,
    output_format="text",
    temperature=0.3,
    max_tokens=150
)

print(response)
```

## Structured Output with Pydantic Schema

```python
from pydantic import BaseModel
from typing import List

# Define schema
class PatientSummary(BaseModel):
    name: str
    age: int
    conditions: List[str]
    medications: List[str]

# Generate structured output
result = client.generate_output_with_token_count(
    context={
        "patient_name": "Jane Smith",
        "patient_age": 42,
        "diagnosis": "Type 2 Diabetes, Hypertension",
        "current_medications": "Metformin, Lisinopril"
    },
    schema=PatientSummary,
    output_format="json",
    temperature=0.0
)

# Access structured data
patient_data = result['output']
print(f"Patient: {patient_data['name']}, Age: {patient_data['age']}")
print(f"Conditions: {', '.join(patient_data['conditions'])}")
```

## Markdown Output Format

```python
# Request markdown-formatted output
response = client.generate_output(
    context="Create a comparison table of Python vs JavaScript",
    output_format="markdown",
    temperature=0.5,
    max_tokens=500
)

print(response)
# Output will have properly formatted markdown with tables, headers, etc.
```

## Advanced Parameters

```python
# Use advanced sampling parameters
response = client.generate_output_with_token_count(
    context="Write a creative story about a time traveler",
    output_format="text",
    temperature=0.8,        # Higher temperature for more creativity
    max_tokens=500,
    top_p=0.9,             # Nucleus sampling
    frequency_penalty=0.5,  # Reduce repetition
    presence_penalty=0.3    # Encourage diverse topics
)

print(response['output'])
```

## Integration with Summarization Service

The `LLMClient` is already integrated into the `LLMSummarizer`:

```python
from document_summarization import SummarizationService, EntityLoader
from azure.identity import DefaultAzureCredential

# Load entities
entities = EntityLoader.load_and_extract("data/labels.json")

# Initialize service (uses LLMClient internally)
service = SummarizationService(
    azure_endpoint="https://your-resource.openai.azure.com",
    deployment_name="gpt-4-deployment",
    api_version="2024-02-01",
    credential=DefaultAzureCredential(),  # Token-based auth
    # OR
    # api_key="your-api-key",  # Key-based auth
    temperature=0.3,
    max_tokens=1000
)

# Generate summary (automatically tracks tokens)
result = service.generate_summary(
    entities=entities,
    context="Insurance Application Form"
)

print(result['summary'])
print(f"Tokens used: {result['metadata']['total_tokens']}")
```

## Error Handling

```python
try:
    result = client.generate_output_with_token_count(
        context="Your context here",
        output_format="text",
        max_tokens=100
    )
    
    print(result['output'])
    
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Error during generation: {e}")
```

## Benefits of Using LLMClient

1. **Unified Interface**: Single client for all Azure OpenAI interactions
2. **Flexible Authentication**: Supports both API key and token-based auth
3. **Token Tracking**: Automatic token usage logging and metrics
4. **Structured Output**: Pydantic schema support for type-safe responses
5. **Multiple Formats**: Text, JSON, Markdown output options
6. **Comprehensive Logging**: Built-in logging for debugging
7. **Error Handling**: Graceful error handling with detailed messages
8. **Reusable**: Can be used across different parts of the application
