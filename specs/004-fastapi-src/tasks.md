# Tasks: FastAPI Structure and API Implementation

**Input**: Design documents from `/specs/004-fastapi-src/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Tests are OPTIONAL - not explicitly requested in the feature specification. Only minimal validation tests included for structure verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:

- Source: `src/api/` (FastAPI application)
- Tests: `tests/api/` (API tests)
- Existing modules: `src/shared/`, `src/interfaces/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create `src/api/` directory structure with `__init__.py` files per plan.md
- [x] T002 [P] Create `pyproject.toml` API extras with FastAPI dependencies
- [x] T003 [P] Create `.env.example` with all environment variables from quickstart.md
- [x] T004 [P] Create `tests/api/` directory structure with `conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Configuration & Settings

- [x] T005 Implement settings module in `src/api/config/__init__.py`
- [x] T006 Implement `Settings` class with Pydantic BaseSettings in `src/api/config/settings.py`

### Enums & Common Models

- [x] T007 [P] Create status enumerations in `src/api/models/enums.py` (CaseStatus, ProcessingStatus, DocumentType)
- [x] T008 [P] Create common models in `src/api/models/common.py` (ErrorResponse, ValidationErrorResponse, HealthResponse)

### Repository Layer (Cosmos DB)

- [x] T009 Create base repository with async Cosmos DB client in `src/api/repositories/base.py`
- [x] T010 [P] Implement counter repository for case ID generation in `src/api/repositories/counter_repository.py`
- [x] T011 [P] Implement case repository in `src/api/repositories/case_repository.py`
- [x] T012 [P] Implement document repository in `src/api/repositories/document_repository.py`
- [x] T013 [P] Implement entity repository in `src/api/repositories/entity_repository.py`
- [x] T014 [P] Implement summary repository in `src/api/repositories/summary_repository.py`

### External Services

- [x] T015 [P] Implement Azure Blob Storage service in `src/api/services/storage_service.py`
- [x] T016 [P] Implement Azure Service Bus queue service in `src/api/services/queue_service.py`

### Middleware

- [x] T017 [P] Implement correlation ID middleware in `src/api/middleware/correlation.py`
- [x] T018 [P] Implement global error handler in `src/api/middleware/error_handler.py`
- [x] T019 [P] Implement request/response logging in `src/api/middleware/logging.py`
- [x] T020 Implement Bearer token auth middleware in `src/api/middleware/auth.py`

### Dependency Injection

- [x] T021 Create FastAPI dependencies module in `src/api/dependencies.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - FastAPI Project Structure (Priority: P1) 🎯 MVP

**Goal**: Well-organized FastAPI project structure with health endpoint and Swagger docs

**Independent Test**: Run `uvicorn src.api.main:app` and verify `/health` returns 200, `/docs` shows Swagger UI

### Implementation for User Story 1

- [x] T022 [US1] Create FastAPI app entry point in `src/api/main.py` with lifespan, middleware, and routers
- [x] T023 [US1] Implement health check endpoint in `src/api/routes/health.py` with service status checks
- [x] T024 [US1] Configure OpenAPI metadata and `/docs` endpoint in `src/api/main.py`
- [x] T025 [US1] Add CORS middleware configuration in `src/api/main.py`
- [x] T026 [US1] Create routes `__init__.py` with router exports in `src/api/routes/__init__.py`
- [x] T027 [US1] Verify application starts with `uvicorn src.api.main:app --reload`

**Checkpoint**: User Story 1 complete - Application structure validated, health check works, Swagger UI accessible

---

## Phase 4: User Story 2 - Case CRUD API Endpoints (Priority: P1)

**Goal**: Full case management (create, read, update, delete, list, restore, status history) - 7 endpoints

**Independent Test**: POST `/api/v1/cases` creates case with CASE-YYYYMM-NNNNNN ID; GET returns case details

### Models for User Story 2

- [x] T028 [P] [US2] Create case request/response models in `src/api/models/case.py`

