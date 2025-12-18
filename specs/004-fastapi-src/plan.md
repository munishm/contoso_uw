# Implementation Plan: FastAPI Structure and API Implementation

**Branch**: `004-fastapi-src` | **Date**: 2025-12-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-fastapi-src/spec.md`
**Depends On**: [002-case-api OpenAPI spec](../002-case-api/contracts/openapi.yaml)

## Summary

Create a proper FastAPI application structure within the `src/api/` folder and implement all 21 API endpoints defined in the OpenAPI specification. The implementation integrates with existing shared modules (`src/shared/`, `src/interfaces/`), uses Azure Cosmos DB for persistence, Azure Blob Storage for documents, and Azure Service Bus for event-driven processing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity  
**Storage**: Azure Cosmos DB (cases, documents, entities, summaries, counters), Azure Blob Storage (files)  
**Testing**: pytest, pytest-asyncio, httpx (async test client), pytest-cov  
**Target Platform**: Linux server (Azure App Service / Container Apps)  
**Project Type**: Web application (backend API within existing monorepo)  
**Performance Goals**: <200ms p95 for CRUD, <30s for 50MB uploads, 50 concurrent requests  
**Constraints**: 50 MB max file, 50 docs/case, Azure-only services, integrate with existing src/shared/  
**Scale/Scope**: POC phase - single tenant, team-level usage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle 1: Compliance & Regulatory Adherence** - Audit logging with correlation IDs, encryption via Azure services, PII handling follows RBAC
- [x] **Principle 2: Human-in-the-Loop** - API provides decision support data; no autonomous decisions; underwriters review all outputs
- [x] **Principle 3: Full Auditability & Source Traceability** - All entities include document_id and page_number; case status history tracked
- [x] **Principle 4: Scalable Architecture** - Data schemas support language metadata; architecture supports multi-language expansion
- [x] **Principle 5: Security by Design** - Bearer token auth, Azure Key Vault for secrets, TLS 1.3+, RBAC enforcement
- [x] **Principle 6: Performance Targets** - <200ms API response, <5 min full processing, architecture supports 10+ concurrent cases
- [x] **Principle 7: Model Monitoring** - Confidence scores exposed in API; feedback capture designed in
- [x] **Principle 8: Reusable Patterns** - Domain-agnostic API design; configurable document types; extensible schemas
- [x] **Principle 9: Azure-Native** - Cosmos DB, Blob Storage, Service Bus, Application Insights - all Azure services

## Project Structure

### Documentation (this feature)

```text
specs/004-fastapi-src/
├── plan.md              # This file
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - Cosmos DB schema design
├── quickstart.md        # Phase 1 output - development setup
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── api/                           # NEW - FastAPI application
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Pydantic BaseSettings configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── case.py                # Case Pydantic models (request/response)
│   │   ├── document.py            # Document Pydantic models
│   │   ├── entity.py              # Entity Pydantic models
│   │   ├── summary.py             # Summary Pydantic models
│   │   ├── common.py              # Shared models (Error, Pagination)
│   │   └── enums.py               # Status enumerations
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── cases.py               # Case CRUD endpoints (7 endpoints)
│   │   ├── documents.py           # Document endpoints (6 endpoints)
│   │   ├── processing.py          # Entity/summary endpoints (8 endpoints)
│   │   └── health.py              # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── case_service.py        # Case business logic
│   │   ├── document_service.py    # Document business logic
│   │   ├── storage_service.py     # Azure Blob Storage operations
│   │   └── queue_service.py       # Azure Service Bus operations
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                # Base repository with Cosmos DB client
│   │   ├── case_repository.py     # Case data access
│   │   ├── document_repository.py # Document data access
│   │   ├── entity_repository.py   # Entity data access
│   │   ├── summary_repository.py  # Summary data access
│   │   └── counter_repository.py  # Atomic counter for case IDs
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                # Bearer token validation
│   │   ├── error_handler.py       # Global exception handling
│   │   ├── logging.py             # Request/response logging
│   │   └── correlation.py         # Correlation ID injection
│   └── dependencies.py            # FastAPI dependency injection
├── shared/                        # EXISTING - Reuse models and utilities
│   ├── models/
│   │   ├── document.py            # Existing Document model (reference)
│   │   └── entity.py              # Existing Entity model (reference)
│   ├── config/
│   │   └── env_loader.py          # Existing env config (reuse)
│   └── utils/
│       ├── file_helpers.py        # Existing file utilities (reuse)
│       └── validation.py          # Existing validation (reuse)
├── interfaces/                    # EXISTING - Processing contracts
│   ├── classifier.py              # Classification interface
│   ├── extractor.py               # Extraction interface
│   ├── processor.py               # Processing interface
│   └── summarizer.py              # Summarization interface
├── document_classification/       # EXISTING - Unchanged
├── document_summarization/        # EXISTING - Unchanged
├── entity_extraction/             # EXISTING - Unchanged
└── orchestration/                 # EXISTING - Unchanged

tests/
├── api/                           # NEW - API tests
│   ├── conftest.py                # Test fixtures and mocks
│   ├── contract/
│   │   └── test_openapi_compliance.py  # OpenAPI contract validation
│   ├── integration/
│   │   ├── test_cases_api.py
│   │   ├── test_documents_api.py
│   │   └── test_processing_api.py
│   └── unit/
│       ├── test_case_service.py
│       ├── test_document_service.py
│       └── test_repositories.py
└── [existing test directories]
```

**Structure Decision**: Creating new `src/api/` directory to house the FastAPI application, separate from existing processing modules. This allows the API layer to import from `src/shared/` and `src/interfaces/` while maintaining clear separation of concerns. The API models in `src/api/models/` will be specific to HTTP request/response while referencing domain models from `src/shared/models/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository layer | Cosmos DB partition key management, query abstraction | Direct Cosmos access in services would duplicate partition logic |
| Separate API models | HTTP concerns (serialization) vs domain concerns | Using shared models directly would leak HTTP details into domain |

## Phase Status

| Phase | Status | Artifacts |
|-------|--------|-----------|
| Phase 0: Research | ✅ Complete | [research.md](research.md) |
| Phase 1: Design | ✅ Complete | [data-model.md](data-model.md), [quickstart.md](quickstart.md) |
| Phase 2: Tasks | ⏳ Pending | Run `/speckit.tasks` to generate |

## Generated Artifacts

- **[research.md](research.md)** - 12 technology decisions covering FastAPI location, shared model integration, Cosmos SDK, container design, ID generation, blob paths, SAS tokens, Service Bus, auth middleware, error handling
- **[data-model.md](data-model.md)** - Cosmos DB container schemas (5 containers), Pydantic models for API layer, status transitions, indexing policies
- **[quickstart.md](quickstart.md)** - Development setup, environment variables, Azure resource setup, testing instructions
- **Agent context updated** - `.github/agents/copilot-instructions.md` updated with Python 3.11, FastAPI, Azure Cosmos DB stack
