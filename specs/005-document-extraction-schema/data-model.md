# Data Model: Schema-Based Document Extraction

**Feature**: [spec.md](spec.md)  
**Date**: 29 December 2025  
**Status**: Complete

## Entity Relationship Overview

```
┌─────────────────────┐       ┌─────────────────────┐
│   DocumentType      │       │  ExtractionModel    │
├─────────────────────┤       ├─────────────────────┤
│ id: UUID            │       │ id: UUID            │
│ name: str           │       │ name: str           │
│ description: str    │       │ type: ModelType     │
│ created_at: datetime│       │ endpoint: str       │
│ created_by: str     │       │ version: str        │
│ is_active: bool     │       │ is_active: bool     │
└─────────┬───────────┘       └─────────┬───────────┘
          │ 1                           │ *
          │                             │
          ▼ *                           │
┌─────────────────────┐                 │
│ DocumentTypeVersion │◄────────────────┘
├─────────────────────┤
│ id: UUID            │
│ document_type_id: FK│
│ version: str        │
│ input_schema: JSON  │
│ output_schema: JSON │
│ model_config: JSON  │
│ citation_level: enum│
│ confidence_threshold│
│ created_at: datetime│
│ is_active: bool     │
└─────────┬───────────┘
          │ 1
          │
          ▼ *
┌─────────────────────┐       ┌─────────────────────┐
│  ExtractionResult   │       │    ExtractedField   │
├─────────────────────┤       ├─────────────────────┤
│ id: UUID            │◄──────│ result_id: FK       │
│ document_id: FK     │ 1   * │ field_name: str     │
│ version_id: FK      │       │ value: Any          │
│ status: enum        │       │ confidence: float   │
│ models_used: list   │       │ citations: list     │
│ processing_duration │       │ needs_review: bool  │
│ created_at: datetime│       │ alternatives: list  │
└─────────────────────┘       └─────────────────────┘
```

## Core Entities

### 1. DocumentType

Represents a category of documents with specific structure and content patterns.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| name | str | Unique, max 100 | Human-readable name (e.g., "Bank Statement") |
| description | str | Optional, max 500 | Purpose and usage notes |
| created_at | datetime | Auto-gen | Creation timestamp |
| created_by | str | Required | User who created the type |
| is_active | bool | Default: true | Soft delete flag |

**Validation Rules**:
- Name must be unique across active document types
- Name must match pattern: `^[A-Za-z][A-Za-z0-9_\s-]{2,99}$`

### 2. DocumentTypeVersion

Specific version of a document type with its extraction configuration.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| document_type_id | UUID | FK → DocumentType | Parent document type |
| version | str | Required, semver | Version string (e.g., "1.0.0", "2023") |
| input_schema | JSON | Required | Fields to extract (JSON Schema) |
| output_schema | JSON | Required | Output structure definition (JSON Schema) |
| model_config | JSON | Required | Extraction model configuration |
| citation_level | enum | Required | "page" \| "bounding_box" \| "both" |
| confidence_threshold | float | 0.0-1.0, default 0.7 | Fallback trigger threshold |
| created_at | datetime | Auto-gen | Creation timestamp |
| created_by | str | Required | User who created the version |
| is_active | bool | Default: true | Whether this version is usable |

**Validation Rules**:
- Version must be unique within document type
- input_schema must be valid JSON Schema Draft 7
- output_schema must be valid JSON Schema Draft 7
- model_config must reference valid ExtractionModel IDs

### 3. ExtractionModel

Represents a model or algorithm used for extraction.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| name | str | Unique, max 100 | Model identifier (e.g., "azure_doc_intelligence_v4") |
| type | enum | Required | "ocr" \| "layout" \| "llm" \| "custom" |
| endpoint | str | Optional | API endpoint URL |
| version | str | Required | Model version |
| capabilities | list[str] | Optional | Supported extraction types |
| is_active | bool | Default: true | Availability flag |
| created_at | datetime | Auto-gen | Registration timestamp |

**Validation Rules**:
- Name must be unique
- Type must be from allowed enum values
- Endpoint must be valid URL if provided

### 4. ExtractionResult

Output of the extraction process for a document.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| document_id | UUID | FK → Document | Source document |
| version_id | UUID | FK → DocumentTypeVersion | Schema version used |
| status | enum | Required | "pending" \| "in_progress" \| "completed" \| "failed" \| "needs_review" |
| models_used | list[str] | Required | Models invoked during extraction |
| raw_output | JSON | Optional | Full model output for debugging |
| processing_duration_ms | int | Optional | Time taken in milliseconds |
| error_message | str | Optional | Error details if failed |
| created_at | datetime | Auto-gen | Extraction start timestamp |
| completed_at | datetime | Optional | Extraction completion timestamp |
| created_by | str | Required | User/system who triggered extraction |

**State Transitions**:
```
pending → in_progress → completed
                     → failed
                     → needs_review (if conflicts detected)
```

### 5. ExtractedField

