# Feature Specification: FastAPI Implementation of Case Management API

**Feature Branch**: `003-fastapi-impl`  
**Created**: December 17, 2025  
**Status**: Draft  
**Input**: User description: "Implement the Case Management OpenAPI specification as FastAPI Python code with Cosmos DB integration, Azure Blob Storage for documents, and Azure Service Bus for event-driven processing"  
**Depends On**: [002-case-api](../002-case-api/spec.md) - OpenAPI specification

## Overview

This feature implements the Underwriting Case Management API defined in [002-case-api/contracts/openapi.yaml](../002-case-api/contracts/openapi.yaml) using FastAPI. The implementation includes all 21 endpoints for case management, document handling, and processing results retrieval, with Azure Cosmos DB for data persistence, Azure Blob Storage for document files, and Azure Service Bus for event-driven document processing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Case CRUD Operations (Priority: P1)

As a developer integrating with the API, I need to create, read, update, and delete underwriting cases so the frontend can manage the case lifecycle.

**Why this priority**: Case operations are the foundation - documents cannot exist without cases. This enables the basic workflow.

**Independent Test**: Can be fully tested by calling case endpoints and verifying Cosmos DB persistence. Delivers core case management capability.

**Acceptance Scenarios**:

1. **Given** a running FastAPI server, **When** POST `/cases` is called with valid JSON body, **Then** a case is created in Cosmos DB with generated CASE-YYYYMM-NNNNNN ID and returned with 201 status
2. **Given** an existing case, **When** GET `/cases/{caseId}` is called, **Then** the case details are returned from Cosmos DB with 200 status
3. **Given** an existing case, **When** PUT `/cases/{caseId}` is called with status change, **Then** status transition is validated and case is updated
4. **Given** an existing case, **When** DELETE `/cases/{caseId}` is called, **Then** the case is soft-deleted (deleted_at timestamp set) and returns 204
5. **Given** a soft-deleted case, **When** POST `/cases/{caseId}/restore` is called, **Then** the case is restored to previous status

---

### User Story 2 - Document Upload and Storage (Priority: P1)

As a developer, I need to upload documents to cases via multipart form so documents are stored in Azure Blob Storage and processing is triggered.

**Why this priority**: Document upload is essential for the underwriting workflow. Without documents, there's nothing to process.

**Independent Test**: Can be fully tested by uploading a file and verifying it exists in Blob Storage with correct metadata in Cosmos DB.

**Acceptance Scenarios**:

1. **Given** an existing case, **When** POST `/cases/{caseId}/documents` is called with multipart file upload, **Then** file is stored in Azure Blob Storage and document record created in Cosmos DB with 201 status
2. **Given** a successful upload, **When** the upload completes, **Then** a message is sent to Azure Service Bus to trigger processing
3. **Given** a file larger than 50 MB, **When** upload is attempted, **Then** 400 error is returned with size limit message
4. **Given** a case with 50 documents, **When** upload is attempted, **Then** 409 error is returned with document limit message
5. **Given** an unsupported file type, **When** upload is attempted, **Then** 400 error is returned with supported formats list

---

### User Story 3 - Document Retrieval and Download (Priority: P2)

As a developer, I need to list and retrieve documents for a case, including generating secure download URLs.

**Why this priority**: Users need to view and download documents after upload to verify and review them.

**Independent Test**: Can be fully tested by listing documents and generating download URLs that successfully retrieve files.

**Acceptance Scenarios**:

1. **Given** a case with documents, **When** GET `/cases/{caseId}/documents` is called, **Then** list of document summaries is returned
2. **Given** an existing document, **When** GET `/cases/{caseId}/documents/{documentId}` is called, **Then** full document details including entities and summary are returned
3. **Given** an existing document, **When** GET `/cases/{caseId}/documents/{documentId}/download` is called, **Then** a time-limited SAS URL is generated and returned

---

### User Story 4 - Processing Results Endpoints (Priority: P2)

As a developer, I need endpoints to retrieve extracted entities and summaries so the UI can display processing results.

**Why this priority**: This delivers the core value of the system - AI-extracted insights from documents.

**Independent Test**: Can be fully tested by calling entity and summary endpoints for processed documents.

**Acceptance Scenarios**:

1. **Given** a processed document, **When** GET `/cases/{caseId}/documents/{documentId}/entities` is called, **Then** list of extracted entities is returned with confidence scores
2. **Given** a processed document, **When** GET `/cases/{caseId}/documents/{documentId}/summary` is called, **Then** document summary with key points is returned
3. **Given** an entity, **When** GET `.../entities/{entityId}/explain` is called, **Then** explanation with source context is returned
4. **Given** a summary, **When** GET `.../summary/explain` is called, **Then** explanation with contributing sections is returned

---

### User Story 5 - Case Listing and Filtering (Priority: P2)

As a developer, I need to list cases with pagination and filtering so the UI can display a manageable case dashboard.

**Why this priority**: Essential for UI to show case lists with reasonable performance.

**Independent Test**: Can be fully tested by creating multiple cases and verifying pagination and filters work correctly.

