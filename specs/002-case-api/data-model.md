# Data Model: Underwriting Case Management API

**Feature**: 002-case-api  
**Date**: 2025-12-17  
**Purpose**: Define entity schemas and relationships

## Entity Relationship Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CASE                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  case_id           VARCHAR(20)     CASE-YYYYMM-NNNNNN                    │
│     client_name       VARCHAR(255)    Required                               │
│     policy_type       VARCHAR(100)    Required                               │
│     submission_date   DATE            Required                               │
│     status            ENUM            draft|in-review|pending-documents|...  │
│     created_at        TIMESTAMP       Auto                                   │
│     updated_at        TIMESTAMP       Auto                                   │
│     deleted_at        TIMESTAMP       Nullable (soft-delete)                 │
│     created_by        VARCHAR(100)    User ID                                │
│     assigned_to       VARCHAR(100)    Underwriter ID                         │
│     metadata          JSONB           Extensible attributes                  │
│     summary           TEXT            Summary of summaries (cached)          │
│     summary_updated   TIMESTAMP       Cache timestamp                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOCUMENT                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  document_id       UUID            Auto-generated                         │
│ FK  case_id           VARCHAR(20)     Required                               │
│     filename          VARCHAR(255)    Original filename                      │
│     content_type      VARCHAR(100)    MIME type                              │
│     size_bytes        BIGINT          File size                              │
│     blob_path         VARCHAR(500)    Azure Blob Storage path                │
│     blob_url          VARCHAR(1000)   SAS URL (generated on request)         │
│     checksum_md5      VARCHAR(32)     For duplicate detection                │
│     upload_status     ENUM            uploading|uploaded|failed              │
│     processing_status ENUM            pending|classifying|extracting|...     │
│     processing_error  TEXT            Error message if failed                │
│     processing_history JSONB          Status change history                  │
│     classification    VARCHAR(100)    Document type                          │
│     classification_confidence DECIMAL Confidence score                       │
│     created_at        TIMESTAMP       Upload timestamp                       │
│     updated_at        TIMESTAMP       Auto                                   │
│     metadata          JSONB           Extensible attributes                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ENTITY                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  entity_id         UUID            Auto-generated                         │
│ FK  document_id       UUID            Required                               │
│     entity_type       VARCHAR(100)    e.g., person_name, date, amount        │
│     value             TEXT            Extracted value                        │
│     normalized_value  TEXT            Standardized format                    │
│     confidence        DECIMAL(5,4)    0.0000 to 1.0000                       │
│     page_number       INT             Source page                            │
│     bounding_box      JSONB           Location in document                   │
│     context           TEXT            Surrounding text for explanation       │
│     created_at        TIMESTAMP       Extraction timestamp                   │
│     metadata          JSONB           Extensible attributes                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            SUMMARY                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  summary_id        UUID            Auto-generated                         │
│ FK  document_id       UUID            Required (unique)                      │
│     summary_text      TEXT            Generated summary                      │
│     key_points        JSONB           Array of key findings                  │
│     source_sections   JSONB           Page/section references                │
│     model_version     VARCHAR(50)     AI model used                          │
│     created_at        TIMESTAMP       Generation timestamp                   │
│     metadata          JSONB           Extensible attributes                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CASE_STATUS_HISTORY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK  history_id        UUID            Auto-generated                         │
│ FK  case_id           VARCHAR(20)     Required                               │
│     previous_status   ENUM            Previous status                        │
│     new_status        ENUM            New status                             │
│     changed_by        VARCHAR(100)    User ID                                │
│     changed_at        TIMESTAMP       Change timestamp                       │
│     reason            TEXT            Optional reason for change             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Enumerations

### CaseStatus

```python
class CaseStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    PENDING_DOCUMENTS = "pending-documents"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"
    DELETED = "deleted"  # Soft-delete state
```

### ProcessingStatus

