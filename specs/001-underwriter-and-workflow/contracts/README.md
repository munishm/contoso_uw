# API Contract Summary

**Feature**: 001-underwriter-and-workflow  
**Date**: 2025-12-17  
**Phase**: 1 - Design and Contracts

---

## Overview

This directory contains OpenAPI 3.0 specifications for the backend REST API that the Vue.js frontend will consume. All endpoints follow RESTful conventions and return JSON responses.

---

## API Files

| File | Description | Base Path |
|------|-------------|-----------|
| [cases-api.yaml](cases-api.yaml) | Case management endpoints | `/api/cases` |
| [documents-api.yaml](documents-api.yaml) | Document upload and processing | `/api/documents` |
| [feedback-api.yaml](feedback-api.yaml) | Feedback submission and analytics | `/api/feedback` |

---

## Generating TypeScript Types

Use `openapi-typescript` to generate type definitions from these specifications:

```bash
# Install generator
npm install --save-dev openapi-typescript

# Generate types from local files
npx openapi-typescript ./contracts/cases-api.yaml -o src/types/generated/cases-api.ts
npx openapi-typescript ./contracts/documents-api.yaml -o src/types/generated/documents-api.ts
npx openapi-typescript ./contracts/feedback-api.yaml -o src/types/generated/feedback-api.ts

# Or generate from live backend
npx openapi-typescript http://localhost:8000/api/openapi.json -o src/types/generated/api.ts
```

---

## API Conventions

### Base URLs

- **Local Development**: `http://localhost:8000/api`
- **Development Environment**: `https://api-dev.hsbc-underwriting.internal/api`

### Authentication

POC phase has no authentication. Production will implement:
- Bearer token authentication via `Authorization: Bearer <token>` header
- Role-based access control (underwriter, admin, data_scientist roles)

### Response Formats

All successful responses return JSON with appropriate HTTP status codes:
- `200 OK` - Successful GET/PATCH/POST (existing resource)
- `201 Created` - Successful POST (new resource)
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Responses

All errors follow consistent format:

```json
{
  "error_code": "INVALID_FILE_TYPE",
  "message": "Only PDF files are supported",
  "details": {
    "received_type": "application/msword",
    "allowed_types": ["application/pdf"]
  },
  "timestamp": "2025-12-17T10:30:00Z"
}
```

### Pagination

List endpoints support pagination:

```typescript
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
}
```

Query parameters:
- `page` - Page number (1-indexed)
- `page_size` - Items per page (default 20, max 100)

---

## Endpoint Summary

### Cases API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List all cases with pagination and filtering |
| POST | `/cases` | Create a new case |
| GET | `/cases/{case_id}` | Get case details with all documents |
| PATCH | `/cases/{case_id}` | Update case metadata |
| DELETE | `/cases/{case_id}` | Delete case (soft delete) |

### Documents API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload PDF document for processing |
| GET | `/documents/{document_id}` | Get document with all results |
| GET | `/documents/{document_id}/status` | Get processing status (for polling) |
| POST | `/documents/{document_id}/retry` | Retry failed processing |
| GET | `/documents/{document_id}/download` | Download original PDF |

### Feedback API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/feedback` | Submit field correction or summary rating |
| GET | `/feedback` | List feedback with filters |
| GET | `/feedback/{feedback_id}` | Get specific feedback entry |
| GET | `/feedback/stats` | Get aggregated feedback metrics |

---

## Key Workflows

### 1. Document Upload and Processing

```typescript
// 1. Upload document
const uploadResponse = await fetch('/api/documents/upload', {
  method: 'POST',
  body: formData  // contains file and case_id
})
const document = await uploadResponse.json()

// 2. Poll for status
const pollStatus = async () => {
  const statusResponse = await fetch(`/api/documents/${document.id}/status`)
  const status = await statusResponse.json()
  
  if (status.status === 'completed') {
    // 3. Fetch full results
    const docResponse = await fetch(`/api/documents/${document.id}`)
    const fullDocument = await docResponse.json()
    // Display classification, fields, summaries
  } else if (status.status === 'failed') {
    // Show error, offer retry
  } else {
    // Continue polling
    setTimeout(pollStatus, 5000)
  }
}
```

### 2. Submitting Feedback

```typescript
// Field correction
await fetch('/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: 'doc-123',
    feedback_type: 'field_correction',
    target_entity_id: 'field-456',
    user_rating: 'incorrect',
    corrected_value: 'John Smith'
  })
})

// Summary rating
await fetch('/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: 'doc-123',
    feedback_type: 'summary_rating',
    target_entity_id: 'summary-789',
    user_rating: 4,
    comments: 'Good but missing details'
  })
})
```

---

## Error Codes Reference

| Code | Description | User Action |
|------|-------------|-------------|
| `INVALID_FILE_TYPE` | Non-PDF file uploaded | Upload PDF only |
| `FILE_TOO_LARGE` | File exceeds 20MB | Reduce file size |
| `CASE_NOT_FOUND` | Case ID doesn't exist | Verify case ID |
| `DOCUMENT_NOT_FOUND` | Document ID doesn't exist | Verify document ID |
| `PROCESSING_FAILED` | Azure OpenAI API error | Retry or contact support |
| `INVALID_FEEDBACK_TYPE` | Wrong feedback type | Check request payload |
| `AZURE_API_UNAVAILABLE` | Azure service down | Try again later |

---

## Testing the API

### Using cURL

```bash
# Create case
curl -X POST http://localhost:8000/api/cases \
  -H "Content-Type: application/json" \
  -d '{"case_name": "Test Case"}'

# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@sample.pdf" \
  -F "case_id=case-uuid"

# Get processing status
curl http://localhost:8000/api/documents/{doc-id}/status

# Submit feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-uuid", "feedback_type": "field_correction", ...}'
```

### Using Postman

Import OpenAPI specifications:
1. Open Postman
2. Import > Link > Paste URL to local YAML file
3. Collection will be auto-generated with all endpoints

---

## Next Steps

1. Review OpenAPI specs with backend team for alignment
2. Generate TypeScript types using `openapi-typescript`
3. Implement service layer in `src/services/` using generated types
4. Add request/response mocking for component testing
