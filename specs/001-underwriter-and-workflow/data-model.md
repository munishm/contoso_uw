# Data Model: Underwriter UI and Workflow

**Feature**: 001-underwriter-and-workflow  
**Date**: 2025-12-17  
**Phase**: 1 - Design and Contracts

---

## Overview

This document defines the TypeScript data model for the underwriter UI frontend application. All types are derived from the feature specification's Key Entities section and aligned with backend API contracts.

---

## Entity Relationship Diagram

```
┌─────────────┐
│    Case     │
│ (1)         │
└──────┬──────┘
       │
       │ has many
       ▼
┌─────────────┐
│  Document   │
│ (n)         │
└──────┬──────┘
       │
       ├───────────────┬─────────────┬──────────────┐
       │               │             │              │
       ▼               ▼             ▼              ▼
┌──────────────┐ ┌─────────┐ ┌──────────┐ ┌────────────────┐
│Classification│ │Extracted│ │ Summary  │ │ProcessingStatus│
│   Result     │ │  Field  │ │          │ │                │
│     (1)      │ │  (n)    │ │  (1-2)   │ │      (1)       │
└──────────────┘ └────┬────┘ └────┬─────┘ └────────────────┘
                      │           │
                      ▼           ▼
                 ┌──────────┐ ┌──────────┐
                 │ Feedback │ │Citation  │
                 │   (n)    │ │   (n)    │
                 └──────────┘ └──────────┘
```

**Cardinality**:
- 1 Case → many Documents
- 1 Document → 1 ClassificationResult
- 1 Document → many ExtractedFields
- 1 Document → 1-2 Summaries (extractive and/or abstractive)
- 1 Document → 1 ProcessingStatus
- 1 Summary → many Citations
- 1 ExtractedField or Summary → many Feedback entries

---

## Core Entities

### 1. Case

Represents an underwriting review case that groups related documents.

```typescript
interface Case {
  id: string                    // UUID, primary key
  case_name: string             // User-provided name
  creation_timestamp: string    // ISO 8601 datetime
  status: CaseStatus            // Enum: Pending | InProgress | Completed
  assigned_underwriter_id?: string  // Optional for POC (no auth)
  document_ids: string[]        // Array of associated document IDs
  priority_level?: number       // Optional: 1 (high) to 5 (low)
  last_updated_timestamp: string // ISO 8601 datetime
}

enum CaseStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed'
}
```

**Validation Rules**:
- `case_name`: Required, 1-200 characters
- `status`: Default is `Pending` on creation
- `document_ids`: Can be empty array initially
- Timestamps are server-generated, readonly on frontend

**State Transitions**:
```
Pending → InProgress (when first document uploaded)
InProgress → Completed (when user marks case complete)
Completed → InProgress (if reopened)
```

---

### 2. Document

Represents an uploaded insurance application document.

```typescript
interface Document {
  id: string                      // UUID, primary key
  case_id: string                 // Foreign key to Case
  filename: string                // Original filename
  upload_timestamp: string        // ISO 8601 datetime
  processing_status: ProcessingStatusType  // Enum
  document_type?: DocumentType    // Classification result (null until classified)
  classification_confidence?: number  // 0-100, null until classified
  file_size: number               // Bytes
  uploader_id?: string            // Optional for POC
  blob_url?: string               // Azure Blob Storage URL for download
  
  // Related entities (populated by API)
  classification_result?: ClassificationResult
  extracted_fields?: ExtractedField[]
  summaries?: Summary[]
  processing_status_detail?: ProcessingStatus
}

enum ProcessingStatusType {
  Pending = 'pending',
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed'
}

enum DocumentType {
  FormA = 'form_a',
  FormB = 'form_b',
  Unknown = 'unknown'
}
```

**Validation Rules**:
- `filename`: Must end with `.pdf`
- `file_size`: Maximum 20MB (20,971,520 bytes)
- `processing_status`: Default `Pending` on upload
- `document_type`: Null until classification completes
- `classification_confidence`: 0-100 range when present

**State Transitions**:
```
Pending → Processing (backend starts processing)
Processing → Completed (all steps succeed)
Processing → Failed (any step fails)
Failed → Pending (manual retry by user)
```

---

### 3. ClassificationResult

AI-determined document type with confidence score.

```typescript
interface ClassificationResult {
  id: string                  // UUID
  document_id: string         // Foreign key
  predicted_type: DocumentType  // Form A, Form B, or Unknown
  confidence_score: number    // 0-100
  model_version: string       // e.g., "azure-openai-gpt-4-2024-11"
  processing_timestamp: string  // ISO 8601 datetime
  raw_output?: string         // Optional: Full model response for debugging
}
```

**Confidence Thresholds**:
- High confidence: ≥ 90%
- Medium confidence: 70-89%
- Low confidence: < 70% (shows warning to user)

**UI Display Logic**:
```typescript
function getConfidenceColor(score: number): string {
  if (score >= 90) return 'success'  // Green
  if (score >= 70) return 'warning'  // Yellow
  return 'error'  // Red
}
```

---

### 4. ExtractedField