### Services for User Story 2

- [x] T029 [US2] Implement case business logic service in `src/api/services/case_service.py`

### Endpoints for User Story 2 (7 endpoints)

- [x] T030 [US2] Implement `GET /api/v1/cases` (list cases with pagination) in `src/api/routes/cases.py`
- [x] T031 [US2] Implement `POST /api/v1/cases` (create case) in `src/api/routes/cases.py`
- [x] T032 [US2] Implement `GET /api/v1/cases/{caseId}` (get case details) in `src/api/routes/cases.py`
- [x] T033 [US2] Implement `PUT /api/v1/cases/{caseId}` (update case) in `src/api/routes/cases.py`
- [x] T034 [US2] Implement `DELETE /api/v1/cases/{caseId}` (soft delete) in `src/api/routes/cases.py`
- [x] T035 [US2] Implement `POST /api/v1/cases/{caseId}/restore` (restore deleted case) in `src/api/routes/cases.py`
- [x] T036 [US2] Implement `GET /api/v1/cases/{caseId}/status-history` in `src/api/routes/cases.py`
- [x] T037 [US2] Add status transition validation in case service per data-model.md rules
- [x] T038 [US2] Register cases router in `src/api/main.py`

**Checkpoint**: User Story 2 complete - All 7 case endpoints functional, CASE-YYYYMM-NNNNNN IDs generated

---

## Phase 5: User Story 3 - Document Upload and Management API (Priority: P1)

**Goal**: Document upload, listing, retrieval, download URL generation - 6 endpoints

**Independent Test**: POST multipart file to `/api/v1/cases/{caseId}/documents` returns document metadata with 201

### Models for User Story 3

- [x] T039 [P] [US3] Create document request/response models in `src/api/models/document.py`

### Services for User Story 3

- [x] T040 [US3] Implement document business logic service in `src/api/services/document_service.py`

### Endpoints for User Story 3 (6 endpoints)

- [x] T041 [US3] Implement `GET /api/v1/cases/{caseId}/documents` (list documents) in `src/api/routes/documents.py`
- [x] T042 [US3] Implement `POST /api/v1/cases/{caseId}/documents` (upload document) in `src/api/routes/documents.py`
- [x] T043 [US3] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}` (get document) in `src/api/routes/documents.py`
- [x] T044 [US3] Implement `PUT /api/v1/cases/{caseId}/documents/{documentId}` (update metadata) in `src/api/routes/documents.py`
- [x] T045 [US3] Implement `DELETE /api/v1/cases/{caseId}/documents/{documentId}` (delete document) in `src/api/routes/documents.py`
- [x] T046 [US3] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}/download` (SAS URL) in `src/api/routes/documents.py`
- [x] T047 [US3] Add file size validation (50 MB max) and document limit (50 per case) in document service
- [x] T048 [US3] Implement Service Bus message publishing on document upload in document service
- [x] T049 [US3] Register documents router in `src/api/main.py`

**Checkpoint**: User Story 3 complete - Document upload/download works, Service Bus messages published

---

## Phase 6: User Story 4 - Processing Results API (Priority: P2)

**Goal**: Entity extraction results, summaries, and explanations - 5 endpoints

**Independent Test**: GET `/api/v1/cases/{caseId}/documents/{documentId}/entities` returns entity list

### Models for User Story 4

- [x] T050 [P] [US4] Create entity models in `src/api/models/entity.py`
- [x] T051 [P] [US4] Create summary models in `src/api/models/summary.py`

### Services for User Story 4

- [x] T052 [US4] Implement processing results service in `src/api/services/processing_service.py`

### Endpoints for User Story 4 (5 endpoints)

