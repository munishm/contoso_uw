# Summarization Step - Quick Start Guide

## Overview

The **Summarization** step has been added to the case processing workflow. It generates natural language summaries from extracted entities.

## Workflow Steps

```
1. Classification  → Identifies document types
2. File Upload     → Prepares files for storage
3. DB Update       → Prepares database records
4. Extraction      → Extracts entities from documents
5. Summarization   → Generates natural language summaries ✨ NEW!
```

## Quick Example

### Using the Full Workflow

```python
from src.orchestration.case_workflow import on_new_case_created_async

# Process a document (includes summarization automatically)
results = await on_new_case_created_async(
    document_path="/path/to/application.pdf",
    case_id="CASE-12345"
)

# Access summarization results
summarization_results = results["results"]["summarization"]
summaries = summarization_results["summaries"]

for summary_data in summaries:
    print(f"Document: {summary_data['document_type']}")
    print(f"Summary: {summary_data['summary']}")
    print(f"Status: {summary_data['status']}")
    print("-" * 50)
```

### Standalone Summarization

```python
from src.document_summarization.summarization_service import SummarizationService
from src.document_summarization.utils.entity_loader import EntityLoader
from azure.identity import DefaultAzureCredential
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Method 1: Load from evaluation data (labels.json format)
entities = EntityLoader.load_and_extract("evaluations/notebooks/data/labels.json")

# Method 2: Or use a dict directly
entities = {
    "Applicant Name": "Ms LOK WING CHING",
    "Job Title": "DIRECTOR",
    "Height": "174 cm",
    "Weight": "77 kg"
}

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

if result["success"]:
    print(result["summary"])
    print(f"\nMetadata: {result['metadata']}")
else:
    print(f"Error: {result['error_message']}")
```

## Input Data Format

### Evaluation Data Format (labels.json)

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
        "chinese_entity_value": {}
    },
    {
        "page_number": 2,
        "entity_presence": {
            "Job Title of Applicant": true
        },
        "entity_value": {
            "Job Title of Applicant": "DIRECTOR"
        }
    }
]
```

### Workflow Extraction Output Format

```python
{
    "extracted_entities": [
        {
            "document_type": "Application Form",
            "file_path": "/path/to/doc.pdf",
            "extraction_result": {
                "entities": [
                    {"type": "Applicant Name", "value": "Ms LOK WING CHING"},
                    {"type": "Job Title", "value": "DIRECTOR"}
                ]
            },
            "status": "success"
        }
    ]
}
```

## Configuration

### Required Environment Variables

```bash
# .env file
GPT_4_1_API_ENDPOINT=https://your-endpoint.openai.azure.com/
GPT_4_1_API_DEPLOYMENT=gpt-4-deployment-name
GPT_4_1_API_VERSION=2024-02-15-preview
```

### Workflow Configuration

The summarization step is enabled by default in `DEFAULT_CASE_WORKFLOW_CONFIG`:

```python
{
    "name": "summarization",
    "type": "summarization",
    "component": "summarizer",
    "inputs": {
        "extracted_entities": None,
        "classification_response": None
    },
    "outputs": ["summaries", "summarization_status"],
    "enabled": True,
    "skip_on_error": True  # Workflow continues even if summarization fails
}
```

### Disabling Summarization

To disable the summarization step:

```python
from src.orchestration.case_workflow import workflow_manager, WorkflowConfig

# Load workflow and modify
config = WorkflowConfig.from_dict(DEFAULT_CASE_WORKFLOW_CONFIG)

# Disable summarization step
for step in config.steps:
    if step.name == "summarization":
        step.enabled = False