A single structured data field extracted from the document.

```typescript
interface ExtractedField {
  id: string                   // UUID
  document_id: string          // Foreign key
  field_name: string           // e.g., "Applicant Name", "Policy Amount"
  field_value: string          // Extracted value
  confidence_score: number     // 0-100
  source_location: SourceLocation  // Location in document
  extraction_method: ExtractionMethod  // Rule-based or LLM
  data_type?: FieldDataType    // Optional: string, number, date, boolean
}

interface SourceLocation {
  page_number: number          // 1-indexed
  bounding_box?: BoundingBox   // Optional coordinates for highlighting
}

interface BoundingBox {
  x: number                    // Left coordinate (0-1 normalized or pixels)
  y: number                    // Top coordinate
  width: number
  height: number
}

enum ExtractionMethod {
  RuleBased = 'rule_based',    // Regex, keyword matching
  LLM = 'llm'                  // Azure OpenAI extraction
}

enum FieldDataType {
  String = 'string',
  Number = 'number',
  Date = 'date',
  Boolean = 'boolean'
}
```

**Field Names by Document Type**:

**Form A Fields**:
- `applicant_name` (String)
- `date_of_birth` (Date)
- `policy_amount` (Number)
- `annual_income` (Number)
- `occupation` (String)
- `medical_conditions` (String)

**Form B Fields**:
- `company_name` (String)
- `incorporation_date` (Date)
- `coverage_amount` (Number)
- `revenue` (Number)
- `industry` (String)
- `employee_count` (Number)

**Validation Rules**:
- `field_name`: Must match schema for document type
- `field_value`: Required, max 1000 characters
- `confidence_score`: 0-100 range
- `page_number`: 1-indexed, must be ≤ document page count

---

### 5. Summary

AI-generated document summary with citations.

```typescript
interface Summary {
  id: string                   // UUID
  document_id: string          // Foreign key
  summary_type: SummaryType    // Extractive or Abstractive
  summary_text: string         // Generated summary
  citations: Citation[]        // Array of source citations
  generation_timestamp: string // ISO 8601 datetime
  model_version: string        // e.g., "azure-openai-gpt-4-turbo"
  word_count?: number          // Optional: Summary length
}

enum SummaryType {
  Extractive = 'extractive',   // Key facts extracted verbatim
  Abstractive = 'abstractive'  // Generated text paraphrasing content
}
```

**Summary Length Guidelines**:
- Extractive: Bullet points, 5-10 key facts
- Abstractive: 150-300 words, paragraph format

**Example Extractive Summary**:
```
• Applicant: John Smith, DOB 1985-03-15
• Policy Type: Whole Life Insurance
• Coverage Amount: $2,000,000
• Annual Premium: $8,500
• Medical History: Hypertension (controlled), no surgeries
• Occupation: Software Engineer
```

**Example Abstractive Summary**:
```
John Smith, a 39-year-old software engineer, has applied for a $2M whole life insurance policy. 
The applicant reports controlled hypertension as the only medical condition and maintains an 
annual income of $250,000. The policy includes standard exclusions for high-risk activities...
```

---

### 6. Citation

Links summary statements to specific locations in source document.

```typescript
interface Citation {
  id: string                   // UUID
  summary_id: string           // Foreign key
  cited_text: string           // Text snippet from summary that is cited
  source_page_number: number   // 1-indexed page in document
  source_bounding_box?: BoundingBox  // Optional highlight coordinates
  citation_number?: number     // Optional: [1], [2], etc. in summary text
}
```

**Citation Format in Summary**:
```typescript
// Summary text with inline citations
"The applicant reported an annual income of $250,000 [1] and works as a software engineer [2]."

// Corresponding citations
[
  { citation_number: 1, source_page_number: 2, cited_text: "annual income of $250,000" },
  { citation_number: 2, source_page_number: 3, cited_text: "software engineer" }
]
```

**UI Interaction**:
- User clicks `[1]` → `DocumentViewer` scrolls to page 2 and highlights bounding box
- User clicks `[2]` → `DocumentViewer` scrolls to page 3 and highlights bounding box

---

### 7. Feedback

User feedback on AI outputs for model improvement.

```typescript
interface Feedback {
  id: string                   // UUID
  document_id: string          // Foreign key
  feedback_type: FeedbackType  // Field correction or summary rating
  target_entity_id: string     // ExtractedField.id or Summary.id
  user_rating: UserRating      // Correct/Incorrect or 1-5 scale
  corrected_value?: string     // Optional: Correct value if field was wrong
  comments?: string            // Optional: Freeform text
  user_id?: string             // Optional for POC
  timestamp: string            // ISO 8601 datetime
}

enum FeedbackType {
  FieldCorrection = 'field_correction',
  SummaryRating = 'summary_rating'
}

type UserRating = 
  | 'correct' 
  | 'incorrect' 
  | 1 | 2 | 3 | 4 | 5  // 1-5 scale for summaries
```

