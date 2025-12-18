# Research: FastAPI Structure and API Implementation

**Feature**: 004-fastapi-src  
**Date**: 2025-12-17  
**Purpose**: Resolve technical decisions for FastAPI structure and API implementation

## Technology Decisions

### 1. FastAPI Application Location

**Decision**: Place FastAPI application at `src/api/` as a new top-level module  
**Rationale**: The existing `src/` structure contains processing modules (document_classification, entity_extraction, etc.). Creating `src/api/` keeps the API layer cleanly separated while allowing imports from `src/shared/` and `src/interfaces/`.  
**Alternatives Considered**:
- Root-level `api/` directory: Rejected - doesn't follow existing pattern of code in `src/`
- Inside `backend/src/`: Rejected - `backend/` exists but is empty scaffolding; using `src/` maintains consistency

### 2. Integration with Existing Shared Models

**Decision**: API models wrap/extend shared models for HTTP serialization  
**Rationale**: The existing `src/shared/models/document.py` and `src/shared/models/entity.py` define domain models. API models in `src/api/models/` will add HTTP-specific fields (pagination, response wrappers) while delegating to shared models for domain logic.  
**Implementation**:
```python
# src/api/models/document.py imports from src/shared/models/document.py
from src.shared.models.document import Document as SharedDocument

class DocumentResponse(BaseModel):
    # Extends SharedDocument with API-specific fields
    download_url: Optional[str] = None
```

### 3. Cosmos DB SDK and Async Pattern

**Decision**: Use `azure-cosmos` with async client (`aio` module)  
**Rationale**: FastAPI is async-native; blocking Cosmos calls would degrade performance. The `azure.cosmos.aio` module provides async `CosmosClient`.  
**Alternatives Considered**:
- Synchronous client with thread pool: Rejected - adds complexity, reduces throughput
- Third-party ODM: Rejected - unnecessary abstraction

### 4. Cosmos DB Container Design

**Decision**: Five containers with partition keys optimized for access patterns
```
- cases: partition key = /case_id
- documents: partition key = /case_id (for case-scoped queries)
- entities: partition key = /document_id
- summaries: partition key = /document_id
- counters: partition key = /counter_id
```
**Rationale**: Cases and documents share partition key for efficient joins. Entities and summaries partition by document_id for processing pipeline queries.

### 5. Case ID Generation

**Decision**: Atomic counter in Cosmos DB + formatted string `CASE-YYYYMM-NNNNNN`  
**Rationale**: Sequential IDs per month require atomic increment. Cosmos stored procedure ensures uniqueness.  
**Implementation**:
```python
# Counter document: {"id": "case-counter-202512", "counter_id": "case-counter-202512", "value": 1234}
# Stored procedure atomically increments and returns new value
case_id = f"CASE-{year_month}-{counter:06d}"
```

### 6. Blob Storage Path Structure

**Decision**: `cases/{case_id}/documents/{document_id}/{original_filename}`  
**Rationale**: Hierarchical structure enables case-level operations. Preserving original filename aids audit.

### 7. SAS Token Generation

**Decision**: User delegation SAS with 1-hour expiration  
**Rationale**: More secure than account keys; short expiration limits exposure.  
**Implementation**:
```python
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

sas_token = generate_blob_sas(
    account_name=account_name,
    container_name=container_name,
    blob_name=blob_path,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.utcnow() + timedelta(hours=1),
    user_delegation_key=user_delegation_key
)
```

### 8. Service Bus Message Format

**Decision**: JSON message with minimal payload
```json
{
  "case_id": "CASE-202512-001234",
  "document_id": "uuid",
  "blob_path": "cases/.../filename.pdf",
  "event_type": "document.uploaded",
  "timestamp": "ISO8601",
  "correlation_id": "request-correlation-id"
}
```
**Rationale**: Processing service fetches full metadata from Cosmos. Minimal message reduces coupling.

### 9. Authentication Middleware

