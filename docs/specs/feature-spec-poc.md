# Feature Specification: HNW Underwriting Automation POC

**Version:** 1.0  
**Status:** Draft  
**Owner:** TBD  
**Created:** 2025-12-11  
**Last Updated:** 2025-12-11

---

## Table of Contents
1. [Overview](#overview)
2. [Feature 1: Document Ingestion & OCR Pipeline](#feature-1-document-ingestion--ocr-pipeline)
3. [Feature 2: Document Classification](#feature-2-document-classification)
4. [Feature 3: Field Extraction](#feature-3-field-extraction)
5. [Feature 4: Document Summarization](#feature-4-document-summarization)
6. [Feature 5: POC Viewer UI](#feature-5-poc-viewer-ui)
7. [Feature 6: Data Contracts & Infrastructure](#feature-6-data-contracts--infrastructure)
8. [Cross-Feature Requirements](#cross-feature-requirements)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Phases](#implementation-phases)

---

## Overview

This document specifies the features for the HNW Underwriting Automation POC, focusing on document field extraction and summarization for a single bilingual (English/Simplified Chinese) insurance application form using Azure-native services.

### POC Scope
- **Document Type**: HNW CMB APP 2 (single insurance application form, 30 pages)
- **Languages**: English and Simplified Chinese
- **Form Structure**: Variable layout with tables, checkboxes, and text fields
- **Monthly Volume**: ~100 documents

### POC Goals
- Validate AI-powered document processing viability for bilingual forms
- Achieve >90% extraction completeness for 7 key fields
- Demonstrate quality summaries with page-level citations
- Establish reusable architecture patterns
- Process documents concurrently (up to 10 simultaneous)

### Technology Stack
- **OCR**: Azure AI Document Intelligence (Layout API)
- **LLM**: Azure OpenAI Service (GPT-4o, 120 TPM quota)
- **Storage**: Azure Blob Storage, Azure Cosmos DB
- **Backend**: Python FastAPI (async support)
- **Frontend**: Vue.js (lightweight SPA)
- **Infrastructure**: Internal HSBC Azure subscription (provisioned)

---

## Feature 1: Document Ingestion & OCR Pipeline

### Purpose
Accept document uploads, perform OCR, extract layout, and prepare clean text for downstream processing.

### User Stories
- **US-1.1**: As an engineer, I want to upload documents via API so that they can be processed automatically
- **US-1.2**: As a data scientist, I want high-quality OCR output so that extraction accuracy is maximized
- **US-1.3**: As a developer, I want layout information so that I can understand document structure

### Functional Requirements

#### FR-1.1: Ingestion API
**Priority:** P0  
**Description:** REST API endpoint to accept document uploads (no authentication for POC)

**Acceptance Criteria:**
- [ ] API accepts PDF format (primary format for HNW CMB APP 2)
- [ ] API validates file size (<50MB per document, typical 30-page form ~5-10MB)
- [ ] API validates file type (magic number verification for PDF)
- [ ] API returns unique ingestion ID immediately
- [ ] API responds within 2 seconds for upload acknowledgment
- [ ] API supports single document upload (batch deferred to production)
- [ ] No authentication required for POC (simplified access)

**Technical Design:**
```
POST /api/v1/ingest
Content-Type: multipart/form-data

Request Body:
- file: binary (required)
- metadata: JSON (optional)
  - source: string
  - uploaded_by: string
  - tags: array

Response:
{
  "ingestion_id": "uuid",
  "status": "accepted",
  "timestamp": "ISO8601",
  "blob_url": "internal_url"
}
```

**Dependencies:**
- Azure Blob Storage provisioned
- API authentication configured

#### FR-1.2: Document Storage
**Priority:** P0  
**Description:** Store uploaded documents in Azure Blob Storage with metadata

**Acceptance Criteria:**
- [ ] Documents stored in Azure Blob Storage with encryption at rest
- [ ] Blob naming convention: `{ingestion_id}/{filename}`
- [ ] Metadata stored as blob properties (timestamp, source, content_type)
- [ ] Blob URLs are internal (not publicly accessible)
- [ ] Retention policy: Keep for POC duration + 30 days

**Technical Design:**
- Container: `poc-documents-raw`
- Blob metadata: ingestion_id, source, uploaded_by, content_type, upload_timestamp
- Access tier: Hot (for POC)

#### FR-1.3: OCR Processing
**Priority:** P0  
**Description:** Extract text from documents using Azure AI Document Intelligence

**Acceptance Criteria:**
- [ ] OCR processes PDF and image documents
- [ ] OCR achieves >98% character accuracy for typed English text (benchmark on test set)
- [ ] OCR completes within 1 minute per 10-page document
- [ ] OCR handles common issues: rotation, skew, varying DPI
- [ ] OCR output includes confidence scores per text block
- [ ] Failed OCR attempts logged with error details

**Technical Design:**
- Service: Azure AI Document Intelligence (Read API or Layout API)
- Model: Prebuilt Read model (or Layout for table extraction)
- Output format: JSON with text, bounding boxes, confidence scores
- Error handling: Retry up to 3 times with exponential backoff

**Optional Preprocessing (FR-1.4):**
- Deskew, denoise, rotation correction if OCR quality insufficient
- Triggered based on confidence scores (<0.8 average)

#### FR-1.5: Layout Extraction
**Priority:** P1  
**Description:** Extract document layout structure (blocks, lines, tables)

**Acceptance Criteria:**
- [ ] Layout API extracts text blocks, lines, and reading order
- [ ] Tables extracted with row/column structure (if present)
- [ ] Bounding boxes provided for all elements
- [ ] Layout stored as structured JSON
- [ ] Layout information accessible for citation generation

**Technical Design:**
- Use Azure AI Document Intelligence Layout API
- Store layout JSON alongside OCR text
- Schema: page_number, blocks[], lines[], tables[], reading_order[]

#### FR-1.6: Text Normalization
**Priority:** P1  
**Description:** Clean and normalize OCR output for downstream processing

**Acceptance Criteria:**
- [ ] Remove OCR artifacts (spurious characters, duplicates)
- [ ] Normalize whitespace (consistent line breaks, spacing)
- [ ] Preserve original character positions for citation mapping
- [ ] Handle hyphenated words at line breaks
- [ ] Standardize encoding (UTF-8)

**Technical Design:**
- Post-processing pipeline after OCR
- Maintain mapping: normalized_text_offset → original_bbox
- Store both raw and normalized text

### Data Flow
```
Upload → Blob Storage → OCR (Azure AI DI) → Layout Extraction → Text Normalization → Database
```

### Success Metrics
- OCR accuracy: >98% character accuracy on test set
- Processing time: <1 min per 10 pages
- API availability: >95% during POC
- Failed OCR rate: <5%

### Testing Requirements
- Unit tests: API validation, text normalization
- Integration tests: End-to-end upload → OCR → storage
- Performance tests: 10-page document processing time
- Accuracy tests: Ground truth OCR comparison on 50+ pages

---

## Feature 2: Document Classification

### Purpose
**SCOPE CHANGE**: POC focuses on single document type (HNW CMB APP 2). Classification feature deferred to production when multiple form types are introduced.

### User Stories
- ~~**US-2.1**: As a data scientist, I want to classify documents accurately so that correct extraction logic is applied~~ **DEFERRED**
- ~~**US-2.2**: As an underwriter, I want to see classification confidence so that I can trust the system~~ **DEFERRED**
- ~~**US-2.3**: As a product owner, I want a confusion matrix so that I can understand classification errors~~ **DEFERRED**

### Functional Requirements

#### FR-2.1: Document Type Validation (Simplified)
**Priority:** P1  
**Description:** Basic validation that uploaded document is HNW CMB APP 2 form

**Acceptance Criteria:**
- [ ] Optional filename pattern matching (e.g., contains "HNW", "CMB", "APP")
- [ ] All documents assumed to be HNW CMB APP 2 type for extraction
- [ ] No machine learning classification needed for POC
- [ ] Document type hardcoded in metadata: `{"document_type": "HNW_CMB_APP_2", "classification_confidence": 1.0}`

**POC Implementation**: All uploaded documents routed to single extraction pipeline designed for HNW CMB APP 2. Full multi-class classification (Form A/B/Unknown, confusion matrix, precision/recall metrics) deferred to production phase when additional form types onboarded.

### Data Requirements
- **Training Data**: None required for POC (no classification model)
- **Test Data**: Validation on ~5-10 HNW CMB APP 2 samples to confirm extraction pipeline works

### Data Flow
```
Normalized Text → [Classification Skipped] → Extraction Pipeline (HNW_CMB_APP_2) → Database
```

### Success Metrics
- Classification accuracy: N/A (deferred to production)
- Document type validation: 100% (all uploads assumed valid HNW CMB APP 2)

### Testing Requirements
- Unit tests: Metadata assignment, pipeline routing
- Integration tests: End-to-end upload → extraction for HNW CMB APP 2
- Accuracy tests: Deferred (no classification to test)
- Edge case tests: Partial documents, rotated images, poor quality scans

---

## Feature 3: Field Extraction

### Purpose
Extract 5-6 structured fields per document type with >90% completeness and correctness.

### User Stories
- **US-3.1**: As an underwriter, I want key fields extracted automatically so that I don't manually re-type data
- **US-3.2**: As a data scientist, I want validation rules so that extracted data is accurate
- **US-3.3**: As an engineer, I want normalized fields so that downstream systems can consume them

### Functional Requirements

#### FR-3.1: Field Schema Definition
**Priority:** P0  
**Description:** Define extraction schema for each document type

**Acceptance Criteria:**
- [ ] Schema defined for Form A (5-6 fields)
- [ ] Schema defined for Form B (5-6 fields)
- [ ] Each field specifies: name, type, required/optional, validation rules
- [ ] Schema versioned (v1.0) and stored in code repository
- [ ] Schema documented in JSON Schema format

**Field Schema (HNW CMB APP 2 - v1.0):**
```json
{
  "form_type": "HNW_CMB_APP_2",
  "version": "1.0",
  "languages": ["en", "zh-CN"],
  "fields": [
    {
      "name": "family_name",
      "type": "string",
      "required": true,
      "validation": "non-empty, 1-50 chars, supports Chinese characters",
      "description": "Family name (surname) of proposed insured",
      "example": "Zhang / 张"
    },
    {
      "name": "given_name",
      "type": "string",
      "required": true,
      "validation": "non-empty, 1-50 chars, supports Chinese characters",
      "description": "Given name (first name) of proposed insured",
      "example": "Wei / 伟"
    },
    {
      "name": "address",
      "type": "string",
      "required": true,
      "validation": "non-empty, 10-200 chars, supports Chinese characters",
      "description": "Residential address of proposed insured",
      "normalization": "Keep as-is, no standardization for POC"
    },
    {
      "name": "date_of_birth",
      "type": "date",
      "required": true,
      "validation": "ISO8601 format (YYYY-MM-DD), past date only",
      "description": "Date of birth of proposed insured",
      "normalization": "Convert to ISO8601, use format 1-Jan-25 -> 2025-01-01"
    },
    {
      "name": "place_of_birth",
      "type": "string",
      "required": true,
      "validation": "non-empty, 2-100 chars, supports Chinese characters",
      "description": "City/country of birth of proposed insured",
      "example": "Shanghai / 上海"
    },
    {
      "name": "health_details",
      "type": "object",
      "required": false,
      "validation": "structured object with medical history fields",
      "description": "Health and medical information of proposed insured",
      "note": "Complex nested structure, extract key medical conditions as array"
    },
    {
      "name": "financial_information",
      "type": "object",
      "required": true,
      "validation": "structured object with income, assets, liabilities",
      "description": "Financial details of proposed insured for underwriting assessment",
      "fields": [
        "annual_income",
        "net_worth",
        "source_of_funds"
      ],
      "currency_normalization": "Infer from document (USD, HKD, CNY), preserve original"
    }
  ],
  "cross_field_rules": [
    "None specified for POC - deferred to production"
  ]
}
```

#### FR-3.2: Rule-Based Extraction
**Priority:** P0  
**Description:** Extract fields using rule-based methods for structured content

**Acceptance Criteria:**
- [ ] Rules defined for each field (regex, keyword matching, position-based)
- [ ] Rules handle common variations (date formats, currency symbols)
- [ ] Rules extract fields with >90% accuracy on structured forms
- [ ] Extraction includes confidence scores
- [ ] Failed extractions return null with reason

**Technical Design:**
- Use regex patterns for structured fields (dates, amounts, names)
- Use keyword proximity matching (e.g., "Applicant Name:" followed by text)
- Use Azure AI Document Intelligence key-value pair extraction
- Fallback: If rule fails, use LLM extraction

#### FR-3.3: LLM-Based Extraction
**Priority:** P0  
**Description:** Extract fields using Azure OpenAI GPT-4o for bilingual unstructured/complex content

**Acceptance Criteria:**
- [ ] LLM extracts fields with >90% completeness on test documents (no training data required)
- [ ] LLM returns structured JSON matching schema (7 fields)
- [ ] LLM includes confidence scores per field (using GPT-4o logprobs)
- [ ] LLM handles missing fields gracefully (returns null)
- [ ] LLM handles bilingual content (English + Simplified Chinese)
- [ ] LLM completes within 30 seconds per 30-page document
- [ ] Low confidence fields (<0.9) flagged for manual review
- [ ] Zero-shot or few-shot prompting (no model fine-tuning for POC)

**Technical Design:**
```
Prompt Template:
"Extract the following fields from this insurance application form:

{field_schema_description}

Document Text:
{document_text}

Return JSON:
{
  \"fields\": {
    \"applicant_name\": {\"value\": \"...\", \"confidence\": 0.0-1.0},
    \"policy_amount\": {\"value\": 123456, \"confidence\": 0.0-1.0},
    ...
  },
  \"extraction_notes\": \"Any issues or ambiguities\"
}

Only extract fields present in the document. Use null for missing fields."
```

- Model: Azure OpenAI GPT-4 (or GPT-4 Turbo for cost)
- Temperature: 0.1 (low for consistency)
- Max tokens: 1000

#### FR-3.4: Field Post-Processing
**Priority:** P1  
**Description:** Normalize and validate extracted fields

**Acceptance Criteria:**
- [ ] Dates normalized to ISO8601 format
- [ ] Currency amounts normalized (remove symbols, convert to float)
- [ ] Names title-cased, whitespace trimmed
- [ ] Addresses normalized (consistent format)
- [ ] Validation rules enforced (range checks, format checks)
- [ ] Invalid fields flagged with warnings (not blocking)

**Technical Design:**
- Post-processing pipeline after extraction
- Use standard libraries (dateutil, babel for currency)
- Store both raw and normalized values

#### FR-3.5: Cross-Field Validation
**Priority:** P2  
**Description:** Validate consistency across related fields

**Acceptance Criteria:**
- [ ] Date ranges validated (end_date > start_date)
- [ ] Numeric constraints validated (policy_amount within limits)
- [ ] Cross-field business rules enforced
- [ ] Validation errors logged but not blocking (for POC)

### Data Requirements
- **Training Data**: Labeled examples with ground truth field values (50+ per form type)
- **Validation Rules**: Business rules provided by SME

### Data Flow
```
Classified Document → Rule-Based Extraction → LLM Extraction (if needed) → Post-Processing → Validation → Database
```

### Success Metrics
- Extraction completeness: >90% (fields extracted / fields present)
- Extraction correctness: >90% (correct values / extracted fields)
- Processing time: <30 seconds per document (including OCR)
- Confidence calibration: High confidence = high accuracy

### Testing Requirements
- Unit tests: Regex patterns, normalization functions, validation rules
- Integration tests: End-to-end extraction pipeline
- Accuracy tests: Compare extractions against ground truth (50+ documents)
- Edge case tests: Missing fields, handwritten values, ambiguous content

---

## Feature 4: Document Summarization

### Purpose
Generate extractive and abstractive summaries with citations to source text, achieving quality comparable to manual summaries.

### User Stories
- **US-4.1**: As an underwriter, I want concise summaries so that I can quickly understand key information
- **US-4.2**: As a compliance officer, I want citations so that I can verify summary accuracy
- **US-4.3**: As a product owner, I want summary quality metrics so that I can validate AI performance

### Functional Requirements

#### FR-4.1: Extractive Summarization
**Priority:** P0  
**Description:** Generate extractive summary by selecting key sentences/phrases from document

**Acceptance Criteria:**
- [ ] Summary contains 5-10 key facts per document
- [ ] Each fact includes citation (page number, bounding box, or text span)
- [ ] Facts ordered by importance or document order
- [ ] Facts cover critical information (names, amounts, dates, conditions)
- [ ] Summary length: 200-500 words

**Technical Design:**

**Option A: Azure OpenAI Extractive Prompt**
```
Prompt:
"Extract the 5-10 most important facts from this insurance application form. 
For each fact, provide:
- The fact text (direct quote from document)
- The approximate location (page number or section)

Document Text:
{document_text}

Return JSON:
{
  \"facts\": [
    {\"text\": \"...\", \"page\": 1, \"importance\": \"high\"},
    ...
  ]
}"
```

**Option B: Extractive Summarization Library**
- Use extractive summarization algorithms (TextRank, LexRank)
- Rank sentences by importance
- Select top-N sentences as summary

**Recommendation:** Option A for POC (simpler, leverages Azure OpenAI)

#### FR-4.2: Abstractive Summarization
**Priority:** P0  
**Description:** Generate abstractive summary with Azure OpenAI, including citations

**Acceptance Criteria:**
- [ ] Summary is 150-300 words
- [ ] Summary includes all critical information (names, amounts, dates, key conditions)
- [ ] Summary is readable and coherent (not just bullet points)
- [ ] Each claim in summary citable to source document (page/section reference)
- [ ] Summary generation completes within 30 seconds

**Technical Design:**
```
Prompt:
"Summarize this insurance application form in 150-300 words. 
Include:
- Applicant name and policy details
- Coverage amount and dates
- Key medical or financial conditions
- Any notable exclusions or requirements

For each important claim, indicate the source page number in parentheses.

Document Text:
{document_text}

Example format:
The applicant, John Doe (page 1), is applying for life insurance coverage of $1,000,000 (page 1) with a term from 2025-01-01 to 2030-01-01 (page 2). The applicant disclosed a history of diabetes (page 3) which will be underwritten accordingly. No other significant medical conditions were reported (page 3-4)."
```

- Model: Azure OpenAI GPT-4
- Temperature: 0.3 (balanced creativity and consistency)
- Max tokens: 500

#### FR-4.3: Summary of Summaries (Optional)
**Priority:** P2  
**Description:** If multiple documents provided, generate combined summary

**Acceptance Criteria:**
- [ ] Combined summary coherent across documents
- [ ] Citations reference specific documents
- [ ] Combined summary length: 300-500 words
- [ ] Scope decision made by week 1 (TBD)

**Technical Design:**
- Concatenate individual summaries
- Prompt Azure OpenAI to synthesize combined summary
- Maintain citation trail to individual documents

#### FR-4.4: Summary Evaluation
**Priority:** P0  
**Description:** Evaluate summary quality against SME-provided criteria

**Acceptance Criteria:**
- [ ] Evaluation criteria defined by SME (Anish) by week 2
- [ ] Summaries evaluated on test set (50+ documents)
- [ ] Metrics calculated: accuracy, completeness, readability
- [ ] Comparison against manual summaries (benchmark)
- [ ] Results documented in evaluation report

**Evaluation Criteria (to be confirmed with Anish):**
- **Accuracy**: Summary contains correct information (no hallucinations)
- **Completeness**: Summary includes all critical fields
- **Citation Quality**: Citations verifiable and accurate
- **Readability**: Summary coherent and understandable
- **Conciseness**: Summary length appropriate (not too verbose)

**Technical Design:**
- Manual evaluation by SME on 20-50 summaries
- Automated metrics: ROUGE scores (extractive), BERTScore (semantic similarity)
- Inter-rater reliability if multiple evaluators

### Data Requirements
- **Test Documents**: 50+ documents with manual summaries for comparison
- **Evaluation Rubric**: Criteria and scoring from SME

### Data Flow
```
Document Text + Extracted Fields → Extractive Summary → Abstractive Summary → Citation Mapping → Database
```

### Success Metrics
- Summary accuracy: >90% (no factual errors)
- Summary completeness: >85% (critical fields included)
- Citation accuracy: 100% (all citations verifiable)
- ROUGE-L score: >0.6 (vs manual summaries)
- BERTScore: >0.8 (semantic similarity)

### Testing Requirements
- Unit tests: Prompt formatting, response parsing, citation extraction
- Integration tests: End-to-end summarization pipeline
- Accuracy tests: Manual evaluation against ground truth
- Quality tests: ROUGE, BERTScore, readability metrics

---

## Feature 5: POC Viewer UI

### Purpose
Provide web-based interface to view summaries, extracted fields, and source documents for POC validation.

### User Stories
- **US-5.1**: As an underwriter, I want to view summaries so that I can validate AI outputs
- **US-5.2**: As an underwriter, I want to click citations so that I can verify source text
- **US-5.3**: As a product owner, I want to see extracted fields so that I can validate extraction quality
- **US-5.4**: As a user, I want simple feedback buttons so that I can mark outputs as correct/incorrect

### Functional Requirements

#### FR-5.1: Summary Viewer
**Priority:** P0  
**Description:** Display summaries with clickable citations

**Acceptance Criteria:**
- [ ] Abstractive summary displayed prominently
- [ ] Extractive facts displayed as bullet points (optional toggle)
- [ ] Citations are clickable links
- [ ] Clicking citation highlights corresponding text in document viewer
- [ ] Summary viewer responsive (web-based)

**UI Mockup:**
```
┌─────────────────────────────────────────────┐
│ Document: Form A - John Doe Application    │
│ Status: Processed | Classification: Form A │
├─────────────────────────────────────────────┤
│ Summary (Abstractive)                       │
│                                             │
│ The applicant, John Doe [↗page 1], is      │
│ applying for life insurance coverage of    │
│ $1,000,000 [↗page 1] with a term from...   │
│                                             │
│ [Show Extractive Facts]                     │
├─────────────────────────────────────────────┤
│ Extracted Fields                            │
│ • Applicant Name: John Doe (✓ 0.98)        │
│ • Policy Amount: $1,000,000 (✓ 0.95)       │
│ • Coverage Start: 2025-01-01 (✓ 0.99)      │
│ ...                                         │
└─────────────────────────────────────────────┘
```

#### FR-5.2: Field Viewer
**Priority:** P0  
**Description:** Display extracted fields with confidence scores

**Acceptance Criteria:**
- [ ] All extracted fields displayed in structured format
- [ ] Confidence scores shown per field (0-1 scale or %)
- [ ] Visual indicators: ✓ high confidence (>0.9), ⚠ medium (0.7-0.9), ✗ low (<0.7)
- [ ] Null/missing fields clearly indicated
- [ ] Fields grouped by category (optional)

#### FR-5.3: Document Viewer
**Priority:** P0  
**Description:** Display source document with page-level highlighting and side-by-side comparison

**Acceptance Criteria:**
- [ ] PDF rendered in browser (30-page bilingual form support)
- [ ] Page-level highlighting for cited content
- [ ] Navigation by page number (citation clicks scroll to page)
- [ ] Zoom controls (in/out, fit-to-width, fit-to-height)
- [ ] Citation click scrolls to relevant page
- [ ] Side-by-side view: original document on left, extracted data on right
- [ ] No download, print, or annotation features for POC (deferred)
- [ ] No keyboard navigation required (mouse/touch only)

**Technical Design:**
- Use PDF.js library for PDF rendering
- Page-level citation linking (no bounding box coordinates required for POC)
- Synchronized scrolling: citation click → page navigation
- Responsive layout for desktop (1920x1080, 1024x768 secondary)

#### FR-5.4: Feedback Mechanism (Optional - Nice to Have)
**Priority:** P2  
**Description:** Allow users to provide simple document-level feedback

**Acceptance Criteria:**
- [ ] Thumbs up/down buttons at document level (not component-level)
- [ ] Optional comment field for qualitative feedback
- [ ] Feedback stored in database with document ID
- [ ] Feedback logged only (no reprocessing triggers)
- [ ] Feedback reviewed manually by underwriters (no automated actions)
- [ ] Simple feedback mechanism (not full annotation tool)

**Technical Design:**
- Simple REST API: POST /api/v1/feedback
- Database table: feedback (document_id, rating, comment, user, timestamp)
- Decision: Nice to have, not critical for POC validation
- Review by: Underwriters on weekly basis

### Technology Stack
- **Frontend**: Vue.js 3 with Composition API (team preference, lightweight SPA)
- **Backend**: Python FastAPI (async support for Azure SDK calls, auto-generated OpenAPI docs)
- **Document Rendering**: PDF.js for PDF display, page-level navigation
- **Deployment**: Azure App Service or Azure Static Web Apps
- **Styling**: Responsive design for desktop (1920x1080 primary), no mobile optimization for POC

### Data Flow
```
User Request → Backend API → Database Query → JSON Response → Frontend Rendering
```

### Success Metrics
- UI load time: <2 seconds
- Citation navigation: <500ms response
- Usability: 4/5 rating from SME testers

### Testing Requirements
- Unit tests: Component rendering, API calls
- Integration tests: End-to-end user workflows
- Usability tests: SME validation sessions
- Browser compatibility: Chrome, Edge (minimum)

---

## Feature 6: Data Contracts & Infrastructure

### Purpose
Establish reusable data contracts, configuration patterns, and infrastructure for POC and production scalability.

### User Stories
- **US-6.1**: As an engineer, I want versioned schemas so that I can maintain backward compatibility
- **US-6.2**: As a data scientist, I want a model registry so that I can track model versions
- **US-6.3**: As an operations engineer, I want audit logs so that I can debug issues
- **US-6.4**: As an architect, I want documented patterns so that production scaling is straightforward

### Functional Requirements

#### FR-6.1: Configuration Contracts
**Priority:** P1  
**Description:** Define structured configuration schema and prompt library

**Acceptance Criteria:**
- [ ] Configuration schema defined (JSON Schema or similar)
- [ ] Configurations versioned in Git repository
- [ ] Prompts stored in prompt library (separate from code)
- [ ] Configuration validation on load
- [ ] Environment-specific configs (dev, test, prod-ready)

**Configuration Schema Example:**
```json
{
  "version": "1.0",
  "ocr": {
    "service": "Azure AI Document Intelligence",
    "model": "prebuilt-read",
    "confidence_threshold": 0.8
  },
  "classification": {
    "service": "Azure OpenAI",
    "model": "gpt-4",
    "temperature": 0.1,
    "prompt_template": "prompts/classification_v1.txt"
  },
  "extraction": {
    "rule_based_priority": ["applicant_name", "policy_amount"],
    "llm_fallback": true,
    "schema_version": "1.0"
  }
}
```

#### FR-6.2: Data Contracts (JSON Schemas)
**Priority:** P1  
**Description:** Define canonical JSON schemas for all outputs

**Acceptance Criteria:**
- [ ] Schema defined for: ingestion, OCR output, classification, extraction, summarization
- [ ] Schemas versioned (semantic versioning)
- [ ] Schema validation enforced in API endpoints
- [ ] Schema documentation generated automatically
- [ ] Breaking changes require major version bump

**Example: Extraction Output Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExtractionOutput",
  "version": "1.0.0",
  "type": "object",
  "properties": {
    "document_id": {"type": "string", "format": "uuid"},
    "form_type": {"type": "string", "enum": ["Form A", "Form B", "Unknown"]},
    "extraction_timestamp": {"type": "string", "format": "date-time"},
    "fields": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "value": {},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1},
          "source": {"type": "string"}
        },
        "required": ["value", "confidence"]
      }
    }
  },
  "required": ["document_id", "form_type", "fields"]
}
```

#### FR-6.3: Structured Storage
**Priority:** P0  
**Description:** Store outputs in Azure Cosmos DB for simple lookups and querying

**Acceptance Criteria:**
- [ ] Database: Azure Cosmos DB (NoSQL, simple lookups, no relational integrity needed)
- [ ] Collections designed for: documents, extractions, summaries, feedback
- [ ] Partition key: document_id (for efficient queries)
- [ ] Indexes on frequently queried fields (document_id, form_type, timestamp)
- [ ] Data retention: Keep all data for 2 weeks POC duration (manual cleanup post-POC)
- [ ] No automated backups for POC (data loss acceptable, non-production)
- [ ] Schema versioning support: store schema_version field in each document
- [ ] Multiple schema versions coexist (no data migration for POC)

**Cosmos DB Collections (NoSQL example):**
```json
// documents collection
{
  "id": "uuid",
  "document_id": "uuid",
  "blob_url": "https://...",
  "upload_timestamp": "2025-12-11T10:00:00Z",
  "source": "manual_upload",
  "status": "completed",
  "form_type": "HNW_CMB_APP_2",
  "schema_version": "1.0",
  "_ts": 1702291200
}

// extractions collection
{
  "id": "uuid",
  "extraction_id": "uuid",
  "document_id": "uuid",
  "fields": {
    "family_name": {"value": "Zhang", "confidence": 0.98, "source": "page 1"},
    "given_name": {"value": "Wei", "confidence": 0.97, "source": "page 1"},
    // ... 5 more fields
  },
  "extraction_method": "hybrid",
  "model_version": "gpt-4o-2024-11-20",
  "extracted_at": "2025-12-11T10:05:00Z",
  "schema_version": "1.0"
}

// summaries collection
{
  "id": "uuid",
  "summary_id": "uuid",
  "document_id": "uuid",
  "summary_type": "abstractive",
  "summary_text": "The proposed insured, Zhang Wei...",
  "citations": [
    {"sentence": "Zhang Wei", "page": 1},
    {"sentence": "annual income $500K", "page": 15}
  ],
  "model_version": "gpt-4o-2024-11-20",
  "summarized_at": "2025-12-11T10:06:00Z",
  "schema_version": "1.0"
}

// feedback collection
{
  "id": "uuid",
  "feedback_id": "uuid",
  "document_id": "uuid",
  "rating": 5,
  "comment": "Extraction accurate, summary helpful",
  "user_id": "underwriter_001",
  "created_at": "2025-12-11T11:00:00Z"
}
```

**Rationale for Cosmos DB**:
- Simple lookups by document_id (primary access pattern)
- No complex joins needed (denormalized data acceptable)
- JSON-native storage (no ORM mapping complexity)
- Global distribution not needed (single region for POC)
- Expected volume: ~100 documents/month = ~200 documents over POC (low scale)
- Cost-effective for POC scale
- Schema flexibility for rapid iteration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### FR-6.4: Audit Logging
**Priority:** P1  
**Description:** Log all processing steps with timestamps and trace IDs

**Acceptance Criteria:**
- [ ] All API calls logged (request, response, latency)
- [ ] All model invocations logged (model, input hash, output, confidence)
- [ ] Errors logged with stack traces
- [ ] Trace IDs propagated across components
- [ ] Logs structured (JSON format)
- [ ] Logs retained for POC duration + 30 days

**Technical Design:**
- Use Python logging library with structured logging (structlog)
- Centralized logging: Azure Monitor / Application Insights
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Trace ID: UUID generated at ingestion, passed to all components

**Log Entry Example:**
```json
{
  "timestamp": "2025-12-11T10:30:00Z",
  "level": "INFO",
  "trace_id": "abc-123-def",
  "component": "extraction",
  "event": "llm_extraction_completed",
  "document_id": "doc-456",
  "model": "gpt-4",
  "latency_ms": 1234,
  "confidence_avg": 0.92
}
```

#### FR-6.5: Model Registry
**Priority:** P1  
**Description:** Track model versions and configurations in Azure ML Model Registry

**Acceptance Criteria:**
- [ ] All models registered in Azure ML Model Registry
- [ ] Model metadata: version, training date, accuracy metrics, hyperparameters
- [ ] Model artifacts stored (prompts, fine-tuned models, config)
- [ ] Model lineage tracked (training data, evaluation results)
- [ ] Model deployment history maintained

**Technical Design:**
- Use Azure ML Model Registry
- Register models: classification, extraction, summarization
- Metadata: version (semantic), accuracy, latency, cost
- Tags: poc, production-ready, deprecated

### Success Metrics
- Schema validation: 100% of API calls
- Audit log completeness: 100% of processing steps
- Model registry: All models registered and versioned
- Configuration management: Zero hardcoded values in production code

### Testing Requirements
- Unit tests: Schema validation, config parsing
- Integration tests: Database CRUD operations
- Compliance tests: Audit log completeness

---

## Cross-Feature Requirements

### Monitoring & Observability

#### Monitoring Dashboards
**Priority:** P1

**Metrics to Track:**
- **OCR Quality**: Character accuracy, processing time, failure rate
- **Extraction**: Completeness, correctness, confidence distribution, latency
- **Summarization**: Summary length, citation count, latency, manual ratings (1-5 scale)
- **System**: API latency, error rates, throughput (docs/hour)

**Technical Design:**
- Azure Monitor dashboards (basic metrics only)
- Application Insights for APM (optional)
- Dashboards updated periodically (not real-time required)

**Alerting:**
- Simple threshold-based alerts: Email if OCR accuracy drops >50% from baseline
- No recipients configured for POC (manual monitoring acceptable)
- No tiered alerts (warning vs critical)
- No SLA for POC alert response

#### Drift Detection (Deferred)
**Priority:** P3 - Production Only

**POC Decision**: Drift detection not required for POC. Monitoring baseline metrics sufficient.

**Production Requirements** (Deferred):
- Track confidence distribution shifts over time
- Track OCR quality trends
- Track extraction success rates by field
- Alert if metrics deviate >10% from baseline
- Weekly drift reports

### Performance Requirements

| Component | Target | Measurement |
|-----------|--------|-------------|
| API Upload | <2s | Response time |
| OCR Processing (30 pages) | <3 min | Layout API processing time |
| Extraction (7 fields, bilingual) | <30s | GPT-4o end-to-end latency |
| Summarization (30 pages, bilingual) | <40s | GPT-4o end-to-end latency |
| Full Pipeline | <5 min per document | Upload to summary complete (single document) |
| Concurrent Processing | 10 documents | Simultaneous document processing using task queue |
| UI Page Load | <3s | Time to interactive (desktop) |

**Notes:**
- Targets based on typical 30-page HNW CMB APP 2 form
- GPT-4o quota: 120 TPM (sufficient for POC scale)
- No performance testing required for POC (manual validation acceptable)

### Error Handling

**POC Simplification**: Basic error handling only. No sophisticated retry logic, circuit breakers, or fallback strategies needed for POC.

**Error Categories:**
1. **User Errors**: Invalid file format, file too large → Return 400 with clear message
2. **Processing Errors**: OCR failure, model timeout → Log error, return 500 with error ID (no automatic retries)
3. **System Errors**: Database down, Azure service unavailable → Return 503 (no retry-after logic)

**Error Response Format (Technical Messages):**
```json
{
  "error": {
    "code": "OCR_FAILED",
    "message": "OCR processing failed: Azure AI Document Intelligence timeout",
    "trace_id": "abc-123-def",
    "timestamp": "2025-12-11T10:30:00Z",
    "details": "Full technical error for debugging (not sanitized for end users)"
  }
}
```

**Logging**: All errors logged internally with DEBUG level verbosity. No PII redaction for POC.

### Security Requirements

**Authentication:**
- No authentication required for POC (open access for internal testing)
- Azure AD integration deferred to production

**Authorization:**
- No RBAC for POC (all users have full access)
- Production requires: uploader, reviewer, admin roles

**Data Protection:**
- Encryption at rest: Azure Blob Storage encryption enabled by default
- Encryption in transit: HTTPS/TLS 1.3
- Access logs: Optional (not required for POC)
- No rate limiting for POC

**POC Risk Acceptance**: Operating in trusted internal environment only. No external access. No sensitive production data processed during POC.

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \        E2E Tests (10%)
      /____\       - Full workflow validation
     /      \      - Stakeholder demo scenarios
    /________\     Integration Tests (30%)
   /          \    - Component integration
  /____________\   - API contract tests
 /______________\  Unit Tests (60%)
                   - Function-level tests
                   - Schema validation
```

### Test Datasets

**Training Set (if applicable):**
- 20-50 labeled documents per form type
- Used for few-shot examples or model training

**Validation Set:**
- 20-30 labeled documents per form type
- Used during development for tuning

**Test Set (Hold-Out):**
- 50+ labeled documents (never used for training)
- Used for final evaluation and reporting
- Includes edge cases (poor quality, handwritten, partial)

### Test Coverage Requirements

| Component | Unit Test Coverage | Integration Tests | Accuracy Tests |
|-----------|-------------------|-------------------|----------------|
| Ingestion API | >80% | Yes | N/A |
| OCR Pipeline | >70% | Yes | >98% char accuracy |
| Classification | >80% | Yes | >95% precision/recall |
| Extraction | >80% | Yes | >90% completeness/correctness |
| Summarization | >70% | Yes | Manual evaluation + ROUGE |
| UI | >60% | Yes | Usability testing |
| Data Contracts | 100% | Yes | Schema validation |

### Evaluation Reports

**Weekly Progress Report:**
- Completed features
- Current metrics vs targets
- Blockers and risks
- Next week plan

**End-of-POC Evaluation Report:**
- All success metrics vs targets
- Confusion matrices, accuracy tables
- Sample outputs (summaries, extractions)
- Stakeholder demo results
- Recommendations for production
- Estimated costs and timeline for production

---

## Implementation Phases

### Phase 1: Setup & Data Prep (Week 1-2)
**Owner:** Engineering/Product

**Deliverables:**
- [ ] Azure infrastructure provisioned (Blob, AI Document Intelligence, OpenAI, Database)
- [ ] 2 application forms identified (Form A, Form B)
- [ ] 5-6 extraction fields defined per form
- [ ] Schemas defined (field extraction, data contracts)
- [ ] Training/validation/test datasets collected and labeled
- [ ] Development environment configured
- [ ] Git repository set up with CI/CD skeleton

**Gate Criteria:**
- Azure services accessible and tested
- Ground truth data available (min 100 documents)
- Schemas approved by stakeholders

---

### Phase 2: OCR & Classification (Week 3-4)
**Owner:** Data Scientist

**Deliverables:**
- [ ] Ingestion API functional (FR-1.1, FR-1.2)
- [ ] OCR pipeline functional with Azure AI Document Intelligence (FR-1.3, FR-1.5, FR-1.6)
- [ ] OCR accuracy measured on test set (>98% target)
- [ ] Classification model implemented (Azure OpenAI or Azure ML) (FR-2.1, FR-2.2)
- [ ] Classification accuracy >95% on test set
- [ ] Confusion matrix generated and analyzed (FR-2.3)
- [ ] Best classification approach selected and documented (ADR)

**Gate Criteria:**
- OCR accuracy >98%
- Classification precision/recall >95%
- End-to-end pipeline: upload → OCR → classification functional

---

### Phase 3: Extraction & Validation (Week 5-6)
**Owner:** Engineering

**Deliverables:**
- [ ] Field extraction implemented (rule-based + LLM fallback) (FR-3.2, FR-3.3)
- [ ] Field post-processing and normalization (FR-3.4)
- [ ] Cross-field validation (FR-3.5)
- [ ] Extraction accuracy >90% on test set
- [ ] Confidence scores calibrated
- [ ] Database schema implemented and populated (FR-6.3)
- [ ] Audit logging functional (FR-6.4)

**Gate Criteria:**
- Extraction completeness >90%
- Extraction correctness >90%
- End-to-end pipeline: upload → classification → extraction functional

---

### Phase 4: Summarization (Week 7-8)
**Owner:** Data Scientist

**Deliverables:**
- [ ] Extractive summarization implemented (FR-4.1)
- [ ] Abstractive summarization implemented with Azure OpenAI (FR-4.2)
- [ ] Citation mapping functional (page numbers, text spans)
- [ ] Summary evaluation criteria defined by SME (Anish) (FR-4.4)
- [ ] Summaries evaluated on test set
- [ ] ROUGE/BERTScore metrics calculated
- [ ] Summary quality meets benchmarks

**Gate Criteria:**
- Summary accuracy >90% (no factual errors)
- Citation accuracy 100%
- ROUGE-L >0.6, BERTScore >0.8
- SME evaluation: 4/5 average rating

---

### Phase 5: UI & Integration (Week 9-10)
**Owner:** Engineering

**Deliverables:**
- [ ] POC Viewer UI functional (FR-5.1, FR-5.2, FR-5.3)
- [ ] Summary viewer with clickable citations
- [ ] Field viewer with confidence scores
- [ ] Document viewer with highlighting
- [ ] Feedback mechanism (if in scope) (FR-5.4)
- [ ] End-to-end workflow tested
- [ ] Configuration contracts documented (FR-6.1)
- [ ] Data contracts (JSON schemas) documented (FR-6.2)
- [ ] Model registry populated (FR-6.5)

**Gate Criteria:**
- UI functional and tested on 3+ browsers
- End-to-end user workflow validated
- All data contracts versioned and documented

---

### Phase 6: Evaluation & Demo (Week 11-12)
**Owner:** Product Owner

**Deliverables:**
- [ ] SME evaluation completed on 20-50 documents (FR-4.4)
- [ ] All success metrics documented in evaluation report
- [ ] Stakeholder demo conducted
- [ ] Production recommendations documented
- [ ] Cost analysis and timeline for production
- [ ] Funding decision secured (go/no-go)

**Gate Criteria:**
- All P0 goals achieved (>95% classification, >90% extraction, quality summaries)
- Stakeholder demo successful (4/5 satisfaction)
- Production funding approved

---

## Success Criteria Summary

### POC Success = ALL of the following:

✅ **OCR**: >95% character accuracy for bilingual (English + Simplified Chinese) typed text on 30-page forms  
✅ **Extraction**: >90% completeness and correctness for 7 key fields on test documents  
✅ **Summarization**: Quality benchmarked vs manual (ROUGE-L >0.6, BERTScore >0.8 if ground truth available, SME rating >4/5 on precision)  
✅ **Architecture**: Reusable patterns, data contracts, and schemas documented for production scaling  
✅ **Stakeholder Demo**: Successful demo with approval for production funding  

**Note**: Classification accuracy target removed (single form type, no classification needed for POC)

### Production Readiness Criteria (Post-POC):

- Security audit completed (authentication, authorization, access controls)
- Compliance validation completed (data retention, PII handling)
- Performance testing at scale (100+ documents/month sustained, 10 concurrent)
- Multi-form classification implemented (when additional form types onboarded)
- Full HITL workflows designed (manual review, correction, reprocessing)
- Production infrastructure provisioned (redundancy, monitoring, alerting)
- Backup and disaster recovery implemented

---

## Appendix: Open Questions & TBDs

### Resolved Questions (2025-12-11)

| Q ID | Question | Answer | Resolved By |
|------|----------|--------|-------------|
| Q-001 | Which 2 specific application forms will be used? | Single form: HNW CMB APP 2.pdf (30 pages, bilingual English/Simplified Chinese, variable layout with tables/checkboxes) | Product Owner |
| Q-002 | What are the 5-6 fields per document type? | 7 fields: family_name, given_name, address, date_of_birth, place_of_birth, health_details, financial_information | Product Owner / SME |
| Q-003 | What are the summary evaluation criteria? (Anish to provide) | Precision evaluation on 1-5 scale across 5 dimensions: accuracy, completeness, citation quality, readability, conciseness. Success threshold: >90% (avg rating >4/5) | SME (Anish) |
| Q-004 | Is summary of summaries in scope for POC? | No - single document processing only. Multi-document combined summaries deferred to production. | Product Owner |
| Q-005 | What feedback mechanism is needed for POC? | Nice to have: Simple thumbs up/down + comment at document level. Logged only, reviewed manually by underwriters weekly. | Product Owner |
| Q-006 | Azure SQL or Cosmos DB for structured storage? | Cosmos DB (NoSQL) - simple lookups, no relational integrity needed, JSON-native, hundreds of documents scale | Technical Lead |
| Q-007 | Is Azure AI Document Intelligence provisioned and accessible? | Yes - provisioned, endpoint/credentials in environment variables | Engineering |
| Q-008 | Is Azure OpenAI Service provisioned with sufficient quota? | Yes - GPT-4o provisioned with 120 TPM quota | Engineering / Security |

### Additional Clarifications

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Authentication | None required for POC | Internal trusted environment, simplified access |
| Error Handling | Basic only (no retries, circuit breakers) | POC simplification, manual intervention acceptable |
| Monitoring | Simplified (alert if accuracy drops >50%) | No real-time monitoring, manual validation sufficient |
| Drift Detection | Deferred to production | Not critical for POC validation |
| Performance Testing | Manual validation only | No automated load testing for POC |
| Backup/Recovery | No automated backups | Data loss acceptable for non-production POC |
| Rate Limiting | None | No abuse risk in internal environment |
| Frontend Framework | Vue.js 3 | Team preference, lightweight SPA |
| Backend Framework | FastAPI | Async support, auto-generated docs |
| OCR Model | Layout API for all documents | Comprehensive table extraction needed |
| Classification | Deferred | Single form type only, no multi-class classifier needed |
| Training Data | None required | Zero-shot/few-shot LLM prompting only |
| Document Viewer | Desktop only, side-by-side view, page-level citations, no download/print | POC scoped to core functionality |
| Multi-Language | English + Simplified Chinese | Supported in OCR, extraction, summarization |
| Concurrency | 10 simultaneous documents | Task queue for concurrent processing |
| Data Retention | 2 weeks (POC duration) | Manual cleanup post-POC |
| Logging Verbosity | DEBUG level for all | Maximum verbosity for troubleshooting |

---

**Document Version:** 1.1  
**Last Updated:** 2025-12-11  
**Next Review:** Weekly during implementation (incorporate feedback)  
**Next Review:** End of Week 2 (incorporate Q&A answers)

---

*This feature specification aligns with:*
- *[POC PRD](hnw-underwriting-poc.md)*
- *[Project Constitution v1.1.0](../.specify/memory/constitution.md)*
- *[POC Scope Presentation](marp.md)*
