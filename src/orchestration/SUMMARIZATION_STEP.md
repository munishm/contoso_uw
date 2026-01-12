# Summarization Workflow Step

## Overview

The **Summarization** step is a new addition to the case processing workflow that generates natural language summaries from extracted entities. It runs after the extraction step and produces human-readable summaries of document data.

## Workflow Position

```
Classification → File Upload → DB Update → Extraction → Summarization
```

The summarization step:
- **Input**: Extracted entities from the extraction step
- **Processing**: Converts structured entity data into natural language summaries using Azure OpenAI
- **Output**: Generated summaries with metadata

## How It Works

### 1. Data Flow

```python
# Extraction Step Output (Input to Summarization)
{
    "extracted_entities": [
        {
            "document_type": "Application Form",
            "file_path": "/path/to/application.pdf",
            "extraction_result": {
                "status": "success",
                "entities": [
                    {"type": "Applicant Name", "value": "Ms LOK WING CHING"},
                    {"type": "Job Title", "value": "DIRECTOR"},
                    {"type": "Height", "value": "174 cm"},
                    {"type": "Weight", "value": "77 kg"}
                ]
            },
            "status": "success"
        }
    ]
}

# Summarization Step Output
{
    "summaries": [
        {
            "document_type": "Application Form",
            "summary": "The applicant, Ms. Lok Wing Ching, is currently employed as a Director. Ms. Lok's height is recorded as 174 cm and her weight is 77 kg.",
            "metadata": {
                "entity_count": 4,
                "summary_length": 150,
                "summary_words": 28,
                "temperature": 0.0,
                "model": "gpt-4.1"
            },
            "status": "success"
        }
    ],
    "summarization_status": "success"
}
```

### 2. Entity Loading from Evaluation Data

The summarization step is compatible with the evaluation data format used in `evaluations/notebooks/data/label.json`:

```json
[
    {
        "page_number": 1,
        "entity_presence": {
            "Applicant Name": true
        },
        "entity_value": {
            "Applicant Name": "Ms LOK WING CHING"
        },
        "chinese_entity_value": {
            "Applicant Name": "林詠菁"
        }
    }
]
```

The `EntityLoader` utility extracts English entity values from this format:

```python
from src.document_summarization.utils.entity_loader import EntityLoader

# Load and extract entities
entities = EntityLoader.load_and_extract("path/to/labels.json")
# Returns: {"Applicant Name": "Ms LOK WING CHING", ...}
```

### 3. SummarizationProcessor

The `SummarizationProcessor` is the workflow component that handles summarization:

```python
class SummarizationProcessor(IDocumentProcessor):
    """
    Processor that generates natural language summaries from extracted entities.
    
    Flow:
    1. Receives extraction results from previous step
    2. Extracts entity data from each extraction result
    3. Calls SummarizationService to generate summaries
    4. Returns summaries with metadata
    """
```

**Key Features:**
- Handles multiple document types in a single workflow run
- Skips documents where extraction failed
- Continues workflow even if summarization fails (skip_on_error: true)
- Uses Azure OpenAI via SummarizationService

## Configuration

### Workflow Configuration

The summarization step is included in the default workflow:

```python
{
    "name": "summarization",
    "type": "summarization",
    "component": "summarizer",
    "inputs": {
        "extracted_entities": None,  # From extraction step
        "classification_response": None  # Passed through
    },
    "outputs": ["summaries", "summarization_status"],
    "enabled": True,
    "skip_on_error": True  # Continue even if summarization fails
}
```

### Environment Variables

Required Azure OpenAI configuration:

```bash
GPT_4_1_API_ENDPOINT=https://your-endpoint.openai.azure.com/
GPT_4_1_API_DEPLOYMENT=gpt-4-deployment-name
GPT_4_1_API_VERSION=2024-02-15-preview
```

## Usage Examples

### Example 1: Using in Workflow

```python
from src.orchestration.case_workflow import on_new_case_created_async

# The workflow automatically includes summarization
results = await on_new_case_created_async(
    document_path="/path/to/document.pdf",
    case_id="CASE-12345"
)

# Access summarization results
summaries = results["results"]["summarization"]["summaries"]
for summary_data in summaries:
    print(f"Document Type: {summary_data['document_type']}")
    print(f"Summary: {summary_data['summary']}")
    print(f"Status: {summary_data['status']}")
```

### Example 2: Standalone Summarization

```python
from src.document_summarization.summarization_service import SummarizationService
from src.document_summarization.utils.entity_loader import EntityLoader
from azure.identity import DefaultAzureCredential
import os

# Load entities from evaluation data
entities = EntityLoader.load_and_extract("evaluations/notebooks/data/labels.json")

# Initialize service
service = SummarizationService(
    azure_endpoint=os.getenv("GPT_4_1_API_ENDPOINT"),
    deployment_name=os.getenv("GPT_4_1_API_DEPLOYMENT"),
    api_version=os.getenv("GPT_4_1_API_VERSION"),
    credential=DefaultAzureCredential(),
    temperature=0.0,
    max_tokens=5000
)

# Generate summary
result = service.generate_summary(
    entities=entities,
    context="Insurance Application Form"
)

print(result["summary"])
```