**Feedback Submission Flow**:
```typescript
// Field correction
const feedback: Feedback = {
  feedback_type: FeedbackType.FieldCorrection,
  target_entity_id: extractedField.id,
  user_rating: 'incorrect',
  corrected_value: 'John Smith',  // User-provided correct value
  comments: 'OCR misread "Jon" as "John"'
}

// Summary rating
const feedback: Feedback = {
  feedback_type: FeedbackType.SummaryRating,
  target_entity_id: summary.id,
  user_rating: 4,  // 4 out of 5 stars
  comments: 'Good summary but missed medical history details'
}
```

---

### 8. ProcessingStatus

Detailed processing state for documents.

```typescript
interface ProcessingStatus {
  id: string                   // UUID
  document_id: string          // Foreign key
  status: ProcessingStatusType // Enum from Document
  progress_percentage: number  // 0-100
  estimated_completion_time?: string  // ISO 8601 datetime
  error_message?: string       // Present if status is Failed
  step_details: ProcessingStep[]  // Breakdown by processing step
  last_updated: string         // ISO 8601 datetime
}

interface ProcessingStep {
  step_name: ProcessingStepName
  status: StepStatus
  started_at?: string          // ISO 8601 datetime
  completed_at?: string        // ISO 8601 datetime
  error_message?: string
}

enum ProcessingStepName {
  OCR = 'ocr',
  Classification = 'classification',
  Extraction = 'extraction',
  Summarization = 'summarization'
}

enum StepStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed',
  Failed = 'failed'
}
```

**Progress Calculation**:
```typescript
const STEP_WEIGHTS = {
  ocr: 25,
  classification: 15,
  extraction: 30,
  summarization: 30
}

function calculateProgress(steps: ProcessingStep[]): number {
  let totalProgress = 0
  steps.forEach(step => {
    if (step.status === StepStatus.Completed) {
      totalProgress += STEP_WEIGHTS[step.step_name]
    } else if (step.status === StepStatus.InProgress) {
      totalProgress += STEP_WEIGHTS[step.step_name] * 0.5
    }
  })
  return totalProgress
}
```

**UI Display**:
- Linear progress bar with percentage
- Stepper component showing current step
- Error message displayed prominently if failed
- Manual retry button for failed documents

---

## Frontend-Specific Types

### API Response Wrappers

```typescript
// Paginated list response
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
}

// Error response
interface APIError {
  error_code: string           // e.g., "INVALID_FILE_TYPE"
  message: string              // User-friendly message
  details?: Record<string, any>  // Additional error context
  timestamp: string            // ISO 8601 datetime
}
```

### UI State Types

```typescript
// Form state
interface DocumentUploadForm {
  caseId: string
  file: File | null
  isValid: boolean
  errors: Record<string, string>
}

// Filter/sort state for dashboard
interface DocumentFilter {
  status?: ProcessingStatusType[]
  documentType?: DocumentType[]
  dateFrom?: string
  dateTo?: string
  searchQuery?: string
}

interface DocumentSort {
  field: 'upload_timestamp' | 'processing_status' | 'document_type' | 'classification_confidence'
  direction: 'asc' | 'desc'
}

// PDF viewer state
interface PDFViewerState {
  currentPage: number
  totalPages: number
  zoom: number
  highlights: HighlightAnnotation[]
}

interface HighlightAnnotation {
  pageNumber: number
  boundingBox: BoundingBox
  color: string
  label?: string  // e.g., citation number
}
```

---

## Data Validation

### Client-Side Validation Functions

```typescript
// File upload validation
function validateDocumentFile(file: File): string | null {
  if (file.type !== 'application/pdf') {
    return 'Only PDF files are supported'
  }
  if (file.size > 20 * 1024 * 1024) {  // 20MB
    return 'File size must be less than 20MB'
  }
  return null  // Valid
}

// Case name validation
function validateCaseName(name: string): string | null {
  if (name.trim().length === 0) {
    return 'Case name is required'
  }
  if (name.length > 200) {
    return 'Case name must be less than 200 characters'
  }
  return null
}

// Confidence score color coding
function getConfidenceClass(score: number): string {
  if (score >= 90) return 'confidence-high'
  if (score >= 70) return 'confidence-medium'
  return 'confidence-low'
}
```

---

## Type Exports

All types should be exported from a central location for reusability:

```typescript
// src/types/index.ts
export * from './case'
export * from './document'
export * from './classification'
export * from './extraction'
export * from './summary'
export * from './feedback'
export * from './processing'
export * from './api'
export * from './ui'
```

---

## Backend API Contract Alignment

All frontend types are designed to match backend API responses. When backend API specifications are finalized:

1. Generate TypeScript types from OpenAPI spec using `openapi-typescript`
2. Validate frontend types against generated types
3. Update frontend types if mismatches found
4. Add runtime validation using Zod or similar library if needed

**Generation Command**:
```bash
npx openapi-typescript http://localhost:8000/api/openapi.json -o src/types/generated/api.ts
```

---

## Next Steps

With data model defined, proceed to:
1. **Phase 1**: Generate API contract specifications in `contracts/`
2. **Phase 1**: Generate quickstart guide in `quickstart.md`
3. **Phase 2**: Generate implementation tasks in `tasks.md` (via `/speckit.tasks`)
