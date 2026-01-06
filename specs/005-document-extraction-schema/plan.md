# Implementation Plan: Schema-Based Document Extraction

**Branch**: `005-document-extraction-schema` | **Date**: 29 December 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-document-extraction-schema/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Schema-based document extraction enables configurable, versioned extraction of structured data from documents using multiple AI models with source citations. Implemented as a reusable module (not REST API), it integrates with the orchestration layer for workflow execution. The system maintains a registry of document types with input/output schemas, supports model pipelines (sequential, parallel, ensemble), and provides page-level or bounding-box citations for all extracted fields.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Pydantic, Azure SDK (azure-ai-formrecognizer, azure-ai-openai), jsonschema  
**Storage**: Azure Cosmos DB (schema registry), Azure Blob Storage (documents)  
**Testing**: pytest with pytest-asyncio  
**Target Platform**: Azure App Service / Azure Container Apps  
**Project Type**: Module (integrates with existing orchestration layer)  
**Performance Goals**: <2 min per document extraction, 100 docs/hour throughput  
**Constraints**: <5 min end-to-end processing (Constitution Principle 6), Azure-only services (Constitution Principle 9)  
**Scale/Scope**: POC: 2 document types, 5-6 fields each; Production: 50+ document types  
**Integration Point**: Called by src/orchestration workflows, not exposed as REST API

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle 1: Compliance & Regulatory Adherence First** - All extracted data traceable to source with citations; audit logging included
- [x] **Principle 2: Human-in-the-Loop (HITL) Mandatory** - Low-confidence and conflicting extractions flagged for human review
- [x] **Principle 3: Full Auditability & Source Traceability** - Page-level and bounding-box citations for all extracted fields
- [x] **Principle 4: Scalable Architecture** - Schema versioning supports multi-language expansion; architecture language-agnostic
- [x] **Principle 5: Security by Design** - RBAC on schema management APIs; encrypted storage
- [x] **Principle 6: Performance Targets** - <2 min per document extraction meets <5 min POC requirement
- [x] **Principle 7: Continuous Model Monitoring** - Model performance metrics tracked per extraction
- [x] **Principle 8: Reusable Patterns & Extensibility** - Schema-driven extraction supports any document type
- [x] **Principle 9: Azure-Native Architecture** - Azure AI Document Intelligence, Azure OpenAI, Cosmos DB only

## Project Structure

### Documentation (this feature)

```text
specs/005-document-extraction-schema/
├── plan.md              # This file
├── research.md          # Technology decisions and rationale
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Usage examples and API walkthrough
├── contracts/           # OpenAPI specifications
│   └── extraction-api.yaml
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (extends existing repository structure)

```text
src/
├── api/                           # EXTEND: Add schema management routes
│   ├── routes/
│   │   └── extraction.py          # NEW: Schema & extraction API endpoints
│   └── dependencies.py            # EXTEND: Add extraction service dependencies
├── entity_extraction/              # EXTEND: Add schema-based extraction
│   ├── models/
│   │   ├── extraction.py          # NEW: Extraction result models
│   │   ├── schema.py              # NEW: Document type/version models
│   │   ├── citation.py            # NEW: Citation value objects
│   │   └── enums.py               # NEW: Enum types
│   ├── repositories/
│   │   ├── schema_repository.py   # NEW: Cosmos DB schema registry
│   │   ├── extraction_model_repository.py  # NEW: Model registry
│   │   └── extraction_repository.py  # NEW: Extraction results storage
│   ├── services/
│   │   ├── schema_extraction_service.py  # NEW: Schema-based extraction orchestration
│   │   └── schema_service.py      # NEW: Schema management
│   ├── adapters/                  # NEW: Model integration adapters
│   │   ├── base.py
│   │   ├── azure_openai_vision.py
│   │   └── azure_doc_intelligence.py
│   └── config.py                  # NEW: Module configuration
├── orchestration/                 # INTEGRATE: Call extraction from workflows
│   └── [existing workflow files will call schema extraction]
└── interfaces/
    └── extraction_types.py        # NEW: Shared type definitions

tests/
├── api/
│   └── test_extraction_routes.py  # NEW: API endpoint tests
├── entity_extraction/
│   ├── test_schema_extraction_service.py
│   ├── test_schema_service.py
│   └── test_adapters.py
└── integration/
    └── test_schema_extraction_pipeline.py