# Load modified config
workflow_manager.load_workflow_config(config)
```

## Output Format

### Successful Summarization

```python
{
    "summaries": [
        {
            "document_type": "Application Form",
            "file_path": "/path/to/application.pdf",
            "summary": "The applicant, Ms. Lok Wing Ching, is currently employed as a Director. Ms. Lok's height is recorded as 174 cm and her weight is 77 kg.",
            "metadata": {
                "entity_count": 4,
                "summary_length": 150,
                "summary_words": 28,
                "temperature": 0.0,
                "model": "gpt-4.1",
                "prompt_tokens": 204,
                "completion_tokens": 49,
                "total_tokens": 253
            },
            "status": "success",
            "error_message": null
        }
    ],
    "summarization_status": "success"
}
```

### Failed/Skipped Summarization

```python
{
    "summaries": [
        {
            "document_type": "Application Form",
            "file_path": "/path/to/application.pdf",
            "summary": null,
            "status": "skipped",
            "reason": "Extraction status was failed"
        }
    ],
    "summarization_status": "failed"
}
```

## Running Examples

### Example 1: Demo Script

```bash
cd src/orchestration/examples
python summarization_example.py
```

This runs a complete demo showing:
- Loading entities from evaluation data
- Generating summaries
- Expected data formats

### Example 2: Test Notebook

Open the test_summary notebook to see the original implementation:

```bash
jupyter notebook src/document_summarization/notebooks/test_summary.ipynb
```

## Common Use Cases

### Case 1: Summarize Evaluation Results

```python
from src.document_summarization.utils.entity_loader import EntityLoader
from src.document_summarization.summarization_service import SummarizationService

# Load entities from evaluation labels
entities = EntityLoader.load_and_extract(
    "evaluations/notebooks/data/labels.json"
)

# Initialize and generate
service = SummarizationService(...)  # See full example above
result = service.generate_summary(entities, "Application Form")
```

### Case 2: Summarize Workflow Results

```python
# After running workflow
workflow_results = await on_new_case_created_async(...)

# Get summaries
summaries = workflow_results["results"]["summarization"]["summaries"]

# Process summaries
for summary_data in summaries:
    if summary_data["status"] == "success":
        # Save to database
        save_summary_to_db(
            case_id="...",
            document_type=summary_data["document_type"],
            summary=summary_data["summary"]
        )
```

### Case 3: Custom Integration

```python
from src.orchestration.case_workflow import SummarizationProcessor

# Create processor
processor = SummarizationProcessor()

# Prepare input (from your extraction step)
inputs = {
    "extracted_entities": [
        {
            "document_type": "Lab Report",
            "file_path": "lab_report.pdf",
            "extraction_result": {
                "entities": [
                    {"type": "Test Name", "value": "Blood Test"},
                    {"type": "Result", "value": "Normal"}
                ]
            },
            "status": "success"
        }
    ]
}

# Process
result = processor.process(inputs)
summaries = result["summaries"]
```

## Troubleshooting

### Issue: "Azure OpenAI configuration missing"

**Solution:**
```bash
# Check environment variables are set
echo $GPT_4_1_API_ENDPOINT
echo $GPT_4_1_API_DEPLOYMENT

# Make sure .env is loaded
from dotenv import load_dotenv
load_dotenv()
```

### Issue: "No entities found"

**Solution:**
- Verify extraction step succeeded
- Check entity format matches expected structure
- Review extraction logs for errors

### Issue: "Authentication failed"

**Solution:**
```bash
# Login to Azure
az login

# Or set up service principal
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
export AZURE_TENANT_ID=...
```

## Next Steps

1. **Read Full Documentation**: See `SUMMARIZATION_STEP.md` for detailed information
2. **Review Test Notebook**: Check `test_summary.ipynb` for working examples
3. **Run Demo**: Execute `summarization_example.py` to see it in action
4. **Integrate**: Add summarization to your case processing workflow

## API Reference

### EntityLoader

```python
class EntityLoader:
    @staticmethod
    def load_and_extract(file_path: str) -> Dict[str, str]:
        """Load and extract entities from label.json format."""
```

### SummarizationService

```python
class SummarizationService:
    def generate_summary(
        self,
        entities: Dict[str, str],
        context: Optional[str] = None
    ) -> Dict:
        """Generate summary from entities."""
```

### SummarizationProcessor

```python
class SummarizationProcessor(IDocumentProcessor):
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process extracted entities into summaries."""
```

## Support

For issues or questions:
1. Check the full documentation in `SUMMARIZATION_STEP.md`
2. Review logs for detailed error messages
3. Consult the test notebook for working examples