```python
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    EXTRACTING_ENTITIES = "extracting-entities"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### UploadStatus

```python
class UploadStatus(str, Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"
```

### DocumentType (Classification)

```python
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

## State Transitions

### Case Status Transitions

```text
                    ┌──────────────────────────────┐
                    │                              │
                    ▼                              │
┌─────────┐    ┌─────────┐    ┌──────────────┐    │
│  draft  │───▶│in-review│───▶│pending-docs  │────┘
└─────────┘    └─────────┘    └──────────────┘
     │              │               │
     │              │               │
     ▼              ▼               ▼
┌─────────┐    ┌─────────┐    ┌──────────┐
│ deleted │◀───│approved │    │ rejected │
└─────────┘    └─────────┘    └──────────┘
                    │               │
                    ▼               ▼
               ┌─────────┐    ┌─────────┐
               │ closed  │    │ closed  │
               └─────────┘    └─────────┘

Valid Transitions:
- draft → in-review, deleted
- in-review → pending-documents, approved, rejected, draft
- pending-documents → in-review
- approved → closed
- rejected → closed, in-review (appeal)
- Any state → deleted (soft-delete)
- deleted → (restore to previous state)
```

### Document Processing Status Transitions

```text
┌─────────┐    ┌────────────┐    ┌────────────────────┐    ┌─────────────┐    ┌───────────┐
│ pending │───▶│classifying │───▶│extracting-entities │───▶│ summarizing │───▶│ completed │
└─────────┘    └────────────┘    └────────────────────┘    └─────────────┘    └───────────┘
                    │                     │                       │
                    ▼                     ▼                       ▼
               ┌────────┐            ┌────────┐              ┌────────┐
               │ failed │            │ failed │              │ failed │
               └────────┘            └────────┘              └────────┘

- Any failed state can be retried → returns to that stage
- Reprocess resets to pending
```

## Pydantic Schemas

### Case Schemas

```python
# Request: Create Case
class CaseCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=255)
    policy_type: str = Field(..., min_length=1, max_length=100)
    submission_date: date
    metadata: dict[str, Any] = Field(default_factory=dict)

# Request: Update Case
class CaseUpdate(BaseModel):
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    policy_type: Optional[str] = Field(None, min_length=1, max_length=100)
    submission_date: Optional[date] = None
    status: Optional[CaseStatus] = None
    assigned_to: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

# Response: Case Summary (list view)
class CaseSummary(BaseModel):
    case_id: str
    client_name: str
    policy_type: str
    status: CaseStatus
    document_count: int
    documents_processed: int
    created_at: datetime
    updated_at: datetime

# Response: Case Detail
class CaseDetail(BaseModel):
    case_id: str
    client_name: str
    policy_type: str
    submission_date: date
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str]
    metadata: dict[str, Any]
    documents: list[DocumentSummary]
    summary: Optional[str]  # Summary of summaries
    summary_updated_at: Optional[datetime]
```

### Document Schemas

```python
# Response: Document Summary (list view)
class DocumentSummary(BaseModel):
    document_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    processing_status: ProcessingStatus
    classification: Optional[str]
    created_at: datetime

# Response: Document Detail
class DocumentDetail(BaseModel):
    document_id: UUID
    case_id: str
    filename: str
    content_type: str
    size_bytes: int
    processing_status: ProcessingStatus
    processing_error: Optional[str]
    classification: Optional[str]
    classification_confidence: Optional[float]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
    entities: list[EntityResponse]
    summary: Optional[SummaryResponse]
    download_url: Optional[str]  # Time-limited SAS URL

# Request: Document Metadata Update
class DocumentUpdate(BaseModel):
    metadata: Optional[dict[str, Any]] = None
```

### Entity Schemas

```python
class EntityResponse(BaseModel):
    entity_id: UUID
    entity_type: str
    value: str
    normalized_value: Optional[str]
    confidence: float
    page_number: Optional[int]
    bounding_box: Optional[dict[str, float]]
    context: Optional[str]  # For explanation

class EntityExplanation(BaseModel):
    entity_id: UUID
    entity_type: str
    value: str
    confidence: float
    extraction_method: str
    source_text: str
    page_number: int
    bounding_box: dict[str, float]
    reasoning: str  # Why this was classified as this type
```

### Summary Schemas

```python
class SummaryResponse(BaseModel):
    summary_id: UUID
    summary_text: str
    key_points: list[str]
    source_sections: list[dict[str, Any]]  # Page/section references
    created_at: datetime

class SummaryExplanation(BaseModel):
    summary_id: UUID
    summary_text: str
    contributing_sections: list[dict[str, Any]]
    model_version: str
    generation_method: str
```

## Validation Rules

### Case Validation

| Field | Rule |
|-------|------|
| client_name | Required, 1-255 characters, no special characters except `-`, `'`, `.` |
| policy_type | Required, must be from allowed list or "other" |
| submission_date | Required, cannot be future date, max 1 year in past |
| status | Valid transition from current status |
| metadata | Max 10KB JSON |

### Document Validation

| Field | Rule |
|-------|------|
| file | Required, max 50 MB |
| content_type | Must be: application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document, image/png, image/jpeg, image/tiff |
| filename | Max 255 characters, sanitized |
| case_id | Must exist, not deleted, document count < 50 |

### Entity Validation

| Field | Rule |
|-------|------|
| entity_type | Must be from known types |
| confidence | 0.0 to 1.0 |
| page_number | >= 1 |

## Indexes

```sql
-- Case indexes
CREATE INDEX idx_cases_status ON cases(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);
CREATE INDEX idx_cases_assigned_to ON cases(assigned_to) WHERE deleted_at IS NULL;
CREATE INDEX idx_cases_client_name ON cases(client_name) WHERE deleted_at IS NULL;

-- Document indexes
CREATE INDEX idx_documents_case_id ON documents(case_id);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX idx_documents_checksum ON documents(checksum_md5);

-- Entity indexes
CREATE INDEX idx_entities_document_id ON entities(document_id);
CREATE INDEX idx_entities_type ON entities(entity_type);

-- Summary indexes
CREATE UNIQUE INDEX idx_summaries_document_id ON summaries(document_id);
```
