# Research: FastAPI Implementation of Case Management API

**Feature**: 003-fastapi-impl  
**Date**: 2025-12-17  
**Purpose**: Resolve technical decisions for implementing the OpenAPI specification

## Technology Decisions

### 1. FastAPI Application Structure

**Decision**: Single FastAPI application with modular routers  
**Rationale**: FastAPI's `APIRouter` provides clean separation without over-engineering. All 21 endpoints in one application, organized by resource (cases, documents, processing).  
**Alternatives Considered**:
- Multiple microservices: Rejected - POC scope doesn't warrant distributed complexity
- Single monolithic file: Rejected - 21 endpoints would be unmaintainable

### 2. Cosmos DB SDK

**Decision**: `azure-cosmos` with async client (`aio` module)  
**Rationale**: Native async support matches FastAPI's async paradigm. Official Azure SDK with full feature support.  
**Alternatives Considered**:
- Synchronous client: Rejected - would block event loop
- Third-party ODM (pynamodb-like): Rejected - unnecessary abstraction, direct SDK is cleaner

### 3. Cosmos DB Container Design

**Decision**: Four containers with optimal partition keys
```
- cases: partition key = /case_id
- documents: partition key = /case_id (for case-scoped queries)
- entities: partition key = /document_id
- summaries: partition key = /document_id
```
**Rationale**: Partition keys align with primary access patterns. Cases and documents partitioned by case_id for efficient case retrieval. Entities and summaries by document_id for document-centric queries.

### 4. Case ID Generation

**Decision**: Atomic counter in Cosmos DB + formatted string  
**Rationale**: `CASE-YYYYMM-NNNNNN` format requires sequential numbers per month. Cosmos DB stored procedure with atomic increment ensures uniqueness without distributed coordination.
**Implementation**:
```python
# Counter document: {"id": "counter-202512", "value": 1234}
# Stored procedure atomically increments and returns new value
```

### 5. Document ID Generation

**Decision**: UUID v4 generated at API layer  
**Rationale**: No need for sequential IDs. UUIDs provide uniqueness without database round-trip. Python `uuid.uuid4()` is sufficient.

### 6. Blob Storage Path Structure

**Decision**: `cases/{case_id}/documents/{document_id}/{original_filename}`  
**Rationale**: Hierarchical structure enables case-level operations (list all blobs for case). Preserving original filename aids debugging and audit.

### 7. SAS Token Generation

**Decision**: User delegation SAS with 1-hour expiration  
**Rationale**: User delegation SAS uses Azure AD credentials (more secure than account keys). 1-hour expiration balances usability and security.

### 8. Service Bus Message Format

**Decision**: JSON message with minimal payload
```json
{
  "case_id": "CASE-202512-001234",
  "document_id": "uuid",
  "blob_path": "cases/.../filename.pdf",
  "event_type": "document.uploaded",
  "timestamp": "ISO8601"
}
```
**Rationale**: Processing service fetches full document metadata from Cosmos DB. Minimal message reduces coupling.

### 9. Authentication Middleware

**Decision**: FastAPI dependency with `azure-identity` token validation  
**Rationale**: Bearer token extracted from Authorization header, validated against Azure AD. FastAPI's dependency injection cleanly integrates auth.

### 10. Error Handling Strategy

**Decision**: Global exception handler + custom exceptions  
**Rationale**: Single point for error response formatting. Custom exceptions (NotFoundError, ValidationError, ConflictError) map to HTTP status codes.

## Best Practices Applied

### FastAPI

- Use `APIRouter` with tags matching OpenAPI spec
- Use `Depends()` for dependency injection (DB client, auth, services)
- Use `BackgroundTasks` for non-blocking queue operations
- Use `UploadFile` with `SpooledTemporaryFile` for streaming uploads
- Enable CORS middleware with configurable origins
- Use `response_model` for automatic serialization

### Pydantic v2

- Use `model_validator` for cross-field validation (status transitions)
- Use `Field(...)` for required fields with descriptions
- Use `ConfigDict` for model configuration
- Use discriminated unions for polymorphic responses

### Azure Cosmos DB

- Use `aio.CosmosClient` with `DefaultAzureCredential`
- Set `partition_key` on all operations
- Use `enable_cross_partition_query=False` when possible
- Use `if_match` (ETag) for optimistic concurrency
- Use stored procedures for atomic operations (case ID counter)

### Azure Blob Storage

- Use `aio.BlobServiceClient` with `DefaultAzureCredential`
- Stream uploads with `upload_blob(data, length=content_length)`
- Set `content_type` on blob metadata
- Use `generate_blob_sas()` for download URLs

### Azure Service Bus

- Use `aio.ServiceBusClient` with `DefaultAzureCredential`
- Set `session_id` to case_id for ordered processing per case
- Use `auto_lock_renewer` for long-running consumers
- Implement dead-letter handling for failed messages

## Security Considerations

### Authentication

- Validate Bearer tokens against Azure AD
- Extract user claims for audit logging
- Reject requests without valid tokens (401)
- Support both user and service principal tokens

### Authorization

- Check user roles against endpoint requirements
- Case access limited to assigned underwriter or supervisors
- Document access inherits case access rules
- Admin endpoints require elevated role

### Input Validation

- Validate file content-type by magic bytes (not just extension)
- Sanitize filenames to prevent path traversal
- Limit JSON payload size (10KB for metadata)
- Validate case ID format with regex

### Data Protection

- No PII in logs (use correlation IDs)
- Mask sensitive fields in error responses
- Use Azure Key Vault for all secrets
- Enable soft-delete on Blob Storage

## Integration Points

### Existing Components

| Component | Integration | Notes |
|-----------|-------------|-------|
| `src/shared/models/document.py` | Reference | Existing Pydantic model for documents |
| `src/shared/models/entity.py` | Reference | Existing entity model with confidence |
| `src/orchestration/pipeline.py` | Future | Processing pipeline consumes queue |

### External Services

| Service | Purpose | SDK |
|---------|---------|-----|
| Azure Cosmos DB | Data persistence | azure-cosmos |
| Azure Blob Storage | Document files | azure-storage-blob |
| Azure Service Bus | Processing queue | azure-servicebus |
| Azure Key Vault | Secrets | azure-keyvault-secrets |
| Azure Application Insights | Telemetry | opencensus-ext-azure |

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| How to handle large file uploads? | Streaming with chunked transfer; UploadFile.read() in chunks |
| How to validate file types? | python-magic library for MIME type detection by content |
| How to handle Cosmos DB rate limiting? | Retry with exponential backoff via SDK's built-in retry policy |
| How to version the API? | URL prefix `/v1`; future versions at `/v2` |
| How to handle concurrent case updates? | Cosmos DB ETags for optimistic locking; 409 on conflict |
