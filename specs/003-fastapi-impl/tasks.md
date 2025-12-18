# Tasks: FastAPI Implementation of Case Management API

**Input**: Design documents from `/specs/003-fastapi-impl/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Not explicitly requested in feature specification. Skipping test tasks.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/` for all API code
- **Tests**: `backend/tests/` for test files

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Initialize FastAPI project structure and dependencies

- [ ] T001 Create backend project directory structure per plan.md in backend/src/
- [ ] T002 Create pyproject.toml with FastAPI, Pydantic v2, azure-cosmos, azure-storage-blob, azure-servicebus dependencies in backend/pyproject.toml
- [ ] T003 [P] Create .env.example with all required environment variables in backend/.env.example
- [ ] T004 [P] Configure pytest and pytest-asyncio in backend/pyproject.toml
- [ ] T005 [P] Create __init__.py files for all packages in backend/src/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Configuration & Settings

- [ ] T006 Implement Settings class with Pydantic BaseSettings in backend/src/config/settings.py
- [ ] T007 [P] Create config __init__.py exporting settings instance in backend/src/config/__init__.py

### Pydantic Models (Shared)

- [ ] T008 [P] Create enums (CaseStatus, ProcessingStatus, DocumentType) in backend/src/models/enums.py
- [ ] T009 [P] Create common models (ErrorResponse, ValidationErrorResponse, HealthResponse, PaginatedResponse) in backend/src/models/common.py
- [ ] T010 [P] Create case models (CaseCreateRequest, CaseUpdateRequest, CaseSummaryResponse, CaseDetailResponse, CaseListResponse) in backend/src/models/case.py
- [ ] T011 [P] Create document models (DocumentSummaryResponse, DocumentDetailResponse, DocumentListResponse) in backend/src/models/document.py
- [ ] T012 [P] Create entity models (BoundingBox, EntityResponse, EntityExplanationResponse) in backend/src/models/entity.py
- [ ] T013 [P] Create summary models (SourceSection, SummaryResponse, SummaryExplanationResponse) in backend/src/models/summary.py
- [ ] T014 Create models __init__.py exporting all models in backend/src/models/__init__.py

### Repository Layer (Cosmos DB)

- [ ] T015 Implement BaseRepository with async CosmosClient connection in backend/src/repositories/base.py
- [ ] T016 Implement CounterRepository for atomic case ID generation in backend/src/repositories/counter_repository.py
- [ ] T017 [P] Implement CaseRepository (create, get, update, delete, list, restore) in backend/src/repositories/case_repository.py
- [ ] T018 [P] Implement DocumentRepository (create, get, update, list by case) in backend/src/repositories/document_repository.py
- [ ] T019 [P] Implement EntityRepository (get by document, get by id) in backend/src/repositories/entity_repository.py
- [ ] T020 [P] Implement SummaryRepository (get by document) in backend/src/repositories/summary_repository.py
- [ ] T021 Create repositories __init__.py exporting all repositories in backend/src/repositories/__init__.py

### Middleware

- [ ] T022 Implement Bearer token authentication middleware in backend/src/middleware/auth.py
- [ ] T023 [P] Implement global exception handler mapping to ErrorResponse in backend/src/middleware/error_handler.py
- [ ] T024 [P] Implement correlation ID injection middleware in backend/src/middleware/correlation.py
- [ ] T025 [P] Implement request/response logging middleware in backend/src/middleware/logging.py
- [ ] T026 Create middleware __init__.py exporting all middleware in backend/src/middleware/__init__.py

### External Service Clients

- [ ] T027 Implement StorageService for Azure Blob Storage operations in backend/src/services/storage_service.py
- [ ] T028 [P] Implement QueueService for Azure Service Bus operations in backend/src/services/queue_service.py

### FastAPI App Entry Point

- [ ] T029 Create FastAPI application with middleware, CORS, and exception handlers in backend/src/main.py
- [ ] T030 Implement dependency injection functions (get_db, get_auth, get_services) in backend/src/api/dependencies.py
- [ ] T031 [P] Implement health check endpoint at GET /api/v1/health in backend/src/api/routes/health.py
- [ ] T032 Create routes __init__.py and register routers in backend/src/api/routes/__init__.py
- [ ] T033 Create api __init__.py in backend/src/api/__init__.py

**Checkpoint**: Foundation ready - verify app starts and health check returns 200

---

## Phase 3: User Story 1 - Case CRUD Operations (Priority: P1) 🎯 MVP

**Goal**: Create, read, update, delete underwriting cases with Cosmos DB persistence

**Independent Test**: Call case endpoints (POST, GET, PUT, DELETE /cases) and verify Cosmos DB persistence

### Implementation for User Story 1

