# Feature Specification: Underwriting Case Management API

**Feature Branch**: `002-case-api`  
**Created**: December 17, 2025  
**Status**: Draft  
**Input**: User description: "Underwriting insurance case management API for creating cases, uploading documents, automatic document processing, case status management, and retrieving documents with entity extraction and summaries"

## Overview

This feature provides a RESTful API for underwriters to manage insurance cases and their associated documents. The system enables case creation, document upload with automatic processing (classification, entity extraction, summarization), and comprehensive case/document retrieval with processing results.

## Clarifications

### Session 2025-12-17

- Q: What is the maximum document file size limit? → A: 50 MB maximum per document
- Q: What format should case identifiers use? → A: Prefixed numeric with year-month date (e.g., CASE-202512-001234)
- Q: What is the maximum number of documents per case? → A: 50 documents maximum per case
- Q: What happens when a case is deleted while documents are processing? → A: Soft-delete case (mark inactive); processing continues, case hidden from UI

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Underwriting Case (Priority: P1)

As an underwriter, I need to create a new insurance case with metadata so I can begin collecting and processing documents for underwriting assessment.

**Why this priority**: This is the foundation of the entire system. Without case creation, no other functionality can be used. Cases serve as the container for all documents and processing results.

**Independent Test**: Can be fully tested by creating a case via API, retrieving it, and updating its status. Delivers immediate value by establishing the case management foundation.

**Acceptance Scenarios**:

1. **Given** an authenticated underwriter, **When** they submit case creation request with required metadata (client name, policy type, submission date), **Then** a new case is created with a unique case ID and initial status of "draft"
2. **Given** an existing case, **When** the underwriter retrieves the case by ID, **Then** they receive the complete case metadata including status, creation date, and summary information
3. **Given** an existing case in "draft" or "in-review" status, **When** the underwriter updates the case status, **Then** the case status is updated and the change is recorded with timestamp
4. **Given** an existing case, **When** the underwriter updates case metadata, **Then** the metadata is updated and reflected in subsequent retrievals

---

### User Story 2 - Upload Documents to Case (Priority: P1)

As an underwriter, I need to upload documents to a case so they can be processed and analyzed for underwriting decisions.

**Why this priority**: Document upload is essential for the underwriting workflow. Documents are the primary input for risk assessment and must be associated with cases.

**Independent Test**: Can be fully tested by uploading a document to an existing case, verifying storage confirmation, and checking that processing is initiated. Delivers value by enabling document collection.

**Acceptance Scenarios**:

1. **Given** an existing case, **When** the underwriter uploads a document with file and optional metadata, **Then** the document is stored, assigned a unique document ID, and linked to the case
2. **Given** a successful document upload, **When** the upload completes, **Then** an automatic processing workflow is triggered (classification, entity extraction, summarization)
3. **Given** multiple documents, **When** the underwriter uploads documents to the same case, **Then** each document is processed independently and associated with the case
4. **Given** a document upload, **When** the file format is unsupported, **Then** the system returns an error with the list of supported formats

---

### User Story 3 - Track Document Processing Status (Priority: P2)

As an underwriter, I need to see the processing status of uploaded documents so I know when analysis results are available for review.

**Why this priority**: Underwriters need visibility into processing progress to plan their workflow and know when documents are ready for review.

**Independent Test**: Can be fully tested by uploading a document and polling for status updates until processing completes. Delivers value by providing processing transparency.

**Acceptance Scenarios**:

1. **Given** an uploaded document, **When** the underwriter retrieves document details, **Then** they see the current processing status (pending, processing, completed, failed)
2. **Given** a document in processing, **When** each processing stage completes (classification, entity extraction, summarization), **Then** the status is updated accordingly
3. **Given** a case with multiple documents, **When** the underwriter retrieves case details, **Then** they see an aggregated view of all document processing statuses

---

### User Story 4 - Retrieve Document Analysis Results (Priority: P2)

As an underwriter, I need to retrieve the extracted entities and summary for each document so I can make informed underwriting decisions without reading entire documents.

**Why this priority**: This is the primary value delivery - providing actionable insights from processed documents to accelerate underwriting decisions.

**Independent Test**: Can be fully tested by retrieving a completed document and verifying entity and summary data are present. Delivers core underwriting intelligence value.

**Acceptance Scenarios**:

1. **Given** a fully processed document, **When** the underwriter retrieves document details, **Then** they receive the document classification type, extracted entities, and summary
2. **Given** a processed document, **When** the underwriter requests entity details, **Then** they receive structured entity data with entity types, values, confidence scores, and source locations
3. **Given** a processed document, **When** the underwriter requests the summary, **Then** they receive a concise summary highlighting key information relevant to underwriting
4. **Given** a case with multiple processed documents, **When** the underwriter retrieves case summary, **Then** they receive a "summary of summaries" aggregating key findings across all documents

---

### User Story 5 - Explain Document Analysis (Priority: P3)

As an underwriter, I need to understand why certain entities were extracted or how the summary was generated so I can validate the analysis and make confident decisions.

**Why this priority**: Explainability builds trust in the automated analysis but is not required for basic functionality.

**Independent Test**: Can be fully tested by requesting explanation for a specific entity or summary. Delivers value by enabling validation of automated analysis.

**Acceptance Scenarios**:

