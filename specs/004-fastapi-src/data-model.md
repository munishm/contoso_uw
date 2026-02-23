# Data Model: FastAPI Structure and API Implementation (Cosmos DB)

**Feature**: 004-fastapi-src  
**Date**: 2025-12-17  
**Purpose**: Define Cosmos DB container schemas and Pydantic models for API layer

## Cosmos DB Container Design

### Container: `cases`

**Partition Key**: `/case_id`  
**Unique Keys**: None (case_id is partition key)

```json
{
  "id": "CASE-202512-001234",
  "case_id": "CASE-202512-001234",
  "client_name": "John Smith",
  "policy_type": "Life Insurance - HNW",
  "submission_date": "2025-12-17",
  "status": "draft",
  "previous_status": null,
  "created_at": "2025-12-17T10:30:00Z",
  "updated_at": "2025-12-17T10:30:00Z",
  "deleted_at": null,
  "created_by": "user@contoso.com",
  "assigned_to": "underwriter@contoso.com",
  "metadata": {},
  "case_summary": null,
  "case_summary_updated_at": null,
  "status_history": [
    {
      "previous_status": null,
      "new_status": "draft",
      "changed_by": "user@contoso.com",
      "changed_at": "2025-12-17T10:30:00Z",
      "reason": "Case created"
    }
  ],
  "_etag": "\"00000000-0000-0000-0000-000000000000\""
}
```

### Container: `documents`

**Partition Key**: `/case_id`  
**Unique Keys**: `/document_id`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "case_id": "CASE-202512-001234",
  "filename": "application_form.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "blob_path": "cases/CASE-202512-001234/documents/550e8400.../application_form.pdf",
  "checksum_md5": "d41d8cd98f00b204e9800998ecf8427e",
  "processing_status": "completed",
  "processing_error": null,
  "processing_history": [
    {"status": "pending", "timestamp": "2025-12-17T10:31:00Z"},
    {"status": "classifying", "timestamp": "2025-12-17T10:31:05Z"},
    {"status": "extracting-entities", "timestamp": "2025-12-17T10:31:15Z"},
    {"status": "summarizing", "timestamp": "2025-12-17T10:31:30Z"},
    {"status": "completed", "timestamp": "2025-12-17T10:31:45Z"}
  ],
  "classification": "application_form",
  "classification_confidence": 0.95,
  "created_at": "2025-12-17T10:31:00Z",
  "updated_at": "2025-12-17T10:31:45Z",
  "metadata": {},
  "_etag": "\"00000000-0000-0000-0000-000000000000\""
}
```

### Container: `entities`

**Partition Key**: `/document_id`

```json
{
  "id": "entity-uuid-here",
  "entity_id": "entity-uuid-here",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_type": "person_name",
  "value": "John Smith",
  "normalized_value": "JOHN SMITH",
  "confidence": 0.92,
  "page_number": 1,
  "bounding_box": {
    "x": 100.5,
    "y": 200.3,
    "width": 150.0,
    "height": 20.0
  },
  "context": "Applicant Name: John Smith",
  "extraction_method": "azure_form_recognizer",
  "created_at": "2025-12-17T10:31:20Z",
  "metadata": {}
}
```

### Container: `summaries`

**Partition Key**: `/document_id`  
**Unique Keys**: `/document_id` (one summary per document)

```json
{
  "id": "summary-uuid-here",
  "summary_id": "summary-uuid-here",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary_text": "This is a life insurance application for John Smith...",
  "key_points": [
    "Applicant: John Smith, age 45",
    "Coverage requested: $5,000,000",
    "No pre-existing conditions reported"
  ],
  "source_sections": [
    {"page_number": 1, "section": "Personal Information", "relevance": "high"},
    {"page_number": 2, "section": "Coverage Details", "relevance": "high"}
  ],
  "model_version": "gpt-4-turbo-2024-04-09",
  "generation_method": "abstractive",
  "created_at": "2025-12-17T10:31:40Z",
  "metadata": {}
}
```

### Container: `counters`

**Partition Key**: `/counter_id`  
**Purpose**: Atomic case ID generation

```json
{
  "id": "case-counter-202512",
  "counter_id": "case-counter-202512",
  "year_month": "202512",
  "current_value": 1234
}
```

## Pydantic Models (src/api/models/)

### Enumerations (enums.py)

```python
from enum import Enum

class CaseStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    PENDING_DOCUMENTS = "pending-documents"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"
    DELETED = "deleted"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    EXTRACTING_ENTITIES = "extracting-entities"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    APPLICATION_FORM = "application_form"
    FINANCIAL_STATEMENT = "financial_statement"
    MEDICAL_REPORT = "medical_report"
    IDENTITY_DOCUMENT = "identity_document"
    PROPERTY_ASSESSMENT = "property_assessment"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    INSURANCE_POLICY = "insurance_policy"
    LEGAL_DOCUMENT = "legal_document"
    OTHER = "other"