```

**Structure Decision**: Extends existing `src/entity_extraction/` module with schema-based extraction capabilities. Exposes schema management via FastAPI routes in `src/api/routes/extraction.py` for admin operations (create document types, manage schemas). Integrated with `src/orchestration/` workflows as a callable service for actual extraction. Follows established patterns (Pydantic models, repository pattern, service layer). Model adapters provide plugin architecture for extraction models.

## Complexity Tracking

**No Constitution violations** - All principles satisfied:
- Follows existing FastAPI patterns (Principle: Consistency Over Innovation)
- Uses Azure SDK directly without wrappers (Principle: Anti-Framework Wrapping)
- Repository pattern already established in codebase (no new abstraction)
- Extraction models as plugins enables extensibility without tight coupling

## Setup & Configuration

### 1. Environment Variables

Add to `.env` or Azure App Configuration:

```bash
# Azure Cosmos DB
EXTRACTION_COSMOS_ENDPOINT=https://hsbc-underwriting.documents.azure.com:443/
EXTRACTION_COSMOS_KEY=<use-azure-key-vault>
EXTRACTION_COSMOS_DATABASE=extraction_db

# Azure OpenAI
EXTRACTION_OPENAI_ENDPOINT=https://hsbc-openai.openai.azure.com/
EXTRACTION_OPENAI_KEY=<use-azure-key-vault>
EXTRACTION_OPENAI_DEPLOYMENT_GPT4_VISION=gpt-4-vision-preview

# Azure Document Intelligence (Phase 4)
EXTRACTION_DOC_INTELLIGENCE_ENDPOINT=https://hsbc-doc-intel.cognitiveservices.azure.com/
EXTRACTION_DOC_INTELLIGENCE_KEY=<use-azure-key-vault>

# Performance
EXTRACTION_SCHEMA_CACHE_TTL_SECONDS=300
EXTRACTION_MAX_CONCURRENT_EXTRACTIONS=10
```

### 2. Cosmos DB Provisioning ✅ IMPLEMENTED

**Setup Script**: `scripts/setup_extraction_cosmos.py`

Execute Cosmos DB setup script to create database and containers:

```bash
# Set environment variables
export EXTRACTION_COSMOS_ENDPOINT='https://your-account.documents.azure.com:443/'
export EXTRACTION_COSMOS_KEY='your-key'  # Optional for managed identity