1. **Given** a processed document with entities, **When** the underwriter requests explanation for an entity, **Then** they receive context showing where in the document the entity was found and why it was classified as such
2. **Given** a processed document with summary, **When** the underwriter requests explanation, **Then** they receive information about which sections contributed to the summary

---

### Edge Cases

- What happens when a document upload fails mid-transfer? The system should support resumable uploads or provide clear retry guidance.
- How does the system handle duplicate document uploads to the same case? The system should detect duplicates and warn the user.
- What happens when document processing fails? The document status shows "failed" with error details, and the underwriter can retry processing.
- What happens when a case is deleted while documents are still processing? The case is soft-deleted (marked inactive and hidden from UI); document processing continues to completion, and the case can be restored if needed.
- How does the system handle documents exceeding the 50 MB size limit? The system rejects with clear error message stating the maximum file size is 50 MB.
- What happens when the underwriter requests a non-existent case or document? The system returns a 404 error with descriptive message.

## Requirements *(mandatory)*

### Functional Requirements

#### Case Management

- **FR-001**: System MUST allow underwriters to create a new case with required metadata (client name, policy type, submission date)
- **FR-002**: System MUST generate a unique case identifier in prefixed numeric format with year-month date (e.g., CASE-202512-001234) for each created case
- **FR-003**: System MUST support retrieving a case by its unique identifier
- **FR-004**: System MUST support updating case metadata for existing cases
- **FR-005**: System MUST track case status with valid states: draft, in-review, pending-documents, approved, rejected, closed, deleted (soft-delete)
- **FR-006**: System MUST allow underwriters to update case status with state transition validation
- **FR-006a**: System MUST implement soft-delete for cases, marking them inactive and hiding from default queries while preserving data and allowing restoration
- **FR-007**: System MUST record timestamps for case creation, last modification, and status changes

#### Document Management

- **FR-008**: System MUST allow uploading documents to an existing case
- **FR-009**: System MUST generate a unique document identifier for each uploaded document
- **FR-010**: System MUST store uploaded documents in persistent storage (blob storage)
- **FR-011**: System MUST associate each document with exactly one case
- **FR-011a**: System MUST enforce a maximum limit of 50 documents per case
- **FR-012**: System MUST support retrieving a document by case ID and document ID
- **FR-013**: System MUST support listing all documents for a given case
- **FR-014**: System MUST support updating document metadata
- **FR-015**: System MUST support common document formats: PDF, DOCX, DOC, PNG, JPG, JPEG, TIFF

#### Automatic Document Processing

- **FR-016**: System MUST automatically trigger document processing upon successful upload
- **FR-017**: System MUST classify documents into predefined document types (application form, financial statement, medical report, identity document, property assessment, etc.)
- **FR-018**: System MUST extract relevant entities from documents based on document classification
- **FR-019**: System MUST generate a summary for each processed document
- **FR-020**: System MUST track processing status for each document: pending, classifying, extracting-entities, summarizing, completed, failed
- **FR-021**: System MUST use event-driven architecture (queue-based) for processing orchestration

#### Results Retrieval

- **FR-022**: System MUST provide access to document classification results
- **FR-023**: System MUST provide access to extracted entities with entity type, value, confidence score, and source location
- **FR-024**: System MUST provide access to document summary
- **FR-025**: System MUST generate a case-level "summary of summaries" aggregating insights from all processed documents
- **FR-026**: System MUST support explanation requests for entity extraction reasoning

#### Error Handling

- **FR-027**: System MUST return appropriate error responses with descriptive messages for invalid requests
- **FR-028**: System MUST handle processing failures gracefully and allow retry of failed processing

### Key Entities

- **Case**: Represents an underwriting case. Contains client information, policy type, submission date, current status, timestamps, and references to associated documents. A case can have multiple documents.

- **Document**: Represents an uploaded document within a case. Contains file reference, upload timestamp, processing status, document type classification, and references to extracted entities and summary.

- **Entity**: Represents an extracted piece of information from a document. Contains entity type (e.g., name, date, amount, address), extracted value, confidence score, and source location within the document.

- **Summary**: Represents the generated summary of a document. Contains the summary text and metadata about summary generation.

- **ProcessingStatus**: Tracks the current state of document processing through classification, entity extraction, and summarization stages.

## Assumptions

- Underwriters are authenticated before accessing the API (authentication mechanism handled separately)
- The system has access to AI/ML services for document classification, entity extraction, and summarization
- Blob storage infrastructure is available for document storage
- Message queue infrastructure is available for event-driven processing
- Document processing times will vary based on document size and complexity
- The system supports single-tenant operation initially (multi-tenancy considerations deferred)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Underwriters can create a case and upload their first document within 2 minutes
- **SC-002**: Document processing (classification, entity extraction, summarization) completes within 60 seconds for documents under 20 pages
- **SC-003**: System correctly classifies document types with at least 90% accuracy
- **SC-004**: Entity extraction captures at least 85% of key underwriting-relevant information
- **SC-005**: Underwriters can retrieve complete case information including all document results in a single request
- **SC-006**: System handles at least 50 concurrent case operations without degradation
- **SC-007**: Case status updates are reflected immediately (within 1 second) in subsequent retrievals
- **SC-008**: 95% of underwriters can complete a full case review (create case, upload documents, review results) without errors