Individual field extracted from a document.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| result_id | UUID | FK → ExtractionResult | Parent result |
| field_name | str | Required | Field key from schema |
| value | Any | Nullable | Extracted value |
| value_type | str | Required | "string" \| "number" \| "date" \| "boolean" \| "array" \| "object" |
| confidence | float | 0.0-1.0 | Extraction confidence score |
| citations | list[Citation] | Required | Source locations |
| needs_review | bool | Default: false | Flag for human review |
| review_reason | str | Optional | Why review is needed |
| alternatives | list[Alternative] | Optional | Other extracted values with lower confidence |
| model_source | str | Required | Model that produced this value |

**Validation Rules**:
- field_name must exist in output_schema
- value must match type defined in output_schema
- citations must have at least one entry for successful extraction

## Embedded Value Objects

### Citation

Location reference for extracted data.

```json
{
  "type": "page | bounding_box",
  "page": 1,
  "bbox": {
    "x": 0.12,
    "y": 0.45,
    "width": 0.08,
    "height": 0.02
  },
  "text_snippet": "original text fragment"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| type | enum | Required | "page" or "bounding_box" |
| page | int | Required, ≥1 | Page number (1-indexed) |
| bbox | object | Optional | Normalized coordinates (0.0-1.0) |
| bbox.x | float | 0.0-1.0 | Left edge |
| bbox.y | float | 0.0-1.0 | Top edge |
| bbox.width | float | 0.0-1.0 | Width |
| bbox.height | float | 0.0-1.0 | Height |
| text_snippet | str | Optional, max 500 | Source text for context |

### Alternative

Alternative extracted value when multiple candidates exist.

```json
{
  "value": "alternative value",
  "confidence": 0.65,
  "model_source": "model_b"
}
```

### ModelConfiguration

Configuration for extraction model pipeline.

```json
{
  "models": [
    {
      "model_id": "uuid",
      "order": 1,
      "strategy": "primary",
      "fields": ["*"]
    },
    {
      "model_id": "uuid",
      "order": 2,
      "strategy": "fallback",
      "fields": ["account_number", "balance"]
    }
  ],
  "combination_strategy": "sequential | parallel | ensemble",
  "conflict_resolution": "highest_confidence | flag_for_review | primary_wins"
}
```

## Input/Output Schema Templates

### Input Schema (JSON Schema Draft 7)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Bank Statement v2.0 Extraction Fields",
  "properties": {
    "account_number": {
      "type": "string",
      "description": "Bank account number",
      "extraction_hints": ["Account No.", "Account Number", "A/C No."],
      "required": true
    },
    "account_holder": {
      "type": "string",
      "description": "Name of account holder",
      "required": true
    },
    "statement_date": {
      "type": "string",
      "format": "date",
      "description": "Statement date",
      "required": true
    },
    "opening_balance": {
      "type": "number",
      "description": "Opening balance amount",
      "required": false
    },
    "closing_balance": {
      "type": "number",
      "description": "Closing balance amount",
      "required": true
    }
  },
  "required": ["account_number", "account_holder", "statement_date", "closing_balance"]
}
```

### Output Schema (JSON Schema Draft 7)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Bank Statement v2.0 Extraction Result",
  "properties": {
    "account_number": {
      "type": "object",
      "properties": {
        "value": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "citations": { "type": "array", "items": { "$ref": "#/definitions/citation" } },
        "needs_review": { "type": "boolean" }
      },
      "required": ["value", "confidence", "citations"]
    }
  },
  "definitions": {
    "citation": {
      "type": "object",
      "properties": {
        "type": { "enum": ["page", "bounding_box"] },
        "page": { "type": "integer", "minimum": 1 },
        "bbox": {
          "type": "object",
          "properties": {
            "x": { "type": "number", "minimum": 0, "maximum": 1 },
            "y": { "type": "number", "minimum": 0, "maximum": 1 },
            "width": { "type": "number", "minimum": 0, "maximum": 1 },
            "height": { "type": "number", "minimum": 0, "maximum": 1 }
          }
        }
      }
    }
  }
}
```

## Database Considerations

### Azure Cosmos DB Structure

**Container**: `extraction_schemas`
- Partition Key: `/document_type_id`
- Includes: DocumentType, DocumentTypeVersion

**Container**: `extraction_models`
- Partition Key: `/type`
- Includes: ExtractionModel

**Container**: `extraction_results`
- Partition Key: `/document_id`
- Includes: ExtractionResult, ExtractedField (embedded)

### Indexing Strategy

- Composite index on (document_type_id, version, is_active) for schema lookup
- Index on (document_id, created_at) for result retrieval
- Index on (status, needs_review) for review queue

## Relationship to Existing Models

| New Entity | Existing Entity | Relationship |
|------------|-----------------|--------------|
| ExtractionResult.document_id | Document (document.py) | FK reference |
| ExtractedField | EntityResponse (entity.py) | Extends pattern, adds citations |
| DocumentType | DocumentType enum (enums.py) | Supersedes static enum |
| ModelConfiguration | N/A | New capability |

## Migration Notes

1. **DocumentType Enum Migration**: Existing `DocumentType` enum in `enums.py` will be replaced by database-driven document types. Backward compatibility maintained via lookup table.

2. **Entity Model Extension**: `EntityResponse.source_location` string will be migrated to structured `Citation` objects.

3. **Soft Delete Pattern**: All entities use `is_active` flag for soft delete, matching existing repository patterns.
