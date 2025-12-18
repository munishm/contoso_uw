# Quickstart: Underwriting Case Management API

**Feature**: 002-case-api  
**Date**: 2025-12-17

## Overview

This API enables underwriters to manage insurance cases and documents with automatic AI-powered processing.

## API Endpoints Summary

### Cases

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases` | List all cases (paginated) |
| POST | `/cases` | Create a new case |
| GET | `/cases/{caseId}` | Get case details with summary |
| PUT | `/cases/{caseId}` | Update case |
| DELETE | `/cases/{caseId}` | Soft-delete case |
| POST | `/cases/{caseId}/restore` | Restore deleted case |
| GET | `/cases/{caseId}/status-history` | Get status change history |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases/{caseId}/documents` | List documents for case |
| POST | `/cases/{caseId}/documents` | Upload document (triggers processing) |
| GET | `/cases/{caseId}/documents/{documentId}` | Get document details |
| PATCH | `/cases/{caseId}/documents/{documentId}` | Update document metadata |
| DELETE | `/cases/{caseId}/documents/{documentId}` | Delete document |
| GET | `/cases/{caseId}/documents/{documentId}/download` | Get download URL |
| POST | `/cases/{caseId}/documents/{documentId}/reprocess` | Reprocess document |

### Processing Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cases/{caseId}/documents/{documentId}/entities` | Get extracted entities |
| GET | `/cases/{caseId}/documents/{documentId}/entities/{entityId}/explain` | Explain entity extraction |
| GET | `/cases/{caseId}/documents/{documentId}/summary` | Get document summary |
| GET | `/cases/{caseId}/documents/{documentId}/summary/explain` | Explain summary |

## Quick Examples

### Create a Case

```bash
curl -X POST https://api.underwriting.hsbc.com/v1/cases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "John Smith",
    "policy_type": "Life Insurance - HNW",
    "submission_date": "2025-12-17"
  }'
```

Response:
```json
{
  "case_id": "CASE-202512-000001",
  "client_name": "John Smith",
  "policy_type": "Life Insurance - HNW",
  "status": "draft",
  "created_at": "2025-12-17T10:30:00Z"
}
```

### Upload Document

```bash
curl -X POST https://api.underwriting.hsbc.com/v1/cases/CASE-202512-000001/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@application_form.pdf"
```

### Get Case with Summary

```bash
curl https://api.underwriting.hsbc.com/v1/cases/CASE-202512-000001 \
  -H "Authorization: Bearer <token>"
```

Response includes aggregated "summary of summaries" from all documents.

## Key Constraints

- **Max file size**: 50 MB per document
- **Max documents per case**: 50
- **Supported formats**: PDF, DOCX, DOC, PNG, JPG, JPEG, TIFF
- **Case ID format**: `CASE-YYYYMM-NNNNNN`

## Architecture Flow

```
UI → Upload → API → Azure Blob Storage
                 ↓
         Event → Azure Service Bus Queue
                 ↓
         Processing Pipeline:
           1. Classification
           2. Entity Extraction  
           3. Summarization
                 ↓
         Results → Azure Cosmos DB
```

## OpenAPI Specification

Full specification: [contracts/openapi.yaml](contracts/openapi.yaml)