- [ ] T034 [US1] Implement CaseService with case ID generation logic in backend/src/services/case_service.py
- [ ] T035 [US1] Implement POST /api/v1/cases endpoint (create case) in backend/src/api/routes/cases.py
- [ ] T036 [US1] Implement GET /api/v1/cases/{caseId} endpoint (get case details) in backend/src/api/routes/cases.py
- [ ] T037 [US1] Implement PUT /api/v1/cases/{caseId} endpoint (update case with status validation) in backend/src/api/routes/cases.py
- [ ] T038 [US1] Implement DELETE /api/v1/cases/{caseId} endpoint (soft-delete) in backend/src/api/routes/cases.py
- [ ] T039 [US1] Implement POST /api/v1/cases/{caseId}/restore endpoint (restore deleted case) in backend/src/api/routes/cases.py
- [ ] T040 [US1] Add status transition validation in CaseService per data-model.md rules in backend/src/services/case_service.py
- [ ] T041 [US1] Register cases router in main.py in backend/src/main.py

**Checkpoint**: User Story 1 complete - can create/read/update/delete cases with proper ID generation and status validation

---

## Phase 4: User Story 2 - Document Upload and Storage (Priority: P1)

**Goal**: Upload documents to cases via multipart form with Azure Blob Storage and Service Bus queue

**Independent Test**: Upload file via POST /cases/{caseId}/documents and verify blob exists in storage

### Implementation for User Story 2

- [ ] T042 [US2] Implement DocumentService with upload orchestration in backend/src/services/document_service.py
- [ ] T043 [US2] Implement POST /api/v1/cases/{caseId}/documents endpoint (multipart upload) in backend/src/api/routes/documents.py
- [ ] T044 [US2] Add file size validation (max 50 MB) in DocumentService in backend/src/services/document_service.py
- [ ] T045 [US2] Add document count validation (max 50 per case) in DocumentService in backend/src/services/document_service.py
- [ ] T046 [US2] Add content-type validation for allowed file types in DocumentService in backend/src/services/document_service.py
- [ ] T047 [US2] Implement streaming upload to Azure Blob Storage in StorageService in backend/src/services/storage_service.py
- [ ] T048 [US2] Implement queue message publishing for document processing in QueueService in backend/src/services/queue_service.py
- [ ] T049 [US2] Register documents router in main.py in backend/src/main.py

**Checkpoint**: User Story 2 complete - can upload documents with validation, blob storage, and queue notification

---

## Phase 5: User Story 3 - Document Retrieval and Download (Priority: P2)

**Goal**: List documents for a case and generate secure download URLs

**Independent Test**: Call GET /cases/{caseId}/documents and generate download URL that retrieves file

### Implementation for User Story 3

- [ ] T050 [US3] Implement GET /api/v1/cases/{caseId}/documents endpoint (list documents) in backend/src/api/routes/documents.py
- [ ] T051 [US3] Implement GET /api/v1/cases/{caseId}/documents/{documentId} endpoint (document details) in backend/src/api/routes/documents.py
- [ ] T052 [US3] Implement SAS URL generation in StorageService in backend/src/services/storage_service.py
- [ ] T053 [US3] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/download endpoint (generate download URL) in backend/src/api/routes/documents.py
- [ ] T054 [US3] Implement PATCH /api/v1/cases/{caseId}/documents/{documentId} endpoint (update metadata) in backend/src/api/routes/documents.py

**Checkpoint**: User Story 3 complete - can list documents and generate secure download URLs

---

## Phase 6: User Story 4 - Processing Results Endpoints (Priority: P2)

**Goal**: Retrieve extracted entities and summaries for processed documents

**Independent Test**: Call entity and summary endpoints for a document and verify response structure

### Implementation for User Story 4

- [ ] T055 [US4] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/entities endpoint in backend/src/api/routes/processing.py
- [ ] T056 [US4] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/entities/{entityId} endpoint in backend/src/api/routes/processing.py
- [ ] T057 [US4] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/entities/{entityId}/explain endpoint in backend/src/api/routes/processing.py
- [ ] T058 [US4] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/summary endpoint in backend/src/api/routes/processing.py
- [ ] T059 [US4] Implement GET /api/v1/cases/{caseId}/documents/{documentId}/summary/explain endpoint in backend/src/api/routes/processing.py
- [ ] T060 [US4] Register processing router in main.py in backend/src/main.py

**Checkpoint**: User Story 4 complete - can retrieve entities, summaries, and explanations

---

## Phase 7: User Story 5 - Case Listing and Filtering (Priority: P2)

**Goal**: List cases with pagination and filtering for UI dashboard

**Independent Test**: Create multiple cases and verify pagination and status filter work correctly

### Implementation for User Story 5