```

### Case Models (case.py)

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional
from .enums import CaseStatus

class CaseCreateRequest(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=255)
    policy_type: str = Field(..., min_length=1, max_length=100)
    submission_date: date
    metadata: dict = Field(default_factory=dict)

class CaseUpdateRequest(BaseModel):
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    policy_type: Optional[str] = Field(None, min_length=1, max_length=100)
    submission_date: Optional[date] = None
    status: Optional[CaseStatus] = None
    assigned_to: Optional[str] = None
    metadata: Optional[dict] = None

class CaseSummaryResponse(BaseModel):
    case_id: str
    client_name: str
    policy_type: str
    status: CaseStatus
    document_count: int
    documents_processed: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CaseDetailResponse(BaseModel):
    case_id: str
    client_name: str
    policy_type: str
    submission_date: date
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str]
    metadata: dict
    documents: list["DocumentSummaryResponse"]
    case_summary: Optional[str]
    case_summary_updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class CaseListResponse(BaseModel):
    items: list[CaseSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class StatusHistoryEntry(BaseModel):
    previous_status: Optional[CaseStatus]
    new_status: CaseStatus
    changed_by: str
    changed_at: datetime
    reason: Optional[str]

class StatusHistoryResponse(BaseModel):
    case_id: str
    history: list[StatusHistoryEntry]
```

### Document Models (document.py)

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID
from .enums import ProcessingStatus, DocumentType

class DocumentSummaryResponse(BaseModel):
    document_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    processing_status: ProcessingStatus
    classification: Optional[DocumentType]
    classification_confidence: Optional[float]
    created_at: datetime

class DocumentDetailResponse(BaseModel):
    document_id: UUID
    case_id: str
    filename: str
    content_type: str
    size_bytes: int
    processing_status: ProcessingStatus
    processing_error: Optional[str]
    classification: Optional[DocumentType]
    classification_confidence: Optional[float]
    created_at: datetime
    updated_at: datetime
    metadata: dict
    entities: list["EntityResponse"]
    summary: Optional["SummaryResponse"]
    download_url: Optional[str]

class DocumentUpdateRequest(BaseModel):
    metadata: Optional[dict] = None

class DocumentListResponse(BaseModel):
    case_id: str
    documents: list[DocumentSummaryResponse]
    total_count: int

class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_at: datetime
```

### Entity Models (entity.py)

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class EntityResponse(BaseModel):
    entity_id: UUID
    entity_type: str
    value: str
    normalized_value: Optional[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    page_number: Optional[int]
    bounding_box: Optional[BoundingBox]

class EntityListResponse(BaseModel):
    document_id: UUID
    entities: list[EntityResponse]
    total_count: int

class EntityExplanationResponse(BaseModel):
    entity_id: UUID
    entity_type: str
    value: str
    confidence: float
    extraction_method: str
    source_text: str
    page_number: int
    bounding_box: BoundingBox
    reasoning: str
```

### Summary Models (summary.py)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class SourceSection(BaseModel):
    page_number: int
    section: str
    relevance: str

class SummaryResponse(BaseModel):
    summary_id: UUID
    summary_text: str
    key_points: list[str]
    source_sections: list[SourceSection]
    created_at: datetime

class SummaryExplanationResponse(BaseModel):
    summary_id: UUID
    summary_text: str
    contributing_sections: list[dict]
    model_version: str
    generation_method: str
```

### Common Models (common.py)

```python
from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None

class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    code: str

class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    message: str
    details: list[ValidationErrorDetail]

class HealthResponse(BaseModel):
    status: str
    version: str
    cosmos_db: str
    blob_storage: str
    service_bus: str
```

## Status Transition Rules

### Case Status Transitions

```python
VALID_CASE_TRANSITIONS = {
    CaseStatus.DRAFT: [CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.IN_REVIEW: [CaseStatus.PENDING_DOCUMENTS, CaseStatus.APPROVED, 
                          CaseStatus.REJECTED, CaseStatus.DRAFT, CaseStatus.DELETED],
    CaseStatus.PENDING_DOCUMENTS: [CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.APPROVED: [CaseStatus.CLOSED, CaseStatus.DELETED],
    CaseStatus.REJECTED: [CaseStatus.CLOSED, CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.CLOSED: [CaseStatus.DELETED],
    CaseStatus.DELETED: [],  # Restore handled separately via /restore endpoint
}

def validate_status_transition(current: CaseStatus, new: CaseStatus) -> bool:
    return new in VALID_CASE_TRANSITIONS.get(current, [])
```

## Indexing Policy

### Cases Container

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {"path": "/status/?"},
    {"path": "/created_at/?"},
    {"path": "/assigned_to/?"},
    {"path": "/deleted_at/?"}
  ],
  "excludedPaths": [
    {"path": "/metadata/*"},
    {"path": "/status_history/*"},
    {"path": "/_etag/?"}
  ],
  "compositeIndexes": [
    [
      {"path": "/status", "order": "ascending"},
      {"path": "/created_at", "order": "descending"}
    ]
  ]
}
```

### Documents Container

```json
{
  "indexingMode": "consistent",
  "includedPaths": [
    {"path": "/processing_status/?"},
    {"path": "/created_at/?"},
    {"path": "/classification/?"}
  ],
  "excludedPaths": [
    {"path": "/metadata/*"},
    {"path": "/processing_history/*"}
  ]
}
```

## Relationship to Existing Shared Models

The API models defined above are designed to work alongside the existing shared models:

| Existing Model | API Model Relationship |
|----------------|----------------------|
| `src/shared/models/document.Document` | API `DocumentDetailResponse` extends with HTTP fields |
| `src/shared/models/entity.Entity` | API `EntityResponse` adapts for API serialization |

The existing shared models focus on domain logic while API models handle HTTP serialization, pagination, and response formatting.