# Run setup
python scripts/setup_extraction_cosmos.py
```

**What it creates:**
- Database: `extraction_db` (or custom name via EXTRACTION_COSMOS_DATABASE)
- Container: `extraction_schemas` 
  - Partition key: `/document_type_id`
  - Indexing: All paths except `/input_schema/*` and `/output_schema/*`
- Container: `extraction_models`
  - Partition key: `/type`
  - Indexing: All paths
- Container: `extraction_results`
  - Partition key: `/document_id`
  - Indexing: All paths except `/fields/*`

**Features:**
- ✅ Supports both access key and managed identity authentication
- ✅ Idempotent (safe to run multiple times)
- ✅ Optimized indexing policies for query performance
- ✅ Validates environment configuration

### 3. FastAPI Integration ✅ IMPLEMENTED

The FastAPI application now includes extraction routes at `/api/v1/extraction/*`:

**Implementation Status:**
- ✅ `src/api/routes/extraction.py` - Complete with 12 endpoints
- ✅ Registered in `src/api/main.py` - Active in application
- ✅ Dependency injection for repositories and services
- ✅ Request/response models with validation
- ✅ Error handling with appropriate HTTP status codes

**Available Endpoints:**

**Admin Endpoints** (Schema Management):
- `POST /api/v1/extraction/document-types` - Create document type
- `GET /api/v1/extraction/document-types` - List document types
- `GET /api/v1/extraction/document-types/{type_id}` - Get document type
- `POST /api/v1/extraction/document-types/{type_id}/versions` - Create schema version
- `GET /api/v1/extraction/document-types/{type_id}/versions` - List versions
- `GET /api/v1/extraction/document-types/{type_id}/versions/{version}` - Get version
- `POST /api/v1/extraction/models` - Register extraction model
- `GET /api/v1/extraction/models` - List models

**Extraction Endpoints** (Document Processing):
- `POST /api/v1/extraction/extract` - Trigger extraction (async)
- `GET /api/v1/extraction/results/{extraction_id}` - Get result
- `GET /api/v1/extraction/documents/{document_id}/extractions` - List extractions
- `POST /api/v1/extraction/results/{extraction_id}/review` - Submit review

### 4. Initial Setup Workflow

**Step 1: Register Extraction Models**

```bash
# Register GPT-4 Vision model
curl -X POST http://localhost:8000/api/v1/extraction/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azure_gpt4_vision",
    "type": "vision",
    "endpoint": "${EXTRACTION_OPENAI_ENDPOINT}",
    "version": "gpt-4-vision-preview",
    "capabilities": ["ocr", "structured_extraction", "spatial_understanding"]
  }'
```

**Step 2: Create Document Type**

```bash
# Create "Bank Statement" document type
curl -X POST http://localhost:8000/api/v1/extraction/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bank Statement",
    "description": "Monthly bank account statements from major financial institutions",
    "created_by": "system@hsbc.com"
  }'

# Response includes document_type_id: "550e8400-e29b-41d4-a716-446655440000"
```

**Step 3: Create Schema Version**

```bash
# Create v1.0.0 schema for Bank Statement
curl -X POST http://localhost:8000/api/v1/extraction/document-types/550e8400-e29b-41d4-a716-446655440000/versions \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "version": "1.0.0",
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
  },
  "output_schema": {
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
  },
  "model_config": {
    "models": [
      {
        "model_name": "azure_gpt4_vision",
        "order": 1,
        "strategy": "primary",
        "fields": ["*"]
      }
    ],
    "combination_strategy": "sequential",
    "conflict_resolution": "flag_for_review"
  },
  "citation_level": "bounding_box",
  "confidence_threshold": 0.7,
  "created_by": "system@hsbc.com"
}
EOF
```

**Step 4: Test Extraction**

```bash
# Trigger extraction for a document
curl -X POST http://localhost:8000/api/v1/extraction/extract \
  -H "Content-Type: multipart/form-data" \
  -F "document_id=doc-test-001" \
  -F "document_type_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "version=1.0.0" \
  -F "file=@sample_bank_statement.pdf"

# Response includes extraction_id: "650e8400-e29b-41d4-a716-446655440001"

# Check result
curl http://localhost:8000/api/v1/extraction/results/650e8400-e29b-41d4-a716-446655440001
```

### 5. Orchestration Integration

For workflow-based extraction (bypassing API):

```python
from entity_extraction.services import SchemaExtractionService
from entity_extraction.repositories import SchemaRepository, ExtractionRepository
from entity_extraction.adapters import AzureOpenAIVisionAdapter
from entity_extraction.config import get_cosmos_client

# Initialize in workflow
cosmos_client = get_cosmos_client()
database = cosmos_client.get_database_client("extraction_db")

schema_repo = SchemaRepository(database)
extraction_repo = ExtractionRepository(database)

extraction_service = SchemaExtractionService(schema_repo, extraction_repo)

# Register adapter
from entity_extraction.config import get_config
config = get_config()
vision_adapter = AzureOpenAIVisionAdapter(
    endpoint=config.openai_endpoint,
    api_key=config.openai_key,
    deployment=config.openai_deployment_gpt4_vision
)
extraction_service.register_adapter("azure_gpt4_vision", vision_adapter)

# Extract in workflow
result = await extraction_service.extract_document(
    document_id="doc-123",
    document_content=pdf_bytes,
    document_type_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    version="1.0.0"
)

# Check if review needed
if result.status == ExtractionStatus.REVIEW_REQUIRED:
    # Route to human review queue
    await workflow.route_to_review(result)
```

### 6. Schema Templates

Store reusable schema templates in `src/entity_extraction/schemas/`:

```text
src/entity_extraction/schemas/
├── bank_statement_v1.json
├── tax_return_v1.json
└── loan_application_v1.json
```

Load templates via API:

```bash
curl -X POST http://localhost:8000/api/v1/extraction/document-types/bulk \
  -H "Content-Type: application/json" \
  -d @src/entity_extraction/schemas/bank_statement_v1.json
```
