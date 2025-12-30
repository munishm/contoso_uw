# Implementation Plan: Schema-Based Document Extraction

**Branch**: `005-document-extraction-schema` | **Date**: 29 December 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-document-extraction-schema/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Schema-based document extraction enables configurable, versioned extraction of structured data from documents using multiple AI models with source citations. The system maintains a registry of document types with input/output schemas, supports model pipelines (sequential, parallel, ensemble), and provides page-level or bounding-box citations for all extracted fields.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic, Azure SDK (azure-ai-formrecognizer, azure-ai-openai), jsonschema  
**Storage**: Azure Cosmos DB (schema registry), Azure Blob Storage (documents)  
**Testing**: pytest with pytest-asyncio  
**Target Platform**: Azure App Service / Azure Container Apps  
**Project Type**: web (extends existing FastAPI backend)  
**Performance Goals**: <2 min per document extraction, 100 docs/hour throughput  
**Constraints**: <5 min end-to-end processing (Constitution Principle 6), Azure-only services (Constitution Principle 9)  
**Scale/Scope**: POC: 2 document types, 5-6 fields each; Production: 50+ document types

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
├── api/
│   ├── models/
│   │   ├── extraction.py          # NEW: Extraction result models
│   │   ├── schema.py              # NEW: Document type/version models
│   │   └── citation.py            # NEW: Citation value objects
│   ├── repositories/
│   │   ├── schema_repository.py   # NEW: Cosmos DB schema registry
│   │   └── extraction_repository.py  # NEW: Extraction results storage
│   ├── services/
│   │   ├── extraction_service.py  # NEW: Extraction orchestration
│   │   ├── schema_service.py      # NEW: Schema management
│   │   └── model_adapters/        # NEW: Model integration adapters
│   │       ├── base.py
│   │       ├── azure_doc_intelligence.py
│   │       └── azure_openai.py
│   └── routes/
│       ├── extraction_routes.py   # NEW: Extraction API endpoints
│       └── schema_routes.py       # NEW: Schema management endpoints
└── shared/
    └── schemas/                   # NEW: JSON Schema templates

tests/
├── api/
│   ├── test_extraction_service.py
│   ├── test_schema_service.py
│   └── test_extraction_routes.py
└── integration/
    └── test_extraction_pipeline.py
```

**Structure Decision**: Extends existing FastAPI backend in `src/api/` following established patterns (Pydantic models, repository pattern, service layer). Model adapters provide plugin architecture for extraction models.

## Complexity Tracking

**No Constitution violations** - All principles satisfied:
- Follows existing FastAPI patterns (Principle: Consistency Over Innovation)
- Uses Azure SDK directly without wrappers (Principle: Anti-Framework Wrapping)
- Repository pattern already established in codebase (no new abstraction)
- Extraction models as plugins enables extensibility without tight coupling
