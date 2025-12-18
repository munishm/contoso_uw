# Research: Underwriting Case Management API

**Feature**: 002-case-api  
**Date**: 2025-12-17  
**Purpose**: Resolve technical unknowns and document technology decisions

## Technology Decisions

### 1. API Framework

**Decision**: FastAPI with Pydantic v2  
**Rationale**: Already used in the existing `backend/` structure. Provides automatic OpenAPI generation, async support for Azure SDK operations, and native Pydantic integration for request/response validation.  
**Alternatives Considered**:
- Flask: Rejected - lacks native async support and OpenAPI generation
- Django REST: Rejected - heavier framework, overkill for API-only service

### 2. Database

**Decision**: Azure Cosmos DB with azure-cosmos SDK  
**Rationale**: Constitution mandates Azure-native services (Principle 9). Cosmos DB provides global distribution, automatic scaling, and flexible schema for document-oriented data. Native Python SDK with async support.  
**Alternatives Considered**:
- Azure SQL Database: Rejected - relational model less flexible for evolving schemas
- MongoDB API on Cosmos: Rejected - native SQL API preferred for Azure integration

### 3. Document Storage

**Decision**: Azure Blob Storage with azure-storage-blob SDK  
**Rationale**: Constitution mandates Azure-native services (Principle 9). Blob Storage provides scalable, cost-effective document storage with built-in redundancy.  
**Alternatives Considered**:
- Azure Files: Rejected - more expensive, SMB protocol unnecessary
- Local filesystem: Rejected - not scalable, violates Azure-only constraint

### 4. Event Queue

**Decision**: Azure Service Bus with azure-servicebus SDK  
**Rationale**: Constitution mandates Azure-native services. Service Bus provides reliable message delivery, dead-letter handling, and native Python SDK.  
**Alternatives Considered**:
- Azure Storage Queues: Rejected - lacks advanced features (sessions, dead-letter)
- RabbitMQ: Rejected - violates Azure-only constraint

### 5. Case ID Generation

**Decision**: Prefixed numeric with year-month (e.g., `CASE-202512-001234`)  
**Rationale**: User-specified format. Provides human-readable IDs with temporal context. Sequential portion uses database sequence for uniqueness.  
**Implementation**: Database sequence per month, formatted with Python string formatting.

### 6. Document ID Generation

**Decision**: UUID v4 format  
**Rationale**: Documents don't need human-readable IDs. UUIDs provide uniqueness without coordination, suitable for distributed upload scenarios.  
**Implementation**: Python `uuid.uuid4()` at upload time.

### 7. Soft Delete Implementation

**Decision**: `deleted_at` timestamp column + `is_deleted` boolean  
**Rationale**: User requested soft-delete for cases. Timestamp provides audit trail, boolean enables efficient filtering.  
**Implementation**: SQLAlchemy `@hybrid_property` for `is_deleted`, query filter excludes deleted by default.

### 8. File Upload Handling

**Decision**: Streaming upload with chunked transfer to Azure Blob  
**Rationale**: 50 MB max file size requires streaming to avoid memory issues. FastAPI `UploadFile` with async iteration enables memory-efficient upload.  
**Implementation**: `upload_blob()` with `max_concurrency` and `length` parameters.

### 9. Processing Status Tracking

**Decision**: Status enum in database + event-sourced status history  
**Rationale**: Current status for quick queries, history for audit trail (Principle 3). Status transitions validated in service layer.  
**Implementation**: 
- `processing_status` column: pending | classifying | extracting-entities | summarizing | completed | failed
- `processing_history` JSON column: array of `{status, timestamp, details}`

### 10. Summary of Summaries Generation

**Decision**: On-demand aggregation triggered by case retrieval  
**Rationale**: Summaries may update as documents are processed. Real-time aggregation ensures freshness. Cache with TTL for performance.  
**Implementation**: Service method aggregates document summaries, uses Azure OpenAI for synthesis.

## Best Practices Applied

### Azure Blob Storage

- Use managed identity authentication (DefaultAzureCredential)
- Set content-type metadata on upload
- Use container-level SAS for document access URLs
- Implement retry policies for transient failures

### Azure Service Bus

- Use sessions for ordered processing per case
- Configure dead-letter queue for failed messages
- Set message TTL and lock duration appropriately
- Use batch receive for efficiency

### FastAPI

- Use dependency injection for database sessions
- Implement proper exception handlers for HTTP errors
- Use background tasks for non-blocking operations
- Enable CORS for frontend integration

### Azure Cosmos DB

- Use `aio` async client from azure-cosmos
- Partition key strategy: `/case_id` for cases container, `/document_id` for documents
- Use point reads where possible for efficiency
- Leverage change feed for event-driven processing triggers
- Configure appropriate RU throughput for POC (400-1000 RU/s)

## Security Considerations

### Authentication & Authorization

- API endpoints require Bearer token authentication (handled by auth middleware)
- Role-based access control: underwriter role required for case operations
- Case access restricted to assigned underwriters or supervisors

### Data Protection

- Document content encrypted at rest in Azure Blob Storage (SSE)
- Database connections use TLS 1.3
- Sensitive fields (client name, policy details) encrypted at application level
- Audit logs capture all data access events

### Input Validation

- File type validation by magic bytes, not just extension
- File size validation before processing (50 MB limit)
- Case metadata sanitized to prevent injection attacks
- Document metadata validated against schema

## Integration Points

### Existing Components

| Component | Integration | Notes |
|-----------|-------------|-------|
| `src/shared/models/document.py` | Extend | Add case_id, processing_status fields |
| `src/shared/models/entity.py` | Use as-is | Entity model sufficient for extraction results |
| `src/orchestration/pipeline.py` | Trigger | Invoke pipeline on document upload event |
| `src/document_classification/` | Consume | Use existing classifier service |
| `src/entity_extraction/` | Consume | Use existing extractor service |
| `src/document_summarization/` | Consume | Use existing summarizer service |

### New Components

| Component | Purpose |
|-----------|---------|
| `backend/src/api/routes/cases.py` | Case CRUD endpoints |
| `backend/src/api/routes/documents.py` | Document endpoints |
| `backend/src/services/case_service.py` | Case business logic |
| `backend/src/services/storage_service.py` | Azure Blob integration |
| `backend/src/services/queue_service.py` | Azure Service Bus integration |
| `src/shared/models/case.py` | Case Pydantic models |

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| How to handle concurrent uploads? | Azure Blob handles concurrency; database uses optimistic locking |
| How to detect duplicate documents? | MD5 hash comparison on upload; warn user if duplicate exists |
| What triggers summary of summaries update? | On-demand when case is retrieved; cached with 5-minute TTL |
| How to handle partial processing failures? | Per-stage status; allow retry of failed stage only |
| How to support document reprocessing? | API endpoint to trigger reprocess; clears existing results first |
