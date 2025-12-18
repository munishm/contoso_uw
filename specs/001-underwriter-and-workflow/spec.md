# Feature Specification: Underwriter UI and Workflow for Document Processing

**Feature Branch**: `001-underwriter-and-workflow`  
**Created**: 17 December 2025  
**Status**: Draft  
**Input**: User description: "Underwriter UI and workflow for document processing that displays document classification results, extracted fields with confidence scores, document summaries with citations to source text, and allows underwriters to review and provide feedback on AI-generated outputs"

 
## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Document Processing Results (Priority: P1)

An underwriter uploads an insurance application document and views the AI-generated classification, extracted fields, and summary to understand the application without reading the entire document manually.

**Why this priority**: Core value proposition - enables underwriters to quickly understand document content and validate AI accuracy. This is the primary use case that must work for the POC to succeed.

**Independent Test**: Can be fully tested by uploading a sample document, viewing the results page showing classification type, key fields, and summary, and verifying all elements are visible and accurate compared to manual review.

**Acceptance Scenarios**:

1. **Given** an underwriter is on the document upload page, **When** they upload a valid application form PDF, **Then** the system processes the document and displays a results page with classification, extracted fields, and summary within 5 minutes
2. **Given** a document has been processed, **When** the underwriter views the results page, **Then** they see the document type (Form A/Form B), confidence score, and all extracted fields displayed clearly with their confidence scores
3. **Given** the underwriter is viewing extracted fields, **When** they click on a field value, **Then** they see the corresponding location highlighted in the source document
4. **Given** the underwriter is viewing the summary, **When** they click on a cited statement, **Then** the source document scrolls to and highlights the referenced text
5. **Given** multiple documents are in the queue, **When** the underwriter accesses the dashboard, **Then** they see a list of all processed documents with their status and key metadata

---

### User Story 2 - Provide Feedback on AI Outputs (Priority: P2)

An underwriter marks AI-generated outputs as correct or incorrect to help the data science team improve model accuracy and builds a feedback dataset for future training.

**Why this priority**: Critical for POC evaluation and model improvement, but underwriters can still use the system without this capability. Provides the data needed to measure accuracy and iterate on models.

**Independent Test**: Can be tested by viewing any processed document result, marking fields or summaries as correct/incorrect, and verifying feedback is saved and can be retrieved by data scientists.

**Acceptance Scenarios**:

1. **Given** an underwriter is reviewing extracted fields, **When** they mark a field as "Correct" or "Incorrect", **Then** the feedback is saved with timestamp and user ID
2. **Given** an underwriter marks a field as incorrect, **When** they provide the correct value in a text input, **Then** the correction is saved alongside the original AI output
3. **Given** an underwriter is reviewing the summary, **When** they rate it using thumbs up/down or a 1-5 scale, **Then** the rating is saved with optional comments
4. **Given** feedback has been provided, **When** a data scientist accesses the feedback dashboard, **Then** they see aggregated feedback metrics (accuracy rates, common errors, correction patterns)
5. **Given** an underwriter provides feedback, **When** they submit it, **Then** they receive confirmation and can continue reviewing other documents

---

### User Story 3 - Navigate and Compare Source Documents (Priority: P2)

An underwriter views the original source document alongside AI outputs to verify extraction accuracy and understand context for citations and summaries.

**Why this priority**: Essential for validation tasks but can be implemented after basic results display. Enables underwriters to trust the AI outputs by seeing the source evidence.

**Independent Test**: Can be tested by displaying a processed document result with a split view showing PDF viewer on one side and AI outputs on the other, with synchronized highlighting when clicking citations.

**Acceptance Scenarios**:

1. **Given** an underwriter is on the results page, **When** they click "View Source Document", **Then** the original PDF opens in an embedded viewer
2. **Given** the source document is open, **When** the underwriter clicks on an extracted field, **Then** the corresponding location in the PDF is highlighted
3. **Given** the underwriter is viewing a summary, **When** they click a citation number, **Then** the PDF scrolls to the cited section and highlights it
4. **Given** multiple sections are highlighted, **When** the underwriter navigates between them, **Then** highlighting updates to show the current focus area
5. **Given** the source document has multiple pages, **When** the underwriter uses page navigation, **Then** they can browse all pages with smooth scrolling and zooming

---

### User Story 4 - Manage Document Queue and Status (Priority: P3)

An underwriter views all uploaded documents in a queue, tracks their processing status, and prioritizes which documents to review next.

**Why this priority**: Improves workflow efficiency but not required for basic functionality. Can be added after core review capabilities work.

**Independent Test**: Can be tested by uploading multiple documents, viewing the queue showing status for each (pending, processing, completed, error), and filtering/sorting by various criteria.

**Acceptance Scenarios**:

1. **Given** multiple documents have been uploaded, **When** the underwriter accesses the dashboard, **Then** they see all documents listed with status (Processing, Completed, Failed), upload time, and document type
2. **Given** the underwriter is viewing the queue, **When** they filter by status or document type, **Then** the list updates to show only matching documents
3. **Given** a document is still processing, **When** the underwriter views its status, **Then** they see a progress indicator and estimated completion time
4. **Given** a document failed processing, **When** the underwriter views the error details, **Then** they see a clear error message and suggested actions (retry, check format, contact support)
5. **Given** documents are listed, **When** the underwriter clicks on a document row, **Then** they navigate to the results page for that document

---

### Edge Cases

- What happens when the uploaded file is not a valid document format (e.g., corrupted PDF, wrong file type)?
- How does the system handle documents that fail OCR processing (e.g., handwritten forms, poor image quality)?
- What happens when classification confidence is very low (<50%) - is the document type shown as "Unknown"?
- How are documents with missing required fields handled - does the UI show blank fields or error indicators?
- What happens when a summary citation references text that spans multiple pages?
- How does the system handle very large documents (>50 pages) that might cause performance issues?
- What happens when two underwriters try to provide feedback on the same document simultaneously?
- How are documents with mixed languages (e.g., English + Chinese annotations) handled when POC only supports English?
- What happens when the Azure OpenAI API is unavailable - does the user see a clear error message?
- How does the system handle documents with tables or complex layouts that extraction might misinterpret?

## Requirements *(mandatory)*

### Functional Requirements

**Case Management**

- **FR-001**: System MUST allow underwriters to create a new case by uploading one or more insurance application documents (PDF format, max 20MB per file)
- **FR-002**: System MUST support uploading a single PDF containing multiple documents (consolidated application package)
- **FR-003**: System MUST display cases in a dashboard with filtering options for status: Pending (uploaded but not started), In Progress (currently being reviewed), Completed (review finished)
- **FR-004**: System MUST allow underwriters to sort cases by creation date, status, document type, or priority
- **FR-005**: System MUST associate all uploaded documents with a case ID for tracking and organization

**Document Processing & Display**

- **FR-006**: System MUST allow underwriters to upload insurance application documents within a case (PDF format, max 20MB file size)
- **FR-007**: System MUST display document classification results showing document type (Form A, Form B, or Unknown) with confidence score (0-100%)
- **FR-008**: System MUST display all extracted fields in a structured format with field name, value, and confidence score
- **FR-009**: System MUST display document summaries with both extractive (key facts) and abstractive (generated text) versions
- **FR-010**: System MUST provide clickable citations that link summary statements to source text locations in the original document
- **FR-011**: System SHOULD display the original source document in an embedded PDF viewer with page navigation and zoom controls (nice-to-have for POC)
- **FR-012**: System MUST highlight corresponding text in the source document when a user clicks on an extracted field or citation
- **FR-013**: System MUST allow underwriters to mark extracted fields as "Correct" or "Incorrect" with optional corrected values
- **FR-014**: System MUST allow underwriters to rate summary quality using a simple rating mechanism (thumbs up/down or 1-5 scale)
- **FR-015**: System MUST save all feedback with timestamp, user ID, and associated document ID for later analysis
- **FR-016**: System MUST display a dashboard listing all cases and documents with status, upload time, document type, and quick actions
- **FR-017**: System MUST show processing status for each document (Pending, Processing, Completed, Failed) with visual indicators
- **FR-018**: System MUST allow filtering and sorting of the document queue by status, date, document type, and confidence score
- **FR-019**: System MUST display clear error messages when document processing fails, with actionable guidance (retry, check format)
- **FR-020**: System MUST show progress indicators for documents currently being processed with estimated completion time
- **FR-021**: System MUST validate uploaded files for format (PDF only for POC) and size (<20MB) before processing
- **FR-022**: System MUST provide a split-view layout option showing source document and AI outputs side-by-side
- **FR-023**: System MUST maintain user session state so underwriters can navigate between cases and documents without losing context

### Key Entities