- [x] T053 [US4] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}/entities` in `src/api/routes/processing.py`
- [x] T054 [US4] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}/entities/{entityId}/explain` in `src/api/routes/processing.py`
- [x] T055 [US4] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}/summary` in `src/api/routes/processing.py`
- [x] T056 [US4] Implement `GET /api/v1/cases/{caseId}/documents/{documentId}/summary/explain` in `src/api/routes/processing.py`
- [x] T057 [US4] Implement `POST /api/v1/cases/{caseId}/documents/{documentId}/reprocess` in `src/api/routes/processing.py`
- [x] T058 [US4] Register processing router in `src/api/main.py`

**Checkpoint**: User Story 4 complete - All processing result endpoints functional

---

## Phase 7: User Story 5 - Middleware and Cross-Cutting Concerns (Priority: P2)

**Goal**: Production-ready middleware for auth, errors, logging, correlation IDs

**Independent Test**: Request without Bearer token returns 401; error returns ErrorResponse schema

### Implementation for User Story 5

- [x] T059 [US5] Integrate auth middleware into request pipeline in `src/api/main.py`
- [x] T060 [US5] Add Azure AD JWKS token validation in `src/api/middleware/auth.py`
- [x] T061 [US5] Ensure all error responses conform to ErrorResponse schema
- [x] T062 [US5] Add correlation ID to all log entries via middleware
- [x] T063 [US5] Add request/response body logging (with PII redaction) in logging middleware
- [x] T064 [US5] Configure Application Insights telemetry integration

**Checkpoint**: User Story 5 complete - Auth enforced, consistent error handling, full observability

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [x] T065 [P] Create API models `__init__.py` with public exports in `src/api/models/__init__.py`
- [x] T066 [P] Create services `__init__.py` with public exports in `src/api/services/__init__.py`
- [x] T067 [P] Create repositories `__init__.py` with public exports in `src/api/repositories/__init__.py`
- [x] T068 [P] Create middleware `__init__.py` with public exports in `src/api/middleware/__init__.py`
- [x] T069 Verify all 21 OpenAPI endpoints match `specs/002-case-api/contracts/openapi.yaml`
- [x] T070 Ensure Pydantic models match OpenAPI component schemas exactly
- [x] T071 Run quickstart.md validation - verify setup instructions work
- [x] T072 Update project README.md with API documentation links

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup ──────────────┐
                             ▼
Phase 2: Foundational ───────┤ BLOCKS ALL USER STORIES
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
Phase 3: US1 (Structure)     │                   │
         │                   │                   │
         ▼                   ▼                   ▼
Phase 4: US2 (Cases)    Phase 5: US3 (Docs)    Phase 6: US4 (Results)
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    Phase 7: US5 (Middleware)
                             │
                             ▼
                    Phase 8: Polish
```

### User Story Dependencies

| User Story | Depends On | Can Parallel With |
|------------|------------|-------------------|
| US1 (Structure) | Foundational | None (first story) |
| US2 (Cases) | US1 (needs main.py) | US3, US4 (different routes) |
| US3 (Documents) | US1 (needs main.py) | US2, US4 (different routes) |
| US4 (Results) | US1 (needs main.py) | US2, US3 (different routes) |
| US5 (Middleware) | US1-US4 (applies across all) | None (integrates with all) |

### Within Each User Story

- Models before services
- Services before endpoints
- Repository layer must be complete (Phase 2) before any endpoints
- Core implementation before integration

### Parallel Opportunities

- All Phase 1 tasks marked [P] can run in parallel
- All Phase 2 repository tasks (T010-T014) can run in parallel
- All Phase 2 middleware tasks (T017-T019) can run in parallel
- User Stories 2, 3, 4 can proceed in parallel once US1 is complete
- All Phase 8 init file tasks can run in parallel

---

## Parallel Example: Phase 2 Repositories

```bash
# Launch all repository implementations together:
Task T010: "Implement counter repository in src/api/repositories/counter_repository.py"
Task T011: "Implement case repository in src/api/repositories/case_repository.py"
Task T012: "Implement document repository in src/api/repositories/document_repository.py"
Task T013: "Implement entity repository in src/api/repositories/entity_repository.py"
Task T014: "Implement summary repository in src/api/repositories/summary_repository.py"
```