- [ ] T061 [US5] Implement GET /api/v1/cases endpoint with pagination in backend/src/api/routes/cases.py
- [ ] T062 [US5] Add status filter query parameter to case listing in backend/src/api/routes/cases.py
- [ ] T063 [US5] Add include_deleted query parameter to case listing in backend/src/api/routes/cases.py
- [ ] T064 [US5] Add sort parameters (sort_by, sort_order) to case listing in backend/src/api/routes/cases.py
- [ ] T065 [US5] Implement paginated query in CaseRepository in backend/src/repositories/case_repository.py

**Checkpoint**: User Story 5 complete - can list cases with pagination, filtering, and sorting

---

## Phase 8: User Story 6 - Document Reprocessing (Priority: P3)

**Goal**: Trigger reprocessing of documents when processing fails or needs refresh

**Independent Test**: Call POST /cases/{caseId}/documents/{documentId}/reprocess and verify queue message sent

### Implementation for User Story 6

- [ ] T066 [US6] Implement POST /api/v1/cases/{caseId}/documents/{documentId}/reprocess endpoint in backend/src/api/routes/documents.py
- [ ] T067 [US6] Add reprocess logic to DocumentService (reset status, queue message) in backend/src/services/document_service.py

**Checkpoint**: User Story 6 complete - can trigger document reprocessing

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation

- [ ] T068 [P] Add OpenAPI metadata (title, description, version) to FastAPI app in backend/src/main.py
- [ ] T069 [P] Verify all 21 endpoints match OpenAPI spec from 002-case-api/contracts/openapi.yaml
- [ ] T070 [P] Add response_model to all endpoints for automatic serialization in backend/src/api/routes/
- [ ] T071 [P] Configure CORS middleware with allowed origins in backend/src/main.py
- [ ] T072 [P] Add API version prefix /api/v1 to all routes in backend/src/main.py
- [ ] T073 Create services __init__.py exporting all services in backend/src/services/__init__.py
- [ ] T074 Run quickstart.md validation - verify app starts and health check works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 (Case CRUD) and US2 (Document Upload) are both P1 - can run in parallel
  - US3, US4, US5 are P2 - can start after Foundational
  - US6 is P3 - lowest priority
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Parallel With |
|-------|----------|------------|-------------------|
| US1 - Case CRUD | P1 | Foundational | US2 |
| US2 - Document Upload | P1 | Foundational | US1 |
| US3 - Document Retrieval | P2 | Foundational | US4, US5 |
| US4 - Processing Results | P2 | Foundational | US3, US5 |
| US5 - Case Listing | P2 | Foundational | US3, US4 |
| US6 - Reprocessing | P3 | Foundational | All above |

### Within Each User Story

- Models before services
- Services before routes
- Core implementation before integration
- Story complete before checkpoint validation

### Parallel Opportunities

```bash
# Phase 1 parallel tasks:
T003, T004, T005  # All independent setup files

# Phase 2 parallel tasks - Models:
T008, T009, T010, T011, T012, T013  # All model files

# Phase 2 parallel tasks - Repositories:
T017, T018, T019, T020  # After T015 (BaseRepository)

# Phase 2 parallel tasks - Middleware:
T023, T024, T025  # After T022 (auth first)

# Phase 2 parallel tasks - Services:
T027, T028  # External service clients

# User Stories in parallel (with team):
US1 + US2  # Both P1, no dependencies
US3 + US4 + US5  # All P2, no cross-dependencies
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Case CRUD)
4. Complete Phase 4: User Story 2 (Document Upload)
5. **STOP and VALIDATE**: Test case creation and document upload flow
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Case CRUD) → Test → Deploy (cases only)
3. Add US2 (Document Upload) → Test → Deploy (MVP!)
4. Add US3 (Document Retrieval) → Test → Deploy
5. Add US4 (Processing Results) → Test → Deploy
6. Add US5 (Case Listing) → Test → Deploy
7. Add US6 (Reprocessing) → Test → Deploy (Full API)

### Single Developer Strategy

Execute in order: T001 → T074

1. Phase 1 tasks in order
2. Phase 2 tasks (skip [P] parallelism, do sequentially)
3. Phase 3 (US1) completely
4. Phase 4 (US2) completely
5. Phase 5 (US3) completely
6. Phase 6 (US4) completely
7. Phase 7 (US5) completely
8. Phase 8 (US6) completely
9. Phase 9 polish tasks

---

## Notes

- Total tasks: 74
- Parallel opportunities: 28 tasks marked [P]
- All paths are absolute from repository root
- Each task should be committed separately or in logical groups
- Use Cosmos DB emulator for local development (see quickstart.md)
- Verify health check (T031) before proceeding to user stories