- **Case**: Represents an underwriting review case with attributes: case ID, case name, creation timestamp, status (Pending/In Progress/Completed), assigned underwriter ID, associated document IDs (array), priority level, last updated timestamp
- **Document**: Represents an uploaded insurance application with attributes: document ID, case ID (foreign key), filename, upload timestamp, processing status (pending/processing/completed/failed), document type (Form A/Form B/Unknown), classification confidence score, file size, uploader ID
- **Classification Result**: The AI-determined document type with attributes: document ID, predicted type, confidence score, model version used, processing timestamp
- **Extracted Field**: A single piece of structured data extracted from the document with attributes: field ID, field name (e.g., "Applicant Name", "Policy Amount"), field value, confidence score (0-100%), source location (page number, bounding box coordinates), extraction method (rule-based/LLM)
- **Summary**: AI-generated document summary with attributes: summary ID, document ID, summary type (extractive/abstractive), summary text, citations (array of {text, source location} pairs), generation timestamp, model version
- **Citation**: Link from summary text to source document with attributes: citation ID, summary ID, cited text, source page number, source bounding box coordinates
- **Feedback**: User feedback on AI outputs with attributes: feedback ID, document ID, feedback type (field correction/summary rating), target entity ID (field ID or summary ID), user rating (correct/incorrect or 1-5 scale), corrected value (optional), comments (optional), user ID, timestamp
- **Processing Status**: Current state of document processing with attributes: document ID, status (pending/processing/completed/failed), progress percentage, estimated completion time, error message (if failed), step details (OCR/Classification/Extraction/Summarization)

### Security & Access Control

- **SEC-001**: System operates with no authentication for POC phase - open access for demo purposes only
- **SEC-002**: Authentication and authorization MUST be implemented before production deployment
- **SEC-003**: All uploaded documents and feedback data are accessible to any user during POC period
- **SEC-004**: Production system will require role-based access control (underwriter, admin, data scientist roles) and audit logging

### Data Storage & Backend Integration

- **STOR-001**: Backend API handles all data persistence using Azure Blob Storage for document files and Azure SQL/Cosmos DB for metadata
- **STOR-002**: UI communicates with backend via REST API endpoints for upload, retrieval, and feedback operations
- **STOR-003**: Documents uploaded through UI are transmitted to backend API which handles storage in Azure Blob Storage
- **STOR-004**: All case, document, classification, extraction, summary, and feedback data persisted in Azure SQL/Cosmos DB by backend
- **STOR-005**: UI does not implement direct storage logic - all persistence operations delegated to backend API

### Non-Functional Requirements

- **NFR-001**: Performance and scalability targets are not mandatory for POC - system operates on best-effort basis
- **NFR-002**: System should handle typical POC demonstration scenarios with reasonable responsiveness
- **NFR-003**: Production deployment will require formal performance benchmarking and capacity planning

### Error Handling & Resilience

- **ERR-001**: When Azure OpenAI API calls fail, system MUST fail immediately without automatic retry
- **ERR-002**: System MUST display clear error message to user indicating API failure with actionable guidance
- **ERR-003**: User MUST have option to manually retry failed document processing operations
- **ERR-004**: Failed processing attempts MUST update document status to "Failed" with error details stored for troubleshooting
- **ERR-005**: Error messages MUST distinguish between different failure types (API timeout, rate limit, invalid response, service unavailable)

### Technical Architecture & Constraints

- **TECH-001**: Frontend MUST be built using Vue.js with TypeScript for type safety and maintainability
- **TECH-002**: UI components MUST use Vuetify framework for consistent design and accelerated development
- **TECH-003**: Frontend MUST communicate with backend via RESTful API endpoints
- **TECH-004**: Backend API handles all business logic, data persistence, and external service integration
- **TECH-005**: Frontend is responsible for user interaction, display logic, and client-side validation only

## Clarifications

### Session 2025-12-17

- Q: What authentication and authorization model should the underwriter UI implement? → A: No authentication - open access for POC demo only
- Q: What data storage and persistence strategy should be used for documents and metadata? → A: Azure Blob Storage for documents + Azure SQL/Cosmos DB for metadata, handled by backend API
- Q: What are the performance and scalability targets for the POC? → A: No specific performance targets - best effort for POC
- Q: When Azure OpenAI API calls fail during document processing, how should the system handle the error? → A: Fail immediately on first error, display message to user
- Q: What frontend technology stack should be used to build the underwriter UI? → A: Vue.js with TypeScript + Vuetify

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Underwriters can upload a document and view complete results (classification, fields, summary) within 5 minutes per document
- **SC-002**: 90% of underwriters successfully locate and understand the document type and key fields within 30 seconds of viewing the results page
- **SC-003**: Citation links navigate to the correct source location with <2 seconds delay and 95%+ accuracy in highlighting the right text
- **SC-004**: 100% of feedback submissions are successfully saved and retrievable by data scientists for model evaluation
- **SC-005**: The UI displays all mandatory fields (as defined in schema) for each document type, with clear indicators when fields are missing or have low confidence (<70%)
- **SC-007**: Zero data loss for uploaded documents or feedback during POC period
- **SC-008**: Error messages provide actionable guidance for 100% of common failure scenarios (invalid format, OCR failure, API timeout)
- **SC-009**: Dashboard loads with all documents visible within 3 seconds even with 100+ documents in the queue
- **SC-010**: Split-view layout allows underwriters to verify field accuracy 50% faster compared to viewing results and source separately
