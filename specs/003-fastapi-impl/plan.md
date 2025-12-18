# Implementation Plan: FastAPI Implementation of Case Management API

**Branch**: `003-fastapi-impl` | **Date**: 2025-12-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-fastapi-impl/spec.md`
**Depends On**: [002-case-api OpenAPI spec](../002-case-api/contracts/openapi.yaml)

## Summary

Implement the 21-endpoint Underwriting Case Management API using FastAPI, with Azure Cosmos DB for data persistence, Azure Blob Storage for document files, and Azure Service Bus for event-driven document processing. The implementation matches the OpenAPI specification defined in 002-case-api and follows existing project patterns.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity  
**Storage**: Azure Cosmos DB (cases, documents, entities, summaries), Azure Blob Storage (files)  
**Testing**: pytest, pytest-asyncio, httpx (async test client), pytest-cov  
**Target Platform**: Linux server (Azure App Service / Container Apps)  
**Project Type**: Web application (backend API)  
**Performance Goals**: <200ms p95 for CRUD, <30s for 50MB uploads, 50 concurrent requests  
**Constraints**: 50 MB max file, 50 docs/case, Azure-only services  
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
specs/003-fastapi-impl/
├── plan.md              # This file
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - Cosmos DB schema design
├── quickstart.md        # Phase 1 output - development setup
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Dependency injection (DB, auth, services)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── cases.py           # Case CRUD endpoints (7 endpoints)
│   │       ├── documents.py       # Document endpoints (6 endpoints)
│   │       └── processing.py      # Entity/summary endpoints (8 endpoints)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── case.py                # Case Pydantic models
│   │   ├── document.py            # Document Pydantic models
│   │   ├── entity.py              # Entity Pydantic models
│   │   ├── summary.py             # Summary Pydantic models
│   │   └── common.py              # Shared models (Error, Pagination)
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
│   │   └── counter_repository.py  # Atomic counter for case IDs
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                # Bearer token validation
│   │   ├── error_handler.py       # Global exception handling
│   │   ├── logging.py             # Request/response logging
│   │   └── correlation.py         # Correlation ID injection
│   └── config/
│       ├── __init__.py
│       └── settings.py            # Environment configuration
└── tests/
    ├── conftest.py                # Test fixtures and mocks
    ├── contract/
    │   └── test_openapi_compliance.py  # OpenAPI contract validation
    ├── integration/
    │   ├── test_cases_api.py
    │   ├── test_documents_api.py
    │   └── test_processing_api.py
    └── unit/
        ├── test_case_service.py
        ├── test_document_service.py
        ├── test_storage_service.py
        └── test_repositories.py
```

**Structure Decision**: Extending existing `backend/src/` structure. Adding `repositories/` layer for Cosmos DB operations (justified by NoSQL-specific patterns like partition key handling). Services remain thin, delegating to repositories. Direct FastAPI usage without wrapper abstractions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository layer | Cosmos DB partition key management, query patterns | Direct Cosmos access in services would duplicate partition logic |

## Phase Status

| Phase | Status | Artifacts |
|-------|--------|-----------|
| Phase 0: Research | ✅ Complete | [research.md](research.md) |
| Phase 1: Design | ✅ Complete | [data-model.md](data-model.md), [quickstart.md](quickstart.md) |
| Phase 2: Tasks | ✅ Complete | [tasks.md](tasks.md) - 74 tasks, 6 user stories |

## Generated Artifacts

- **[research.md](research.md)** - 10 technology decisions covering FastAPI structure, Cosmos SDK, container design, ID generation, blob paths, SAS tokens, Service Bus messages, auth middleware, error handling
- **[data-model.md](data-model.md)** - Cosmos DB container schemas (5 containers), Pydantic models, status transitions, indexing policies
- **[quickstart.md](quickstart.md)** - Development setup, environment variables, Azure resource setup, testing instructions
- **Agent context updated** - `.github/agents/copilot-instructions.md` updated with Python 3.11, FastAPI, Azure Cosmos DB stack
