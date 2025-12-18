# Feature Specification: FastAPI Structure and API Implementation

**Feature Branch**: `004-fastapi-src`  
**Created**: December 17, 2025  
**Status**: Draft  
**Input**: User description: "Create proper FastAPI structure inside src folder and implement the OpenAPI spec API endpoints"  
**Depends On**: [002-case-api](../002-case-api/spec.md) - OpenAPI specification

## Overview

This feature creates a proper FastAPI project structure within the `src/` folder and implements all 21 API endpoints defined in the OpenAPI specification. The implementation uses the existing shared modules (`src/shared/`, `src/interfaces/`) and integrates with Azure Cosmos DB, Azure Blob Storage, and Azure Service Bus.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - FastAPI Project Structure (Priority: P1)

As a developer, I need a well-organized FastAPI project structure inside the `src/` folder so that I can efficiently develop, test, and maintain the API codebase.

**Why this priority**: Without proper structure, no API implementation can proceed. This is the foundation for all subsequent work.

**Independent Test**: Can be fully tested by verifying the folder structure exists, `main.py` starts without errors, and `/health` endpoint returns 200.

**Acceptance Scenarios**:

1. **Given** the project root, **When** I navigate to `src/api/`, **Then** I find a FastAPI application structure with `main.py`, `routes/`, `models/`, `services/`, `repositories/`, `middleware/`, and `config/`
2. **Given** the FastAPI app, **When** I run `uvicorn src.api.main:app`, **Then** the application starts on port 8000 without errors
3. **Given** a running FastAPI server, **When** I call `GET /api/v1/health`, **Then** I receive a 200 response with service health status
4. **Given** the FastAPI app, **When** I navigate to `/docs`, **Then** I see Swagger UI with OpenAPI documentation

---

### User Story 2 - Case CRUD API Endpoints (Priority: P1)

As a developer, I need the case management endpoints implemented so that clients can create, read, update, and delete underwriting cases.

**Why this priority**: Case operations are the foundation - documents cannot exist without cases. This enables the basic workflow.

**Independent Test**: Can be fully tested by calling case endpoints and verifying responses match OpenAPI schema.

**Acceptance Scenarios**:

1. **Given** a running API, **When** POST `/api/v1/cases` is called with valid JSON, **Then** a case is created with CASE-YYYYMM-NNNNNN ID and returns 201
2. **Given** an existing case, **When** GET `/api/v1/cases/{caseId}` is called, **Then** case details are returned with 200 status
3. **Given** an existing case, **When** PUT `/api/v1/cases/{caseId}` is called with status change, **Then** status transition is validated and case is updated
4. **Given** an existing case, **When** DELETE `/api/v1/cases/{caseId}` is called, **Then** the case is soft-deleted and returns 204
5. **Given** a soft-deleted case, **When** POST `/api/v1/cases/{caseId}/restore` is called, **Then** the case is restored to previous status
6. **Given** multiple cases, **When** GET `/api/v1/cases` is called with pagination, **Then** paginated list is returned with correct metadata

---

### User Story 3 - Document Upload and Management API (Priority: P1)

As a developer, I need document upload and management endpoints so that clients can upload documents to cases and manage them.

**Why this priority**: Document handling is essential for the underwriting workflow. Without documents, there's nothing to process.

**Independent Test**: Can be fully tested by uploading a file via multipart form and verifying document metadata is returned.

**Acceptance Scenarios**:

1. **Given** an existing case, **When** POST `/api/v1/cases/{caseId}/documents` is called with multipart file, **Then** document is uploaded and returns 201 with document details
2. **Given** a case with documents, **When** GET `/api/v1/cases/{caseId}/documents` is called, **Then** list of documents is returned
3. **Given** an existing document, **When** GET `/api/v1/cases/{caseId}/documents/{documentId}` is called, **Then** document details are returned
4. **Given** an existing document, **When** GET `/api/v1/cases/{caseId}/documents/{documentId}/download` is called, **Then** a time-limited download URL is returned
5. **Given** a file larger than 50 MB, **When** upload is attempted, **Then** 400 error is returned
6. **Given** a case with 50 documents, **When** upload is attempted, **Then** 409 error is returned

---

### User Story 4 - Processing Results API (Priority: P2)

As a developer, I need endpoints to retrieve extracted entities and summaries so the UI can display document processing results.

**Why this priority**: This delivers the core AI value - extracted insights from documents.

**Independent Test**: Can be fully tested by calling entity and summary endpoints for a document.

**Acceptance Scenarios**:

1. **Given** a processed document, **When** GET `/api/v1/cases/{caseId}/documents/{documentId}/entities` is called, **Then** list of entities with confidence scores is returned
2. **Given** an entity, **When** GET `.../entities/{entityId}/explain` is called, **Then** explanation with source context is returned
3. **Given** a processed document, **When** GET `/api/v1/cases/{caseId}/documents/{documentId}/summary` is called, **Then** document summary is returned
4. **Given** a summary, **When** GET `.../summary/explain` is called, **Then** explanation with contributing sections is returned
5. **Given** a document, **When** POST `.../reprocess` is called, **Then** processing is reset and returns 202

---

### User Story 5 - Middleware and Cross-Cutting Concerns (Priority: P2)

As a developer, I need authentication, error handling, and logging middleware so the API is secure and observable.

**Why this priority**: Security and observability are essential for production readiness.

**Independent Test**: Can be fully tested by calling endpoints without auth token and verifying 401, or triggering errors and verifying error response format.

**Acceptance Scenarios**:

1. **Given** an endpoint, **When** called without Authorization header, **Then** 401 Unauthorized is returned
2. **Given** an endpoint, **When** a validation error occurs, **Then** 422 with field-level details is returned
3. **Given** any request, **When** it is processed, **Then** correlation ID is added to response headers
4. **Given** any request, **When** it is processed, **Then** request/response is logged with correlation ID
5. **Given** an internal error, **When** it occurs, **Then** 500 with ErrorResponse schema is returned

---

### Edge Cases

- What happens when Cosmos DB is unavailable? Return 503 Service Unavailable with retry-after header
- What happens when Blob Storage upload fails mid-stream? Return 500 with error details, clean up partial data
- What happens when case ID format is invalid? Return 400 with validation error
- What happens when concurrent updates conflict? Return 409 Conflict with ETag mismatch details
- What happens when unsupported file type is uploaded? Return 400 with supported formats list

## Requirements *(mandatory)*

### Functional Requirements

#### Project Structure

- **FR-001**: FastAPI application MUST be located at `src/api/main.py` as the entry point
- **FR-002**: Routes MUST be organized in `src/api/routes/` with separate files for cases, documents, and processing
- **FR-003**: Pydantic models MUST be located in `src/api/models/` matching OpenAPI schemas
- **FR-004**: Business logic MUST be in `src/api/services/` separate from route handlers
- **FR-005**: Cosmos DB operations MUST be in `src/api/repositories/` with partition key handling
- **FR-006**: Middleware MUST be in `src/api/middleware/` for auth, logging, error handling
- **FR-007**: Configuration MUST be in `src/api/config/settings.py` using Pydantic BaseSettings

#### API Compliance

- **FR-008**: All 21 endpoints MUST match paths defined in `specs/002-case-api/contracts/openapi.yaml`
- **FR-009**: Request/response schemas MUST match OpenAPI component schemas exactly
- **FR-010**: Status codes MUST match OpenAPI response definitions
- **FR-011**: API MUST be versioned with `/api/v1` prefix
- **FR-012**: OpenAPI docs MUST be served at `/docs` (Swagger) and `/redoc`

#### Integration

- **FR-013**: System MUST integrate with existing `src/shared/` models and utilities
- **FR-014**: System MUST integrate with existing `src/interfaces/` for processing contracts
- **FR-015**: System MUST use Azure Cosmos DB for data persistence
- **FR-016**: System MUST use Azure Blob Storage for document files
- **FR-017**: System MUST publish messages to Azure Service Bus on document upload

#### Authentication & Security

- **FR-018**: All endpoints except /health MUST require Bearer token authentication
- **FR-019**: Tokens MUST be validated against Azure AD
- **FR-020**: User identity MUST be extracted from token for audit logging

### Key Entities

- **Case**: Underwriting case with client info, status, and metadata (partition key: case_id)
- **Document**: Uploaded file with processing status and classification (partition key: case_id)
- **Entity**: Extracted data point from document with confidence score (partition key: document_id)
- **Summary**: AI-generated document summary with key points (partition key: document_id)

## Assumptions

- Azure Cosmos DB containers are provisioned (cases, documents, entities, summaries, counters)
- Azure Blob Storage container is provisioned for document files
- Azure Service Bus queue is provisioned for processing messages
- Azure AD application is configured for token validation
- Existing `src/shared/` and `src/interfaces/` modules are compatible with new structure
- Python 3.11+ environment with pip package management

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 21 API endpoints pass contract tests against OpenAPI specification
- **SC-002**: FastAPI application starts without errors and serves `/docs` endpoint
- **SC-003**: Health check endpoint responds in under 100ms
- **SC-004**: Case CRUD operations respond in under 200ms p95
- **SC-005**: File uploads up to 50 MB complete within 30 seconds
- **SC-006**: All error responses conform to ErrorResponse schema
- **SC-007**: 100% of Pydantic models validate against OpenAPI schema definitions
- **SC-008**: Project structure follows plan.md specification exactly