## Parallel Example: User Story Routes (After US1)

```bash
# After Phase 3 (US1) complete, launch in parallel:
Task T030: "Implement GET /api/v1/cases (list cases) in src/api/routes/cases.py"
Task T041: "Implement GET /api/v1/cases/{caseId}/documents in src/api/routes/documents.py"
Task T053: "Implement GET /api/v1/cases/{caseId}/documents/{documentId}/entities in src/api/routes/processing.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - Project structure, health check
4. Complete Phase 4: US2 - Case CRUD
5. **STOP and VALIDATE**: Test cases API independently
6. Deploy/demo MVP with case management

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Structure) → Health check works → Deploy
3. Add US2 (Cases) → Case CRUD works → Deploy (MVP!)
4. Add US3 (Documents) → Upload/download works → Deploy
5. Add US4 (Results) → Full processing results → Deploy
6. Add US5 (Middleware) → Production-ready → Deploy

### Task Count Summary

| Phase | Task Range | Count | Parallel Tasks |
|-------|-----------|-------|----------------|
| Phase 1: Setup | T001-T004 | 4 | 3 |
| Phase 2: Foundational | T005-T021 | 17 | 13 |
| Phase 3: US1 (P1) | T022-T027 | 6 | 0 |
| Phase 4: US2 (P1) | T028-T038 | 11 | 1 |
| Phase 5: US3 (P1) | T039-T049 | 11 | 1 |
| Phase 6: US4 (P2) | T050-T058 | 9 | 2 |
| Phase 7: US5 (P2) | T059-T064 | 6 | 0 |
| Phase 8: Polish | T065-T072 | 8 | 4 |
| **TOTAL** | | **72** | **24** |

---

## Endpoint Coverage

All 21 OpenAPI endpoints mapped to tasks:

| # | Endpoint | Method | Task | Story |
|---|----------|--------|------|-------|
| 1 | `/health` | GET | T023 | US1 |
| 2 | `/cases` | GET | T030 | US2 |
| 3 | `/cases` | POST | T031 | US2 |
| 4 | `/cases/{caseId}` | GET | T032 | US2 |
| 5 | `/cases/{caseId}` | PUT | T033 | US2 |
| 6 | `/cases/{caseId}` | DELETE | T034 | US2 |
| 7 | `/cases/{caseId}/restore` | POST | T035 | US2 |
| 8 | `/cases/{caseId}/status-history` | GET | T036 | US2 |
| 9 | `/cases/{caseId}/documents` | GET | T041 | US3 |
| 10 | `/cases/{caseId}/documents` | POST | T042 | US3 |
| 11 | `/cases/{caseId}/documents/{documentId}` | GET | T043 | US3 |
| 12 | `/cases/{caseId}/documents/{documentId}` | PUT | T044 | US3 |
| 13 | `/cases/{caseId}/documents/{documentId}` | DELETE | T045 | US3 |
| 14 | `/cases/{caseId}/documents/{documentId}/download` | GET | T046 | US3 |
| 15 | `/cases/{caseId}/documents/{documentId}/entities` | GET | T053 | US4 |
| 16 | `/cases/{caseId}/documents/{documentId}/entities/{entityId}/explain` | GET | T054 | US4 |
| 17 | `/cases/{caseId}/documents/{documentId}/summary` | GET | T055 | US4 |
| 18 | `/cases/{caseId}/documents/{documentId}/summary/explain` | GET | T056 | US4 |
| 19 | `/cases/{caseId}/documents/{documentId}/reprocess` | POST | T057 | US4 |
| 20 | OpenAPI `/docs` | GET | T024 | US1 |
| 21 | OpenAPI `/redoc` | GET | T024 | US1 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All paths are relative to project root `/home/ksharma/microsoft/contoso/poc/Contoso_IWPB_UW`
