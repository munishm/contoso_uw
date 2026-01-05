# Quickstart: Schema-Based Document Extraction

**Feature**: [spec.md](spec.md)  
**Date**: 29 December 2025

## Overview

This guide walks through the essential steps to set up and use schema-based document extraction as a Python module, from registering a document type to extracting data with citations.

## Prerequisites

- Python 3.11+
- Access to HSBC Azure subscription
- Azure AI Document Intelligence endpoint and key
- Azure OpenAI Service endpoint and deployment
- Azure Cosmos DB database provisioned

## 1. Initialize Schema Service

Create and configure the schema service:

```python
from src.entity_extraction.services import SchemaService
from src.entity_extraction.repositories import SchemaRepository
from azure.cosmos import CosmosClient

# Initialize Cosmos DB client
cosmos_client = CosmosClient.from_connection_string(
    conn_str=os.getenv("COSMOS_CONNECTION_STRING")
)
database = cosmos_client.get_database_client("extraction_db")

# Initialize repositories and services
schema_repo = SchemaRepository(database)
schema_service = SchemaService(schema_repo)
```

## 2. Register a Document Type

Create a new document type for bank statements:

```python
from src.entity_extraction.models import DocumentTypeCreate

document_type = await schema_service.create_document_type(
    DocumentTypeCreate(
        name="Bank Statement",
        description="Monthly bank account statements from major financial institutions"
    )
)

print(f"Created document type: {document_type.id}")
# Output: Created document type: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## 3. Register Extraction Models

Register the Azure Document Intelligence model:

```python
from src.entity_extraction.models import ExtractionModelCreate, ModelType

# Register Azure Document Intelligence
doc_intelligence_model = await schema_service.register_extraction_model(
    ExtractionModelCreate(
        name="azure_doc_intelligence_v4",
        type=ModelType.OCR,
        endpoint=os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT"),
        version="4.0",
        capabilities=["ocr", "tables", "key_value_pairs", "layout"]
    )
)

# Register Azure OpenAI
openai_model = await schema_service.register_extraction_model(
    ExtractionModelCreate(
        name="azure_openai_gpt4_extractor",
        type=ModelType.LLM,
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        version="gpt-4-turbo",
        capabilities=["structured_extraction", "entity_recognition"]
    )
)
```

## 4. Create a Schema Version

Define the extraction schema for Bank Statement v2.0:

```python
from src.entity_extraction.models import SchemaVersionCreate, CitationLevel

input_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "account_number": {
            "type": "string",
            "description": "Bank account number",
            "extraction_hints": ["Account No.", "Account Number", "A/C No."]
        },
        "account_holder": {
            "type": "string",
            "description": "Name of account holder"
        },
        "statement_period": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            }
        },
        "closing_balance": {
            "type": "number",
            "description": "Closing balance amount"
        }
    },
    "required": ["account_number", "account_holder", "closing_balance"]
}

output_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "account_number": {"$ref": "#/definitions/extracted_field"},
        "account_holder": {"$ref": "#/definitions/extracted_field"},
        "statement_period": {"$ref": "#/definitions/extracted_field"},
        "closing_balance": {"$ref": "#/definitions/extracted_field"}
    },
    "definitions": {
        "extracted_field": {
            "type": "object",
            "properties": {
                "value": {},
                "confidence": {"type": "number"},
                "citations": {"type": "array"},
                "needs_review": {"type": "boolean"}
            }
        }
    }
}

model_config = {
    "models": [
        {
            "model_id": str(doc_intelligence_model.id),
            "order": 1,
            "strategy": "primary",
            "fields": ["*"]
        },
        {
            "model_id": str(openai_model.id),
            "order": 2,
            "strategy": "fallback",
            "fields": ["account_holder", "statement_period"]
        }
    ],
    "combination_strategy": "sequential",
    "conflict_resolution": "flag_for_review"
}

schema_version = await schema_service.create_schema_version(
    document_type_id=document_type.id,
    version_data=SchemaVersionCreate(
        version="2.0.0",
        input_schema=input_schema,
        output_schema=output_schema,
        model_config=model_config,
        citation_level=CitationLevel.BOUNDING_BOX,
        confidence_threshold=0.7
    )
)
```

## 5. Extract Data from a Document

Initialize extraction service and trigger extraction:

```python
from src.entity_extraction.services import SchemaExtractionService
from src.entity_extraction.repositories import ExtractionRepository

# Initialize extraction service
extraction_repo = ExtractionRepository(database)
extraction_service = SchemaExtractionService(
    schema_repo=schema_repo,
    extraction_repo=extraction_repo
)

# Perform extraction
extraction_result = await extraction_service.extract_document(
    document_id="doc-123-456",
    document_type_id=str(document_type.id),
    version="2.0.0"
)