### Example 3: Running the Demo

```bash
# Run the example script
cd src/orchestration/examples
python summarization_example.py
```

This demonstrates:
- Loading entities from evaluation data
- Generating summaries
- Expected data formats

## Integration with test_summary Notebook

The summarization step follows the pattern from `src/document_summarization/notebooks/test_summary.ipynb`:

1. **Load Entities**: Uses `EntityLoader.load_and_extract()` to load from label.json
2. **Initialize Service**: Creates `SummarizationService` with Azure OpenAI config
3. **Generate Summary**: Calls `service.generate_summary(entities, context)`
4. **Save Results**: Optionally saves summaries to files

The key difference is that the workflow version:
- Receives entities from the extraction step (not from files)
- Processes multiple documents in batch
- Integrates with the overall case processing flow

## Error Handling

The summarization step includes robust error handling:

1. **Skip Failed Extractions**: Only processes documents with successful extraction
2. **Continue on Error**: Workflow continues even if summarization fails (skip_on_error: true)
3. **Detailed Logging**: All steps are logged for debugging
4. **Status Tracking**: Each summary has a status field (success/failed/skipped)

Example error scenarios:

```python
# Extraction failed - summarization skipped
{
    "status": "skipped",
    "reason": "Extraction status was failed"
}

# Azure config missing - summarization failed
{
    "status": "failed",
    "error_message": "Azure OpenAI configuration missing"
}

# No entities found - summarization failed
{
    "status": "failed",
    "error_message": "No entities found in extraction result"
}
```

## Testing

### Unit Testing

Test the SummarizationProcessor independently:

```python
from src.orchestration.case_workflow import SummarizationProcessor

processor = SummarizationProcessor()

# Test input
inputs = {
    "extracted_entities": [
        {
            "document_type": "Application Form",
            "extraction_result": {
                "entities": [
                    {"type": "Name", "value": "John Doe"}
                ]
            },
            "status": "success"
        }
    ]
}

# Process
result = processor.process(inputs)

# Verify output
assert "summaries" in result
assert result["summarization_status"] in ["success", "failed"]
```

### Integration Testing

Test the full workflow:

```python
from src.orchestration.case_workflow import workflow_manager, initialize_case_workflow

# Initialize workflow
initialize_case_workflow()

# Execute with real document
results = workflow_manager.execute_workflow(
    "case_processing",
    {"document": {"path": "test_document.pdf"}, "case_id": "TEST-001"}
)

# Verify summarization ran
assert "summarization" in results["results"]
summaries = results["results"]["summarization"]["summaries"]
assert len(summaries) > 0
```

## Performance Considerations

- **Batch Processing**: Multiple documents are summarized in a single workflow run
- **Async Compatible**: Runs in thread pool when called from async context
- **Caching**: Entity extraction results are reused (not re-extracted)
- **Token Usage**: Summary length controlled by max_tokens parameter (default: 5000)

## Monitoring and Logging

All summarization activities are logged with the following levels:

- **INFO**: Step progress, entity counts, summary lengths
- **WARNING**: Missing configuration, no entities found
- **ERROR**: Summarization failures, import errors

Example log output:

```
INFO - ############################################################
INFO - STEP 5: SUMMARIZATION - INPUT RECEIVED
INFO - ############################################################
INFO - Processing summarization for Application Form
INFO -   Extracted 5 entities for summarization
INFO -   ✓ Summary generated for Application Form
INFO -     Summary length: 192 chars
INFO - --------------------------------------------------
INFO - SUMMARIZATION COMPLETE: 1 summaries generated, 0 failed/skipped
INFO - ==================================================
```

## Future Enhancements

Potential improvements for the summarization step:

1. **Customizable Templates**: Allow template-based summaries for different document types
2. **Multi-language Support**: Generate summaries in multiple languages
3. **Summary Persistence**: Save summaries to database or blob storage
4. **Evaluation Metrics**: Track summary quality metrics (readability, accuracy)
5. **Caching**: Cache summaries to avoid regenerating for identical entity sets
6. **Streaming**: Support streaming responses for long summaries

## Troubleshooting

### Common Issues

**1. "Azure OpenAI configuration missing"**
- Ensure environment variables are set: GPT_4_1_API_ENDPOINT, GPT_4_1_API_DEPLOYMENT, GPT_4_1_API_VERSION
- Load .env file with `load_dotenv()`

**2. "No entities found in extraction result"**
- Check extraction step output format
- Verify entities are in expected format (list or dict)
- Review entity extraction logs

**3. "Import error: module not found"**
- Ensure all dependencies are installed
- Check Python path includes project root

**4. Authentication failures**
- Verify Azure AD credentials are configured
- Check DefaultAzureCredential() can authenticate
- Try `az login` if using Azure CLI

## References

- **Test Notebook**: `src/document_summarization/notebooks/test_summary.ipynb`
- **EntityLoader**: `src/document_summarization/utils/entity_loader.py`
- **SummarizationService**: `src/document_summarization/summarization_service.py`
- **Workflow Config**: `src/orchestration/case_workflow.py` (DEFAULT_CASE_WORKFLOW_CONFIG)
- **Example Data**: `src/evaluation/entity_extraction/notebooks/data/labels.json`
