# Batch Evaluation Integration

## Overview

The entity extraction service now automatically evaluates extracted fields after extraction and saves the evaluation results to the Cosmos DB database in the same document collection.

## Implementation

### Changes Made

1. **ExtractionRepository** - Updated `update_extraction()` to accept optional `evaluation_results` parameter
2. **SchemaExtractionService** - Added batch evaluation after extraction completes

### How It Works

```python
# 1. Extract fields from document
extraction = await extraction_service.extract_document(
    document_id="doc-123",
    document_content=pdf_bytes,
    document_type_id=document_type_id,
    version="1.0.0"
)

# 2. Evaluation runs automatically (if enabled)
# 3. Results saved to database in extraction.evaluation field
```

### Database Structure

```json
{
  "id": "document-id",
  "case_id": "case-123",
  "extraction": {
    "fields": [...],
    "evaluation": {
      "total_fields": 5,
      "results": [
        {
          "field_name": "account_number",
          "extracted_value": "1234567890",
          "evaluations": {
            "correctness": {
              "score": 1.0,
              "extraction_correct": true
            }
          },
          "summary": {
            "overall_score": 1.0,
            "evaluators_run": ["correctness"]
          }
        }
      ],
      "aggregate_summary": {
        "average_correctness_score": 0.92,
        "fields_correct": 4,
        "total_fields": 5
      }
    }
  }
}
```

## Configuration

### Enable/Disable Evaluation

```python
# Enable (default)
service = SchemaExtractionService(
    schema_repo, extraction_repo, model_repo,
    enable_evaluation=True
)

# Disable
service = SchemaExtractionService(
    schema_repo, extraction_repo, model_repo,
    enable_evaluation=False
)
```

### Requirements

- Evaluation service module installed
- Azure Document Intelligence SDK: `pip install azure-ai-documentintelligence`
- Azure credentials (for completeness evaluator - optional)

### Environment Variables

```bash
# Required for Document Intelligence OCR
DOC_INTELLIGENCE_ENDPOINT=https://your-instance.cognitiveservices.azure.com/

# Optional for completeness evaluator
EXTRACTION_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
EXTRACTION_OPENAI_DEPLOYMENT_GPT4_VISION=gpt-4-vision-preview
```

## Text Extraction

The system uses **Azure Document Intelligence** to extract text page-wise from documents:

- **Text Files**: Directly decoded if UTF-8 compatible
- **PDFs & Images**: Processed using Document Intelligence `prebuilt-read` model
- **Page Organization**: Text is extracted and organized by page number
- **Format**: `[Page 1]\ntext...\n\n[Page 2]\ntext...`

Example output:
```
[Page 1]
Invoice Number: INV-12345
Date: 2024-01-08
Customer: ACME Corp

[Page 2]
Line Items:
- Product A: $100
- Product B: $250
Total: $350
```

## Accessing Results

```python
# Query document from Cosmos DB
container = database.get_container_client("documents")
doc = container.read_item(item=doc_id, partition_key=case_id)

# Access evaluation results
evaluation = doc["extraction"]["evaluation"]
avg_score = evaluation["aggregate_summary"]["average_correctness_score"]
fields_correct = evaluation["aggregate_summary"]["fields_correct"]

print(f"Average correctness: {avg_score}")
print(f"Fields correct: {fields_correct}/{evaluation['total_fields']}")
```

## Error Handling

- If evaluation initialization fails, extraction continues without evaluation
- If evaluation fails during processing, error is logged but extraction still completes
- No breaking changes to existing code - evaluation_results parameter is optional

## Performance

- Adds ~500-2000ms to extraction time (depends on field count)
- Correctness evaluator has no API costs (computational only)
- Completeness evaluator requires Azure OpenAI (additional cost)