print(f"Extraction status: {extraction_result.status}")
print(f"Processing time: {extraction_result.processing_duration_ms}ms")
```

## 6. Get Extraction Results

Retrieve the completed extraction with citations:

```python
# Wait for completion (in production, use async/polling)
import asyncio
while extraction_result.status == ExtractionStatus.IN_PROGRESS:
    await asyncio.sleep(1)
    extraction_result = await extraction_service.get_extraction_result(
        extraction_result.id
    )

# Display results
for field in extraction_result.fields:
    print(f"\nField: {field.field_name}")
    print(f"  Value: {field.value}")
    print(f"  Confidence: {field.confidence:.2f}")
    print(f"  Citations: {len(field.citations)} location(s)")
    
    if field.needs_review:
        print(f"  ⚠️  Needs review: {field.review_reason}")
        if field.alternatives:
            print(f"  Alternatives: {field.alternatives}")
    
    # Display citation details
    for citation in field.citations:
        if citation.type == "bounding_box":
            print(f"    Page {citation.page}, bbox: ({citation.bbox.x:.2f}, "
                  f"{citation.bbox.y:.2f}, {citation.bbox.width:.2f}, "
                  f"{citation.bbox.height:.2f})")
        else:
            print(f"    Page {citation.page}")
```

**Example Output:**
```
Field: account_number
  Value: 1234567890
  Confidence: 0.95
  Citations: 1 location(s)
    Page 1, bbox: (0.12, 0.08, 0.15, 0.02)

Field: account_holder
  Value: John Smith
  Confidence: 0.88
  Citations: 1 location(s)
    Page 1, bbox: (0.12, 0.12, 0.20, 0.02)

Field: closing_balance
  Value: 15234.56
  Confidence: 0.65
  Citations: 1 location(s)
    Page 2, bbox: (0.70, 0.85, 0.12, 0.02)
  ⚠️  Needs review: Confidence below threshold (0.7)
  Alternatives: [{'value': 15234.65, 'confidence': 0.62, 'model_source': 'azure_openai_gpt4_extractor'}]
```

## 7. Review Flagged Fields

Submit human review for flagged fields:

```python
# Submit review decision
reviewed_field = await extraction_service.review_field(
    extraction_id=extraction_result.id,
    field_name="closing_balance",
    action="correct",
    corrected_value=15234.56,
    notes="Verified against source document page 2"
)

print(f"Review recorded for {reviewed_field.field_name}")
```

## 8. Integration with Orchestration

Use extraction in orchestration workflows:

```python
# In src/orchestration/nodes/extraction_node.py
from src.entity_extraction.services import SchemaExtractionService

async def extract_document_node(state: WorkflowState) -> dict:
    """Orchestration node for schema-based extraction."""
    
    extraction_service = get_extraction_service()  # From dependency injection
    
    # Extract from document
    result = await extraction_service.extract_document(
        document_id=state["document_id"],
        document_type_id=state["document_type"],
        version=state.get("schema_version", "latest")
    )
    
    # Update state with extracted data
    return {
        "extraction_id": result.id,
        "extracted_fields": result.fields,
        "needs_review": any(f.needs_review for f in result.fields)
    }
```

## Key Concepts

### Module Architecture

The extraction module is **not exposed as a REST API**. Instead:
- Services are called directly from Python code
- Orchestration workflows invoke extraction as part of document processing pipelines
- Repository pattern provides data access abstraction
- Adapter pattern enables pluggable extraction models

### Citation Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `page` | Page number only | Quick reference, lower storage |
| `bounding_box` | Normalized coordinates (0.0-1.0) | Precise highlighting, audit |
| `both` | Page and bounding box | Maximum traceability |

### Model Strategies

| Strategy | Description |
|----------|-------------|
| `primary` | Main model for extraction |
| `fallback` | Used when primary fails or low confidence |
| `parallel` | Run simultaneously, combine results |

### Confidence Threshold

- Default: 0.7 (70%)
- Configurable per document type version
- Below threshold triggers fallback model (if configured)
- Low-confidence fields flagged for human review

## Error Handling

### Unknown Document Type

```python
try:
    result = await extraction_service.extract_document(
        document_id="doc-123",
        document_type_id="unknown-type",
        version="1.0.0"
    )
except DocumentTypeMismatchError as e:
    print(f"Error: {e.message}")
    # Handle: prompt user to specify correct document type
```

### Missing Required Fields

Extraction completes successfully but returns null with indicator:

```python
for field in result.fields:
    if field.value is None and field.field_name in required_fields:
        print(f"Missing required field: {field.field_name}")
        print(f"Reason: {field.review_reason}")
```

## Next Steps

1. **Integrate with orchestration**: Add extraction nodes to workflow graphs
2. **Test with sample documents**: Upload test documents and verify extraction quality
3. **Tune confidence thresholds**: Adjust based on observed accuracy
4. **Add fallback models**: Configure LLM fallback for complex fields
5. **Monitor metrics**: Track extraction accuracy and processing times in Azure Monitor
