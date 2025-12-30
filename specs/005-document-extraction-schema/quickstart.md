# Quickstart: Schema-Based Document Extraction

**Feature**: [spec.md](spec.md)  
**Date**: 29 December 2025

## Overview

This guide walks through the essential steps to set up and use schema-based document extraction, from registering a document type to extracting data with citations.

## Prerequisites

- Python 3.11+
- Access to HSBC Azure subscription
- Azure AI Document Intelligence endpoint and key
- Azure OpenAI Service endpoint and deployment
- Azure Cosmos DB database provisioned

## 1. Register a Document Type

Create a new document type for bank statements:

```bash
curl -X POST /api/v1/document-types \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bank Statement",
    "description": "Monthly bank account statements from major financial institutions"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Bank Statement",
  "description": "Monthly bank account statements from major financial institutions",
  "is_active": true,
  "created_at": "2025-12-29T10:00:00Z",
  "created_by": "user@example.com",
  "versions_count": 0
}
```

## 2. Register Extraction Models

Register the Azure Document Intelligence model:

```bash
curl -X POST /api/v1/extraction-models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure_doc_intelligence_v4",
    "type": "ocr",
    "endpoint": "https://your-instance.cognitiveservices.azure.com/",
    "version": "4.0",
    "capabilities": ["ocr", "tables", "key_value_pairs", "layout"]
  }'
```

Register the Azure OpenAI extraction model:

```bash
curl -X POST /api/v1/extraction-models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure_openai_gpt4_extractor",
    "type": "llm",
    "endpoint": "https://your-instance.openai.azure.com/",
    "version": "gpt-4-turbo",
    "capabilities": ["structured_extraction", "entity_recognition"]
  }'
```

## 3. Create a Schema Version

Define the extraction schema for Bank Statement v2.0:

```bash
curl -X POST /api/v1/document-types/a1b2c3d4-e5f6-7890-abcd-ef1234567890/versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0.0",
    "input_schema": {
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
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" }
          }
        },
        "closing_balance": {
          "type": "number",
          "description": "Closing balance amount"
        }
      },
      "required": ["account_number", "account_holder", "closing_balance"]
    },
    "output_schema": {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "account_number": { "$ref": "#/definitions/extracted_field" },
        "account_holder": { "$ref": "#/definitions/extracted_field" },
        "statement_period": { "$ref": "#/definitions/extracted_field" },
        "closing_balance": { "$ref": "#/definitions/extracted_field" }
      },
      "definitions": {
        "extracted_field": {
          "type": "object",
          "properties": {
            "value": {},
            "confidence": { "type": "number" },
            "citations": { "type": "array" },
            "needs_review": { "type": "boolean" }
          }
        }
      }
    },
    "model_config": {
      "models": [
        {
          "model_id": "<ocr_model_id>",
          "order": 1,
          "strategy": "primary",
          "fields": ["*"]
        },
        {
          "model_id": "<llm_model_id>",
          "order": 2,
          "strategy": "fallback",
          "fields": ["account_holder", "statement_period"]
        }
      ],
      "combination_strategy": "sequential",
      "conflict_resolution": "flag_for_review"
    },
    "citation_level": "bounding_box",
    "confidence_threshold": 0.7
  }'
```

## 4. Extract Data from a Document

Trigger extraction for an uploaded document:

```bash
curl -X POST /api/v1/documents/doc-123-456/extract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "2.0.0"
  }'
```

**Response (202 Accepted):**
```json
{
  "id": "extr-789-012",
  "document_id": "doc-123-456",
  "status": "pending",
  "created_at": "2025-12-29T10:05:00Z"
}
```

## 5. Get Extraction Results

Retrieve the completed extraction with citations:

```bash
curl -X GET /api/v1/extractions/extr-789-012 \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "id": "extr-789-012",
  "document_id": "doc-123-456",
  "document_type": "Bank Statement",
  "version": "2.0.0",
  "status": "completed",
  "models_used": ["azure_doc_intelligence_v4", "azure_openai_gpt4_extractor"],
  "fields": [
    {
      "field_name": "account_number",
      "value": "1234567890",
      "value_type": "string",
      "confidence": 0.95,
      "citations": [
        {
          "type": "bounding_box",
          "page": 1,
          "bbox": { "x": 0.12, "y": 0.08, "width": 0.15, "height": 0.02 },
          "text_snippet": "Account No: 1234567890"
        }
      ],
      "needs_review": false,
      "model_source": "azure_doc_intelligence_v4"
    },
    {
      "field_name": "account_holder",
      "value": "John Smith",
      "value_type": "string",
      "confidence": 0.88,
      "citations": [
        {
          "type": "bounding_box",
          "page": 1,
          "bbox": { "x": 0.12, "y": 0.12, "width": 0.20, "height": 0.02 },
          "text_snippet": "Account Holder: John Smith"
        }
      ],
      "needs_review": false,
      "model_source": "azure_doc_intelligence_v4"
    },
    {
      "field_name": "closing_balance",
      "value": 15234.56,
      "value_type": "number",
      "confidence": 0.65,
      "citations": [
        {
          "type": "bounding_box",
          "page": 2,
          "bbox": { "x": 0.70, "y": 0.85, "width": 0.12, "height": 0.02 },
          "text_snippet": "Closing Balance: $15,234.56"
        }
      ],
      "needs_review": true,
      "review_reason": "Confidence below threshold (0.7)",
      "alternatives": [
        {
          "value": 15234.65,
          "confidence": 0.62,
          "model_source": "azure_openai_gpt4_extractor"
        }
      ],
      "model_source": "azure_doc_intelligence_v4"
    }
  ],
  "processing_duration_ms": 4523,
  "created_at": "2025-12-29T10:05:00Z",
  "completed_at": "2025-12-29T10:05:04Z"
}
```

## 6. Review Flagged Fields

Submit human review for the flagged `closing_balance` field:

```bash
curl -X POST /api/v1/extractions/extr-789-012/fields/closing_balance/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "correct",
    "corrected_value": 15234.56,
    "notes": "Verified against source document page 2"
  }'
```

## Key Concepts

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

```json
{
  "error": "document_type_mismatch",
  "message": "Document does not match specified type 'Bank Statement v2.0.0'. Please specify the correct document type manually.",
  "details": {
    "document_id": "doc-123-456",
    "specified_type": "Bank Statement",
    "specified_version": "2.0.0"
  }
}
```

### Missing Required Fields

Extraction completes successfully but returns null with indicator:

```json
{
  "field_name": "account_number",
  "value": null,
  "confidence": 0.0,
  "citations": [],
  "needs_review": true,
  "review_reason": "Required field not found in document"
}
```

## Next Steps

1. **Test with sample documents**: Upload test documents and verify extraction quality
2. **Tune confidence thresholds**: Adjust based on observed accuracy
3. **Add fallback models**: Configure LLM fallback for complex fields
4. **Monitor metrics**: Track extraction accuracy and processing times in Azure Monitor
