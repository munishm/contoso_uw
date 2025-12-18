# Implementation Plan: Underwriting Case Management API

**Branch**: `002-case-api` | **Date**: 2025-12-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-case-api/spec.md`

## Summary

This plan implements a RESTful API for underwriting case management, enabling underwriters to create cases, upload documents (stored in Azure Blob Storage), and retrieve processing results (classification, entity extraction, summaries). The API follows event-driven architecture with Azure Service Bus queues triggering document processing workflows. The design aligns with the existing Python/FastAPI backend structure and integrates with existing document processing components.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic v2, Azure SDK (azure-storage-blob, azure-servicebus, azure-cosmos)  
**Storage**: Azure Blob Storage (documents), Azure Cosmos DB (structured data)  
**Testing**: pytest, pytest-asyncio, pytest-cov  
**Target Platform**: Linux server (Azure App Service / Container Apps)  
**Project Type**: Web application (backend API)  
**Performance Goals**: <5 min full processing, <1 sec API response, 50 concurrent cases  
**Constraints**: 50 MB max file size, 50 docs per case, Azure-only services (POC constraint)  
**Scale/Scope**: POC phase - single tenant, team-level usage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle 1: Compliance & Regulatory Adherence First** - API endpoints designed with audit logging, all data encrypted, PII handled per regulations
- [x] **Principle 2: Human-in-the-Loop (HITL) Mandatory** - API provides decision support only; underwriters review all AI outputs before decisions
- [x] **Principle 3: Full Auditability & Source Traceability** - All entities include source document ID and page references; case history tracked
- [x] **Principle 4: Scalable Architecture with Multi-Language Readiness** - Data schemas support language metadata; English-only for POC
- [x] **Principle 5: Security by Design & Zero Trust** - RBAC enforced, TLS 1.3+, Azure Key Vault for secrets, MFA (handled by auth layer)
- [x] **Principle 6: Performance & Scalability Targets** - POC targets: <5 min processing, <30 sec classification, architecture supports 10+ concurrent cases
- [x] **Principle 7: Continuous Model Monitoring** - Processing results include confidence scores; feedback capture designed into API
- [x] **Principle 8: Reusable Patterns & Extensibility** - Generic case/document patterns; configurable document types via metadata
- [x] **Principle 9: Azure-Native Architecture** - Exclusive use of Azure services: Blob Storage, Service Bus, SQL Database, OpenAI

## Project Structure

### Documentation (this feature)

```text
specs/002-case-api/
├── plan.md              # This file
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - entity schemas
├── quickstart.md        # Phase 1 output - development setup
├── contracts/           # Phase 1 output - OpenAPI specification
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── cases.py          # Case CRUD endpoints
│   │   │   └── documents.py      # Document upload/retrieval endpoints
│   │   ├── __init__.py
│   │   └── dependencies.py       # FastAPI dependencies (auth, db)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── case.py               # Case SQLAlchemy model
│   │   └── document.py           # Document SQLAlchemy model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── case_service.py       # Case business logic
│   │   ├── document_service.py   # Document business logic
│   │   ├── storage_service.py    # Azure Blob Storage integration
│   │   └── queue_service.py      # Azure Service Bus integration
│   └── config/
│       ├── __init__.py
│       └── settings.py           # Environment configuration
└── tests/
    ├── contract/
    │   └── test_api_contracts.py # OpenAPI contract tests
    ├── integration/
    │   ├── test_cases_api.py     # Case API integration tests
    │   └── test_documents_api.py # Document API integration tests
    └── unit/
        ├── test_case_service.py
        └── test_document_service.py

src/shared/models/
├── case.py                       # Case Pydantic schemas (shared)
└── document.py                   # Document Pydantic schemas (existing, extended)
```

**Structure Decision**: Extending existing `backend/` structure with new routes under `api/routes/`. Shared Pydantic models in `src/shared/models/` for cross-component consistency. Follows existing project patterns from `001-project-structure`.

## Complexity Tracking

> No constitution violations requiring justification. Design follows existing patterns.