**Acceptance Scenarios**:

1. **Given** multiple cases exist, **When** GET `/cases` is called, **Then** paginated list is returned with default page size 20
2. **Given** cases with different statuses, **When** GET `/cases?status=in-review` is called, **Then** only matching cases are returned
3. **Given** soft-deleted cases exist, **When** GET `/cases?include_deleted=true` is called, **Then** deleted cases are included in results

---

### User Story 6 - Document Reprocessing (Priority: P3)

As a developer, I need to trigger reprocessing of documents when processing fails or needs refresh.

**Why this priority**: Enables recovery from processing failures without re-uploading documents.

**Independent Test**: Can be fully tested by calling reprocess endpoint and verifying new processing message is queued.

**Acceptance Scenarios**:

1. **Given** a processed or failed document, **When** POST `/cases/{caseId}/documents/{documentId}/reprocess` is called, **Then** processing status is reset to "pending" and new message sent to queue

---

### Edge Cases

- What happens when Cosmos DB is unavailable? Return 503 Service Unavailable with retry-after header
- What happens when Blob Storage upload fails mid-stream? Clean up partial uploads, return 500 with error details
- What happens when Service Bus is unavailable? Store message locally and retry with exponential backoff
- What happens when case ID format is invalid? Return 400 with validation error
- What happens when concurrent updates conflict? Use Cosmos DB ETags for optimistic concurrency, return 409 on conflict
- What happens when document processing takes too long? Processing is async; status endpoint shows current state

## Requirements *(mandatory)*

### Functional Requirements

#### API Framework

- **FR-001**: Implementation MUST use FastAPI framework with Python 3.11+
- **FR-002**: All endpoints MUST match the OpenAPI specification in `002-case-api/contracts/openapi.yaml`
- **FR-003**: Request/response models MUST use Pydantic v2 for validation
- **FR-004**: API MUST serve OpenAPI documentation at `/docs` (Swagger UI) and `/redoc`
- **FR-005**: All endpoints MUST require Bearer token authentication (middleware)

#### Data Layer

- **FR-006**: Case data MUST be stored in Azure Cosmos DB with partition key `/case_id`
- **FR-007**: Document metadata MUST be stored in Cosmos DB with partition key `/case_id`
- **FR-008**: Entity and summary data MUST be stored in Cosmos DB with partition key `/document_id`
- **FR-009**: Case ID generation MUST follow format `CASE-YYYYMM-NNNNNN` using atomic counter

#### File Storage

- **FR-010**: Document files MUST be stored in Azure Blob Storage
- **FR-011**: Blob container structure MUST be `cases/{case_id}/documents/{document_id}/{filename}`
- **FR-012**: Download URLs MUST be SAS tokens with 1-hour expiration
- **FR-013**: Upload MUST support streaming for files up to 50 MB

#### Event Processing

- **FR-014**: Document upload MUST publish message to Azure Service Bus queue
- **FR-015**: Message payload MUST include case_id, document_id, and blob_path
- **FR-016**: Failed message delivery MUST retry with exponential backoff

#### Error Handling

- **FR-017**: All errors MUST return consistent ErrorResponse schema
- **FR-018**: Validation errors MUST return 422 with field-level details
- **FR-019**: Not found errors MUST return 404 with resource type and ID
- **FR-020**: Status transition violations MUST return 409 with allowed transitions

#### Observability

- **FR-021**: All requests MUST be logged with correlation ID
- **FR-022**: Azure Application Insights MUST be integrated for telemetry
- **FR-023**: Health check endpoint MUST be available at `/health`

### Key Components

- **Routes**: FastAPI routers for cases, documents, and processing results
- **Services**: Business logic layer for case operations, document handling, storage, and queue
- **Repositories**: Data access layer for Cosmos DB operations
- **Models**: Pydantic schemas matching OpenAPI specification
- **Middleware**: Authentication, error handling, logging, CORS
- **Config**: Environment-based configuration with Azure SDK credential handling

## Assumptions

- Azure Cosmos DB account and database are provisioned with containers for cases, documents, entities, summaries
- Azure Blob Storage account and container are provisioned
- Azure Service Bus namespace and queue are provisioned
- Authentication/authorization is handled by Azure AD B2C or similar (token validation middleware)
- Document processing pipeline (classification, extraction, summarization) is handled by separate service consuming queue messages
- Local development uses Azure emulators or connection strings from environment

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 21 API endpoints pass contract tests against OpenAPI specification
- **SC-002**: API responds to simple requests (case CRUD) in under 200ms p95
- **SC-003**: File uploads up to 50 MB complete successfully within 30 seconds
- **SC-004**: 100% of Pydantic models match OpenAPI schema definitions
- **SC-005**: Unit test coverage exceeds 80% for services and repositories
- **SC-006**: Integration tests verify Cosmos DB, Blob Storage, and Service Bus connectivity
- **SC-007**: API handles 50 concurrent requests without errors
- **SC-008**: All error responses conform to ErrorResponse schema