**Decision**: FastAPI dependency with `azure-identity` for token validation  
**Rationale**: Azure AD tokens validated via JWKS endpoint. FastAPI `Depends()` cleanly injects auth context.  
**Implementation**:
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # Validate against Azure AD JWKS
    # Extract user claims
    return user_claims
```

### 10. Error Handling Strategy

**Decision**: Global exception handler + custom exceptions  
**Rationale**: Centralized error formatting ensures consistent `ErrorResponse` schema.  
**Custom Exceptions**:
```python
class NotFoundError(Exception): status_code = 404
class ValidationError(Exception): status_code = 422
class ConflictError(Exception): status_code = 409
class ServiceUnavailableError(Exception): status_code = 503
```

### 11. Reusing Existing Utilities

**Decision**: Import and use `src/shared/utils/` and `src/shared/config/`  
**Rationale**: Avoid duplication. The existing `file_helpers.py` and `validation.py` are compatible.  
**Integration Points**:
- `src/shared/config/env_loader.py` - Environment variable loading
- `src/shared/utils/file_helpers.py` - File type detection, size validation
- `src/shared/utils/validation.py` - Input sanitization

### 12. Uvicorn Entry Point

**Decision**: `uvicorn src.api.main:app` from project root  
**Rationale**: Running from project root ensures Python can resolve `src.api` and `src.shared` imports correctly.  
**Alternative**: Using absolute imports with `PYTHONPATH` set

## Best Practices Applied

### FastAPI

- Use `APIRouter` with tags matching OpenAPI spec
- Use `Depends()` for dependency injection (DB client, auth, services)
- Use `BackgroundTasks` for non-blocking queue operations
- Use `UploadFile` with `SpooledTemporaryFile` for streaming uploads
- Enable CORS middleware with configurable origins
- Use `response_model` for automatic serialization
- Set `summary` and `description` on routes for OpenAPI docs

### Pydantic v2

- Use `model_validator` for cross-field validation (status transitions)
- Use `Field(...)` for required fields with descriptions
- Use `ConfigDict(from_attributes=True)` for ORM-style conversion
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
- Include `correlation_id` in message properties for tracing

## Security Considerations

### Authentication

- Validate Bearer tokens against Azure AD JWKS endpoint
- Cache JWKS keys with TTL (1 hour)
- Extract user claims (oid, email, roles) for audit logging
- Reject expired tokens with 401

### Authorization

- Health endpoint (`/api/v1/health`) is public
- All other endpoints require valid Bearer token
- Role-based access implemented in Phase 2 (not POC scope)

### Input Validation

- Validate file content-type by magic bytes (not just extension)
- Sanitize filenames to prevent path traversal
- Limit JSON payload size (10KB for metadata)
- Validate case ID format with regex `^CASE-\d{6}-\d{6}$`

### Data Protection

- No PII in logs (use correlation IDs only)
- Mask sensitive fields in error responses
- Use Azure Key Vault for all secrets
- Enable soft-delete on Blob Storage

## Integration Points with Existing Code

### From `src/shared/`

| Module | Usage |
|--------|-------|
| `models/document.py` | Reference for document schema, extend for API |
| `models/entity.py` | Reference for entity schema, extend for API |
| `config/env_loader.py` | Load environment variables |
| `utils/file_helpers.py` | File type detection, extension mapping |
| `utils/validation.py` | Input sanitization helpers |

### From `src/interfaces/`

| Module | Usage |
|--------|-------|
| `classifier.py` | Interface for document classification |
| `extractor.py` | Interface for entity extraction |
| `summarizer.py` | Interface for summarization |
| `processor.py` | Orchestration interface |

These interfaces define contracts that the processing pipeline implements. The API layer will queue documents for processing and retrieve results.

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| Where to place FastAPI app? | `src/api/` as new top-level module |
| How to integrate with shared models? | Import and extend for HTTP-specific needs |
| How to handle existing `backend/` folder? | Ignore - use `src/api/` instead for consistency |
| How to run uvicorn? | `uvicorn src.api.main:app` from project root |
| How to share utilities? | Direct import from `src/shared/utils/` |
