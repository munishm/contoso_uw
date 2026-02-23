---
description: "Implementation tasks for HNW Underwriting Automation POC - Updated 2025-12-11"
---

# Tasks: HNW Underwriting Automation POC

**Feature**: Field Extraction and Summarization for Single Bilingual Insurance Application Form  
**Source Documents**: 
- Feature Spec: `/docs/specs/feature-spec-poc.md` (v1.1)
- PRD: `/docs/prds/hnw-underwriting-poc.md`
- Constitution: `/.specify/memory/constitution.md`

**Timeline**: 12 weeks (POC Phase)  
**Technology Stack**: Azure AI Document Intelligence (Layout API), Azure OpenAI (GPT-4o), Azure Blob Storage, Azure Cosmos DB, Python FastAPI, Vue.js

**SCOPE UPDATES (2025-12-11)**:
- **Single Form Type**: HNW CMB APP 2 (30 pages, bilingual English/Simplified Chinese)
- **No Classification**: Classification feature deferred to production (single form type) - **Phase 4 tasks removed**
- **7 Fields**: family_name, given_name, address, date_of_birth, place_of_birth, health_details, financial_information
- **Cosmos DB**: NoSQL database for simple lookups (no SQL, no migrations)
- **Vue.js + FastAPI**: Frontend/backend framework decisions finalized
- **No Authentication**: Open access for POC (internal environment) - Auth tasks removed
- **Simplified**: No complex error handling, drift detection, performance testing, backups for POC
- **Bilingual**: OCR, extraction, summarization support English + Simplified Chinese
- **Concurrent Processing**: Task queue for 10 simultaneous documents
- **No Training Data**: Zero-shot/few-shot LLM extraction only

**TASK COUNT IMPACT**:
- **Original**: 294 tasks across 11 phases
- **Updated**: ~220 tasks (removed ~74 classification, auth, complex monitoring tasks)
- **Phases Affected**: Phase 1 (simplified), Phase 2 (Cosmos DB, no auth), **Phase 4 (removed entirely)**, Phase 5 (no training), Phase 7 (Vue.js), Phase 9 (simplified monitoring)

**KEY DEFERRED ITEMS** (Not in POC):
- Multi-form classification (US-2.x tasks)
- Training data collection and model fine-tuning
- Authentication and RBAC
- Sophisticated retry logic and circuit breakers
- Real-time drift detection and alerting
- Automated performance testing
- Database backups and disaster recovery
- API rate limiting

---

## Task Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, etc.) - only for user story phases
- File paths included for each task

---

## Phase 1: Setup & Infrastructure (Week 1-2) 🏗️

**Purpose**: Project initialization, Azure infrastructure provisioning, and data preparation

**Gate Criteria**: 
- Azure services accessible and tested
- Ground truth data available (min 100 documents)
- Schemas approved by stakeholders

### Azure Infrastructure Provisioning

- [ ] T001 Create Azure resource group for POC in Contoso subscription
- [ ] T002 [P] Provision Azure Blob Storage with containers: `poc-documents-raw`, `poc-preprocessed-images`
- [ ] T003 [P] Provision Azure AI Document Intelligence resource and verify API access (Layout API model)
- [ ] T004 [P] Provision Azure OpenAI Service (GPT-4o with 120 TPM quota confirmed)
- [ ] T005 [P] Provision Azure Cosmos DB (NoSQL for simple lookups, partition key: document_id)
- [ ] T006 [P] Provision Azure Service Bus or Redis for task queue (concurrent processing of 10 documents)
- [ ] T007 [P] Configure Azure Monitor and Application Insights for basic logging
- [ ] T008 ~~Setup Azure Key Vault for secrets management~~ **DEFERRED** (no auth for POC, credentials in env vars)

### Project Structure & Configuration

- [ ] T009 Create Git repository structure: `src/`, `tests/`, `config/`, `docs/`, `scripts/`
- [ ] T010 [P] Initialize Python project with dependencies: fastapi, uvicorn, azure-storage-blob, azure-ai-documentintelligence, openai, azure-cosmos, pydantic
- [ ] T011 [P] Configure environment files: `.env.example` with Azure credentials (endpoint, key, subscription)
- [ ] T012 [P] Setup CI/CD pipeline skeleton in `.github/workflows/`
- [ ] T013 [P] Configure linting and formatting: black, ruff, mypy

### Schema & Data Contract Definition

- [ ] T014 ~~Identify 2 specific application forms (Form A, Form B) with Product Owner (Q-001)~~ **RESOLVED**: Single form HNW CMB APP 2
- [ ] T015 ~~Define 5-6 extraction fields per form type with SME input (Q-002)~~ **RESOLVED**: 7 fields defined (family_name, given_name, address, date_of_birth, place_of_birth, health_details, financial_information)
- [ ] T016 [P] Create field extraction JSON schema in `config/schemas/hnw_cmb_app2_schema.json` (7 fields, bilingual support)
- [ ] T017 [P] Create data contract schemas: ingestion, OCR output, extraction, summarization in `config/schemas/contracts/` (no classification schema needed)
- [ ] T018 [P] Version all schemas (v1.0.0) using semantic versioning
- [ ] T019 [P] Document schema validation rules and bilingual field handling in `docs/schemas.md`

### Data Collection & Preparation

- [ ] T020 ~~Collect training dataset: 20-50 labeled documents per form type (Form A, Form B, Unknown)~~ **NOT REQUIRED**: Zero-shot LLM extraction, no training data
- [ ] T021 ~~Collect validation dataset: 20-30 labeled documents per form type~~ **NOT REQUIRED**
- [ ] T022 Collect test dataset: 5-10 HNW CMB APP 2 samples with ground truth for validation
- [ ] T023 [P] Upload test documents to Azure Blob Storage container `poc-documents-test`
- [ ] T024 [P] Create ground truth labels JSON: document_id, 7 field values (family_name, given_name, etc.)
- [ ] T025 Store manual summaries (if available) for 1-5 documents for ROUGE/BERTScore evaluation

### Configuration & Prompt Library

- [ ] T026 [P] Create configuration contract in `config/app_config.json` (OCR Layout API settings, GPT-4o model, temperature values, concurrency=10)
- [ ] T027 [P] Create prompt library directory: `config/prompts/`
- [ ] T028 ~~Draft initial classification prompt template~~ **DEFERRED**: No classification for POC
- [ ] T029 [P] Draft initial extraction prompt template in `config/prompts/extraction_v1.txt` (bilingual English/Chinese, 7 fields, zero-shot)
- [ ] T030 [P] Draft initial summarization prompt template in `config/prompts/summarization_v1.txt` (bilingual, page-level citations, 150-300 words)

**Checkpoint**: Infrastructure provisioned, schemas defined, datasets ready

---

## Phase 2: Foundational Components (Week 2-3) 🧱

**Purpose**: Core infrastructure that MUST be complete before user story implementation

**Gate Criteria**: 
- Database schema deployed and tested
- Authentication working
- Logging and monitoring functional

### Database Schema & Models

- [ ] T031 Design Cosmos DB collections: documents, extractions, summaries, feedback (NoSQL schema, partition key: document_id)
- [ ] T032 ~~Create database migration scripts~~ **NOT NEEDED**: NoSQL schema-on-write
- [ ] T033 [P] Implement base Pydantic models in `src/models/base.py` (for JSON validation)
- [ ] T034 [P] Implement Document model in `src/models/document.py`
- [ ] T035 ~~Implement Classification model~~ **DEFERRED**: No classification for POC
- [ ] T036 [P] Implement Extraction model in `src/models/extraction.py` (7 fields schema)
- [ ] T037 [P] Implement Summary model in `src/models/summary.py`
- [ ] T038 [P] Implement Feedback model in `src/models/feedback.py`
- [ ] T039 Create Cosmos DB collections via Azure SDK or portal (no migration scripts)

### Core Infrastructure

- [ ] T040 Implement Azure Blob Storage client wrapper in `src/infrastructure/blob_storage.py`
- [ ] T041 [P] Implement Azure AI Document Intelligence client (Layout API) in `src/infrastructure/document_intelligence.py`
- [ ] T042 [P] Implement Azure OpenAI client wrapper (GPT-4o) in `src/infrastructure/openai_client.py`
- [ ] T043 [P] Implement Cosmos DB connection manager in `src/infrastructure/cosmos_db.py`
- [ ] T044 [P] Implement configuration loader in `src/infrastructure/config.py`
- [ ] T045 [P] Implement prompt loader with versioning in `src/infrastructure/prompt_loader.py`
- [ ] T046 [P] Implement task queue client (Azure Service Bus or Redis) in `src/infrastructure/task_queue.py` for concurrent processing

### Logging & Monitoring

- [ ] T047 Implement DEBUG-level logging with trace IDs in `src/infrastructure/logging.py` (maximum verbosity)
- [ ] T048 [P] Configure Azure Application Insights integration (optional)
- [ ] T049 [P] Create logging decorators for API endpoints and service methods
- [ ] T050 ~~Setup custom metrics endpoint~~ **SIMPLIFIED**: Basic Azure Monitor metrics only

### API Framework (No Authentication)

- [ ] T051 ~~Implement basic authentication~~ **NOT REQUIRED**: No auth for POC (internal environment)
- [ ] T052 [P] Setup FastAPI application with CORS middleware in `src/api/app.py`
- [ ] T053 [P] Implement API error handlers (technical error messages) in `src/api/error_handlers.py`
- [ ] T054 [P] Create API response models using Pydantic in `src/api/schemas/`

### Utility Functions

- [ ] T055 [P] Implement schema validation utilities in `src/utils/schema_validator.py`
- [ ] T056 [P] Implement text normalization utilities (bilingual support) in `src/utils/text_normalizer.py`
- [ ] T057 [P] Implement date/currency normalization (ISO8601, infer currency from doc) in `src/utils/field_normalizer.py`
- [ ] T058 ~~Implement retry logic with exponential backoff~~ **SIMPLIFIED**: No automatic retries for POC
- [ ] T059 [P] Implement OpenCV image preprocessing utilities in `src/utils/image_preprocessor.py` (rotation, deskew, denoise)

**Checkpoint**: Foundation complete - user story implementation can now begin

---

## Phase 3: Document Ingestion & OCR (Week 3-4) 📄

**User Story US-1.1**: As an engineer, I want to upload documents via API so that they can be processed automatically  
**User Story US-1.2**: As a data scientist, I want high-quality OCR output so that extraction accuracy is maximized  
**User Story US-1.3**: As a developer, I want layout information so that I can understand document structure

**Goal**: Accept document uploads, perform OCR with Azure AI Document Intelligence, extract layout, and prepare clean text

**Independent Test**: Upload a document → verify OCR text extracted → verify layout JSON stored → verify normalized text available

### Ingestion API Implementation

- [ ] T058 [P] [US1] Implement file upload validation (size, type, magic number) in `src/services/validation_service.py`
- [ ] T059 [US1] Implement ingestion API endpoint: POST /api/v1/ingest in `src/api/routes/ingestion.py`
- [ ] T060 [US1] Implement document storage service in `src/services/storage_service.py` (upload to Azure Blob)
- [ ] T061 [US1] Create database record for uploaded document with status tracking
- [ ] T062 [US1] Return ingestion response with document_id, status, timestamp

### OCR Processing Pipeline

- [ ] T063 [P] [US1] Implement OCR service using Azure AI Document Intelligence Read API in `src/services/ocr_service.py`
- [ ] T064 [US1] Add retry logic for OCR failures (3 attempts, exponential backoff)
- [ ] T065 [US1] Extract text with bounding boxes and confidence scores
- [ ] T066 [US1] Store raw OCR output JSON in database and blob storage
- [ ] T067 [US1] Log OCR metrics: processing time, confidence scores, error rates

### Layout Extraction

- [ ] T068 [P] [US1] Implement layout extraction using Azure AI Document Intelligence Layout API in `src/services/layout_service.py`
- [ ] T069 [US1] Extract text blocks, lines, tables with bounding boxes
- [ ] T070 [US1] Store layout JSON with schema: page_number, blocks[], lines[], tables[], reading_order[]
- [ ] T071 [US1] Link layout information to OCR output for citation generation

### Text Normalization

- [ ] T072 [P] [US1] Implement text normalization pipeline in `src/services/text_normalization_service.py`
- [ ] T073 [US1] Remove OCR artifacts (spurious characters, duplicates)
- [ ] T074 [US1] Normalize whitespace (line breaks, spacing)
- [ ] T075 [US1] Handle hyphenated words at line breaks
- [ ] T076 [US1] Maintain mapping: normalized_text_offset → original_bbox for citations
- [ ] T077 [US1] Store both raw and normalized text in database

### Testing & Validation

- [ ] T078 [US1] Test OCR accuracy on 50+ page test set (target: >98% character accuracy)
- [ ] T079 [US1] Test processing time benchmark (target: <1 min per 10 pages)
- [ ] T080 [US1] Test API response time (target: <2s for upload acknowledgment)
- [ ] T081 [US1] Test error handling: invalid formats, oversized files, OCR failures

**Checkpoint**: Document ingestion → OCR → layout extraction → text normalization pipeline functional

---

## Phase 4: Document Classification (Week 4-5) 🏷️

**User Story US-2.1**: As a data scientist, I want to classify documents accurately so that correct extraction logic is applied  
**User Story US-2.2**: As an underwriter, I want to see classification confidence so that I can trust the system  
**User Story US-2.3**: As a product owner, I want a confusion matrix so that I can understand classification errors

**Goal**: Automatically classify documents into Form A, Form B, or Unknown with >95% accuracy

**Independent Test**: Feed normalized text → get classification (Form A/B/Unknown) → verify confidence score → validate against ground truth

### Classification Model Implementation

- [ ] T082 [P] [US2] Implement Azure OpenAI few-shot classification in `src/services/classification_service.py`
- [ ] T083 [US2] Load classification prompt template from `config/prompts/classification_v1.txt`
- [ ] T084 [US2] Format prompt with document text (first 2000 tokens)
- [ ] T085 [US2] Parse JSON response: classification, confidence, reasoning
- [ ] T086 [US2] Store classification result in database with model_version
- [ ] T087 [US2] Add error handling for API timeouts and invalid responses

### Baseline Experiments

- [ ] T088 [P] [US2] Implement Azure ML custom classifier baseline (optional) in `src/experiments/classification_baseline.py`
- [ ] T089 [US2] Implement rule-based classifier baseline for comparison
- [ ] T090 [US2] Run experiments on validation set: Azure OpenAI, Azure ML, rule-based
- [ ] T091 [US2] Document accuracy, latency, cost for each approach in `docs/adr/classification-approach.md`
- [ ] T092 [US2] Select best approach meeting >95% accuracy target (Architecture Decision Record)

### Evaluation & Metrics

- [ ] T093 [P] [US2] Implement confusion matrix generation in `src/evaluation/classification_evaluator.py`
- [ ] T094 [US2] Calculate precision, recall, F1 score per class (Form A, Form B, Unknown)
- [ ] T095 [US2] Run evaluation on test set (50+ documents)
- [ ] T096 [US2] Generate confusion matrix heatmap visualization
- [ ] T097 [US2] Analyze misclassified samples for error patterns
- [ ] T098 [US2] Store evaluation results in database with timestamp

### Testing & Validation

- [ ] T099 [US2] Test classification on edge cases: partial documents, rotated images, poor quality
- [ ] T100 [US2] Test classification latency (target: <30s per document)
- [ ] T101 [US2] Validate >95% precision and recall on test set
- [ ] T102 [US2] Validate Unknown category rate <10% on valid forms

**Checkpoint**: Classification model achieves >95% accuracy, confusion matrix validated, best approach selected

---

## Phase 5: Field Extraction (Week 5-7) 🔍

**User Story US-3.1**: As an underwriter, I want key fields extracted automatically so that I don't manually re-type data  
**User Story US-3.2**: As a data scientist, I want validation rules so that extracted data is accurate  
**User Story US-3.3**: As an engineer, I want normalized fields so that downstream systems can consume them

**Goal**: Extract 5-6 structured fields per document type with >90% completeness and correctness

**Independent Test**: Feed classified document → extract fields → verify against ground truth → validate normalization

### Rule-Based Extraction

- [ ] T103 [P] [US3] Implement rule-based extraction service in `src/services/rule_extraction_service.py`
- [ ] T104 [US3] Define regex patterns for structured fields (dates, amounts, names) in `config/extraction_rules.json`
- [ ] T105 [US3] Implement keyword proximity matching (e.g., "Applicant Name:" + text)
- [ ] T106 [US3] Use Azure AI Document Intelligence key-value pair extraction
- [ ] T107 [US3] Return extracted fields with confidence scores
- [ ] T108 [US3] Handle extraction failures gracefully (return null with reason)

### LLM-Based Extraction

- [ ] T109 [P] [US3] Implement Azure OpenAI extraction service in `src/services/llm_extraction_service.py`
- [ ] T110 [US3] Load extraction prompt template from `config/prompts/extraction_v1.txt`
- [ ] T111 [US3] Format prompt with field schema and document text
- [ ] T112 [US3] Parse JSON response matching field schema
- [ ] T113 [US3] Extract confidence scores per field
- [ ] T114 [US3] Handle missing fields gracefully (return null)
- [ ] T115 [US3] Add timeout handling (target: <20s per document)

### Hybrid Extraction Pipeline

- [ ] T116 [US3] Implement hybrid extraction orchestrator in `src/services/extraction_service.py`
- [ ] T117 [US3] Try rule-based extraction first for high-confidence fields
- [ ] T118 [US3] Fall back to LLM extraction for low-confidence or failed extractions
- [ ] T119 [US3] Merge results from both approaches (prefer higher confidence)
- [ ] T120 [US3] Store extraction method used (rule_based, llm, hybrid) in database

### Field Post-Processing

- [ ] T121 [P] [US3] Implement field normalization service in `src/services/field_normalization_service.py`
- [ ] T122 [US3] Normalize dates to ISO8601 format using dateutil
- [ ] T123 [US3] Normalize currency amounts (remove symbols, convert to float)
- [ ] T124 [US3] Normalize names (title-case, trim whitespace)
- [ ] T125 [US3] Normalize addresses (consistent format)
- [ ] T126 [US3] Store both raw and normalized field values

### Validation

- [ ] T127 [P] [US3] Implement field validation service in `src/services/field_validation_service.py`
- [ ] T128 [US3] Enforce field-level validation rules (range checks, format checks, required/optional)
- [ ] T129 [US3] Implement cross-field validation (e.g., end_date > start_date)
- [ ] T130 [US3] Flag validation errors with warnings (non-blocking for POC)
- [ ] T131 [US3] Log validation issues for review

### Testing & Evaluation

- [ ] T132 [US3] Test extraction on 50+ documents per form type with ground truth
- [ ] T133 [US3] Calculate extraction completeness: (fields extracted / fields present)
- [ ] T134 [US3] Calculate extraction correctness: (correct values / extracted fields)
- [ ] T135 [US3] Test edge cases: missing fields, handwritten values, ambiguous content
- [ ] T136 [US3] Validate >90% completeness and correctness on test set
- [ ] T137 [US3] Test processing time (target: <30s per document including OCR)

**Checkpoint**: Extraction pipeline achieves >90% completeness and correctness, hybrid approach functional

---

## Phase 6: Document Summarization (Week 7-9) 📝

**User Story US-4.1**: As an underwriter, I want concise summaries so that I can quickly understand key information  
**User Story US-4.2**: As a compliance officer, I want citations so that I can verify summary accuracy  
**User Story US-4.3**: As a product owner, I want summary quality metrics so that I can validate AI performance

**Goal**: Generate extractive and abstractive summaries with citations, achieving quality comparable to manual summaries

**Independent Test**: Feed document text + extracted fields → generate summaries → verify citations → compare against manual summaries

### Extractive Summarization

- [ ] T138 [P] [US4] Implement extractive summarization service in `src/services/extractive_summary_service.py`
- [ ] T139 [US4] Use Azure OpenAI to extract 5-10 key facts from document
- [ ] T140 [US4] Load extractive prompt template from `config/prompts/extractive_summary_v1.txt`
- [ ] T141 [US4] Parse JSON response with facts, page numbers, importance levels
- [ ] T142 [US4] Order facts by importance or document order
- [ ] T143 [US4] Target summary length: 200-500 words

### Abstractive Summarization

- [ ] T144 [P] [US4] Implement abstractive summarization service in `src/services/abstractive_summary_service.py`
- [ ] T145 [US4] Load abstractive prompt template from `config/prompts/summarization_v1.txt`
- [ ] T146 [US4] Include critical information: names, amounts, dates, key conditions
- [ ] T147 [US4] Generate coherent summary (150-300 words)
- [ ] T148 [US4] Include page number citations in parentheses for each claim
- [ ] T149 [US4] Test summary generation latency (target: <30s)

### Citation Mapping

- [ ] T150 [P] [US4] Implement citation mapping service in `src/services/citation_service.py`
- [ ] T151 [US4] Map summary claims to source document locations (page, bounding box)
- [ ] T152 [US4] Use layout information from OCR to link citations
- [ ] T153 [US4] Store citations as JSON: [{claim, page, bbox, confidence}]
- [ ] T154 [US4] Validate citation accuracy: all citations verifiable

### Summary Orchestration

- [ ] T155 [US4] Implement summary orchestration service in `src/services/summary_service.py`
- [ ] T156 [US4] Generate extractive summary first
- [ ] T157 [US4] Generate abstractive summary with citations
- [ ] T158 [US4] Store both summaries in database with model_version
- [ ] T159 [US4] Link summaries to extracted fields for context

### Summary Evaluation

- [ ] T160 [P] [US4] Define evaluation criteria with SME (Anish) by week 8 (Q-003)
- [ ] T161 [US4] Implement summary evaluator in `src/evaluation/summary_evaluator.py`
- [ ] T162 [US4] Collect manual summaries for 50+ test documents
- [ ] T163 [US4] Calculate ROUGE-L scores (target: >0.6)
- [ ] T164 [US4] Calculate BERTScore for semantic similarity (target: >0.8)
- [ ] T165 [US4] Conduct manual evaluation by SME on 20-50 summaries
- [ ] T166 [US4] Document evaluation results in `docs/evaluation-report.md`

### Testing & Validation

- [ ] T167 [US4] Test summary accuracy: no factual errors (target: >90%)
- [ ] T168 [US4] Test summary completeness: critical fields included (target: >85%)
- [ ] T169 [US4] Validate citation accuracy: 100% verifiable
- [ ] T170 [US4] Test readability and coherence with SME feedback

**Checkpoint**: Summarization achieves quality benchmarks, citations verified, evaluation complete

---

## Phase 7: POC Viewer UI (Week 9-10) 🖥️

**User Story US-5.1**: As an underwriter, I want to view summaries so that I can validate AI outputs  
**User Story US-5.2**: As an underwriter, I want to click citations so that I can verify source text  
**User Story US-5.3**: As a product owner, I want to see extracted fields so that I can validate extraction quality  
**User Story US-5.4**: As a user, I want simple feedback buttons so that I can mark outputs as correct/incorrect

**Goal**: Provide web-based interface to view summaries, extracted fields, and source documents for POC validation

**Independent Test**: Load UI → select document → view summary → click citation → verify document highlights → provide feedback

### Frontend Setup

- [ ] T171 Initialize React or Vue.js project in `frontend/`
- [ ] T172 [P] Setup build configuration with Vite or webpack
- [ ] T173 [P] Configure TypeScript and ESLint
- [ ] T174 [P] Install dependencies: axios, react-router, PDF.js
- [ ] T175 [P] Create responsive layout components in `frontend/src/components/layout/`

### Summary Viewer

- [ ] T176 [P] [US5] Implement summary viewer component in `frontend/src/components/SummaryViewer.tsx`
- [ ] T177 [US5] Display abstractive summary prominently
- [ ] T178 [US5] Add toggle for extractive facts display
- [ ] T179 [US5] Make citations clickable links
- [ ] T180 [US5] Handle citation click events to highlight document

### Field Viewer

- [ ] T181 [P] [US5] Implement field viewer component in `frontend/src/components/FieldViewer.tsx`
- [ ] T182 [US5] Display extracted fields in structured format
- [ ] T183 [US5] Show confidence scores with visual indicators (✓ >0.9, ⚠ 0.7-0.9, ✗ <0.7)
- [ ] T184 [US5] Clearly indicate null/missing fields
- [ ] T185 [US5] Group fields by category (optional)

### Document Viewer

- [ ] T186 [P] [US5] Implement PDF/image viewer using PDF.js in `frontend/src/components/DocumentViewer.tsx`
- [ ] T187 [US5] Add text highlighting for cited content using bounding boxes
- [ ] T188 [US5] Implement page navigation controls
- [ ] T189 [US5] Add zoom controls
- [ ] T190 [US5] Synchronize scrolling with citation clicks (<500ms response)

### Backend API for UI

- [ ] T191 [P] [US5] Implement GET /api/v1/documents endpoint in `src/api/routes/documents.py`
- [ ] T192 [US5] Implement GET /api/v1/documents/{id}/summary endpoint
- [ ] T193 [US5] Implement GET /api/v1/documents/{id}/fields endpoint
- [ ] T194 [US5] Implement GET /api/v1/documents/{id}/content endpoint (blob URL)
- [ ] T195 [US5] Add CORS configuration for frontend

### Feedback Mechanism (Optional - Q-005)

- [ ] T196 [P] [US5] Implement feedback API: POST /api/v1/feedback in `src/api/routes/feedback.py`
- [ ] T197 [US5] Add thumbs up/down buttons to UI
- [ ] T198 [US5] Add optional comment field
- [ ] T199 [US5] Store feedback in database with document_id, component, rating, comment
- [ ] T200 [US5] Display feedback confirmation to user

### Deployment

- [ ] T201 [US5] Build frontend for production
- [ ] T202 [US5] Deploy backend API to Azure App Service
- [ ] T203 [US5] Deploy frontend to Azure Static Web Apps
- [ ] T204 [US5] Configure custom domain and HTTPS

### Testing & Validation

- [ ] T205 [US5] Test UI load time (target: <2s)
- [ ] T206 [US5] Test citation navigation responsiveness
- [ ] T207 [US5] Test browser compatibility: Chrome, Edge
- [ ] T208 [US5] Conduct usability testing with SME (target: 4/5 rating)

**Checkpoint**: UI functional, responsive, citation navigation working, SME feedback positive

---

## Phase 8: Data Contracts & Model Registry (Week 10-11) 📋

**User Story US-6.1**: As an engineer, I want versioned schemas so that I can maintain backward compatibility  
**User Story US-6.2**: As a data scientist, I want a model registry so that I can track model versions  
**User Story US-6.3**: As an operations engineer, I want audit logs so that I can debug issues  
**User Story US-6.4**: As an architect, I want documented patterns so that production scaling is straightforward

**Goal**: Establish reusable data contracts, configuration patterns, and infrastructure for POC and production scalability

**Independent Test**: Validate schema enforcement → check model registry → verify audit logs → review documentation

### Configuration Management

- [ ] T209 [P] [US6] Finalize configuration contract in `config/app_config.json`
- [ ] T210 [US6] Version all configurations (semantic versioning)
- [ ] T211 [US6] Implement configuration validation on application startup
- [ ] T212 [US6] Create environment-specific configs: dev, test, prod-ready
- [ ] T213 [US6] Document configuration schema in `docs/configuration.md`

### Data Contract Finalization

- [ ] T214 [P] [US6] Finalize JSON schemas for all outputs in `config/schemas/contracts/`
- [ ] T215 [US6] Implement schema validation in all API endpoints
- [ ] T216 [US6] Generate schema documentation automatically
- [ ] T217 [US6] Test breaking changes detection (major version bump required)
- [ ] T218 [US6] Document schema versioning policy in `docs/schema-versioning.md`

### Model Registry

- [ ] T219 [P] [US6] Register classification model in Azure ML Model Registry
- [ ] T220 [US6] Register extraction model (prompts, configs) in Azure ML Model Registry
- [ ] T221 [US6] Register summarization model (prompts, configs) in Azure ML Model Registry
- [ ] T222 [US6] Add model metadata: version, accuracy, latency, cost
- [ ] T223 [US6] Track model lineage: training data, evaluation results
- [ ] T224 [US6] Tag models: poc, production-ready, deprecated
- [ ] T225 [US6] Document model deployment history

### Audit Logging Enhancement

- [ ] T226 [P] [US6] Review audit log completeness (100% of processing steps)
- [ ] T227 [US6] Validate trace ID propagation across all components
- [ ] T228 [US6] Test log retention policy (POC duration + 30 days)
- [ ] T229 [US6] Create log analysis queries in Azure Monitor
- [ ] T230 [US6] Document logging patterns in `docs/logging.md`

### Documentation

- [ ] T231 [P] [US6] Document architecture patterns in `docs/architecture.md`
- [ ] T232 [US6] Document API contracts with OpenAPI/Swagger in `docs/api-spec.yaml`
- [ ] T233 [US6] Document deployment procedures in `docs/deployment.md`
- [ ] T234 [US6] Create runbook for common operations in `docs/runbook.md`
- [ ] T235 [US6] Document production scaling recommendations in `docs/production-scaling.md`

**Checkpoint**: All contracts versioned, models registered, audit logs complete, patterns documented

---

## Phase 9: Monitoring & Observability (Week 11) 📊

**Purpose**: Establish monitoring dashboards and drift detection for POC and production readiness

### Monitoring Dashboards

- [ ] T236 [P] Create Azure Monitor dashboard for OCR quality metrics
- [ ] T237 [P] Create dashboard for classification accuracy, confusion matrix, confidence distribution
- [ ] T238 [P] Create dashboard for extraction completeness, correctness, latency
- [ ] T239 [P] Create dashboard for summarization metrics (length, citation count, latency)
- [ ] T240 [P] Create dashboard for system metrics (API latency, error rates, throughput)
- [ ] T241 Configure real-time dashboard updates during POC

### Drift Detection

- [ ] T242 [P] Implement drift detection service in `src/services/drift_detection_service.py`
- [ ] T243 Establish baseline metrics for classification distribution (Form A vs B vs Unknown)
- [ ] T244 Track average confidence scores per component over time
- [ ] T245 Track OCR quality metrics over time
- [ ] T246 Track field extraction success rates over time
- [ ] T247 Configure alerts if metrics deviate >10% from baseline
- [ ] T248 Generate weekly drift reports

### Performance Testing

- [ ] T249 Test API upload response time (target: <2s)
- [ ] T250 Test OCR processing time (target: <1 min per 10 pages)
- [ ] T251 Test classification latency (target: <30s)
- [ ] T252 Test extraction latency (target: <30s)
- [ ] T253 Test summarization latency (target: <30s)
- [ ] T254 Test full pipeline (target: <5 min per document)
- [ ] T255 Test UI page load time (target: <2s)

**Checkpoint**: Monitoring dashboards live, drift detection functional, performance validated

---

## Phase 10: POC Evaluation & Demo (Week 12) 🎯

**Purpose**: Complete SME evaluation, prepare stakeholder demo, document results, secure production funding

**Gate Criteria**: 
- All P0 goals achieved (>95% classification, >90% extraction, quality summaries)
- Stakeholder demo successful (4/5 satisfaction)
- Production funding approved

### Evaluation Execution

- [ ] T256 Run final classification evaluation on full test set (50+ documents)
- [ ] T257 Run final extraction evaluation on full test set (50+ documents per form)
- [ ] T258 Conduct SME evaluation of 20-50 summaries (Anish)
- [ ] T259 Calculate all success metrics vs targets
- [ ] T260 Generate confusion matrices and accuracy tables
- [ ] T261 Collect sample outputs (summaries, extractions) for demo
- [ ] T262 Document evaluation results in `docs/evaluation-report.md`

### Demo Preparation

- [ ] T263 Prepare demo script with 3-5 representative documents
- [ ] T264 Create demo presentation slides with success metrics
- [ ] T265 Test demo workflow end-to-end
- [ ] T266 Prepare backup plan for live demo issues
- [ ] T267 Schedule stakeholder demo session

### Production Recommendations

- [ ] T268 Document production architecture recommendations
- [ ] T269 Estimate costs for production (Azure services, compute, storage)
- [ ] T270 Estimate timeline for production rollout (40-50 document types)
- [ ] T271 Identify risks and mitigation strategies
- [ ] T272 Define production readiness checklist
- [ ] T273 Document security and compliance requirements for production

### Stakeholder Demo

- [ ] T274 Conduct stakeholder demo session
- [ ] T275 Collect stakeholder feedback and satisfaction ratings
- [ ] T276 Address questions and concerns
- [ ] T277 Present cost analysis and production timeline
- [ ] T278 Secure go/no-go decision for production funding

### Final Documentation

- [ ] T279 Complete end-of-POC evaluation report
- [ ] T280 Document lessons learned
- [ ] T281 Create handoff documentation for production team
- [ ] T282 Archive POC codebase and datasets
- [ ] T283 Update project constitution with POC results

**Checkpoint**: POC evaluation complete, demo successful, production funding secured

---

## Phase 11: Polish & Cross-Cutting Concerns 🎨

**Purpose**: Final improvements, code quality, security hardening

- [ ] T284 [P] Code review and refactoring for maintainability
- [ ] T285 [P] Security audit: dependency vulnerabilities, secrets management
- [ ] T286 [P] Performance optimization: caching, query optimization
- [ ] T287 [P] Documentation review and updates
- [ ] T288 [P] Add comprehensive unit tests (target: >80% coverage for business logic)
- [ ] T289 [P] Add integration tests for critical workflows
- [ ] T290 Error handling improvements across all services
- [ ] T291 Accessibility review for UI (WCAG 2.1 AA compliance)
- [ ] T292 Browser compatibility testing (Chrome, Edge, Safari, Firefox)
- [ ] T293 Load testing: 10+ concurrent document processing
- [ ] T294 Final security hardening: HTTPS, TLS 1.3, CORS policies

**Checkpoint**: POC code production-ready, security validated, documentation complete

---

## Dependencies & Execution Order

### Phase Dependencies

1. **Setup (Phase 1)**: No dependencies - start immediately
2. **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user story work
3. **User Story Phases (Phase 3-8)**: All depend on Foundational phase completion
   - Can proceed sequentially in priority order: US1 → US2 → US3 → US4 → US5 → US6
   - Or in parallel if team capacity allows
4. **Monitoring (Phase 9)**: Can start once any user story generates data
5. **Evaluation (Phase 10)**: Depends on all P0 user stories complete (US1-US4)
6. **Polish (Phase 11)**: Depends on evaluation complete

### Critical Path (Sequential Dependencies)

```
Setup → Foundational → Ingestion/OCR → Classification → Extraction → Summarization → UI → Evaluation → Demo
```

### User Story Dependencies

- **US1 (Ingestion/OCR)**: Independent - can start after Foundational
- **US2 (Classification)**: Depends on US1 (needs normalized text)
- **US3 (Extraction)**: Depends on US2 (needs classified documents)
- **US4 (Summarization)**: Depends on US1 (needs text), can use US3 outputs (fields)
- **US5 (UI)**: Depends on US1-US4 (displays all outputs)
- **US6 (Contracts)**: Can proceed in parallel with other stories, finalized at end

### Parallel Opportunities by Phase

**Phase 1 (Setup)**: T002-T008 (Azure provisioning), T010-T013 (project setup), T016-T019 (schemas), T023-T024 (data upload), T026-T030 (config/prompts)

**Phase 2 (Foundational)**: T033-T038 (models), T040-T045 (infrastructure clients), T047-T049 (logging), T051-T053 (API setup), T054-T057 (utils)

**Phase 3 (Ingestion/OCR)**: T058, T063, T068, T072 can start in parallel, then sequential pipelines

**Phase 4 (Classification)**: T082, T088, T089, T093 can start in parallel

**Phase 5 (Extraction)**: T103, T109 can start in parallel, T121, T127 can proceed in parallel

**Phase 6 (Summarization)**: T138, T144, T150 can start in parallel

**Phase 7 (UI)**: T172-T175 (frontend setup), T176, T181, T186, T191 can start in parallel

**Phase 8 (Contracts)**: T209, T214, T219, T226, T231 can proceed in parallel

**Phase 9 (Monitoring)**: T236-T240 (dashboards), T242-T248 (drift) can proceed in parallel

**Phase 11 (Polish)**: T284-T289, T291-T294 can proceed in parallel

---

## Parallel Execution Examples

### Phase 1 Setup (Parallel):
```bash
# Team member 1: Azure infrastructure
T001-T008 (Azure provisioning)

# Team member 2: Project setup
T009-T013 (Git, Python, CI/CD)

# Team member 3: Schemas & data
T014-T025 (Schemas, data collection)

# Team member 4: Configuration
T026-T030 (Config, prompts)
```

### Phase 2 Foundational (Parallel):
```bash
# Team member 1: Database
T031-T039 (Schema, models, migrations)

# Team member 2: Infrastructure clients
T040-T045 (Blob, Document Intelligence, OpenAI, DB, config)

# Team member 3: API & logging
T046-T053 (Logging, auth, API framework)

# Team member 4: Utilities
T054-T057 (Schema validation, text normalization, retry logic)
```

### Phase 3-8 User Stories (Sequential for POC, or parallel with multiple teams):
```bash
# Option A: Sequential (single team)
US1 → US2 → US3 → US4 → US5 → US6

# Option B: Parallel (multiple teams)
Team 1: US1 (Ingestion/OCR)
Team 2: US2 (Classification) - starts after US1 T058-T077 complete
Team 3: US3 (Extraction) - starts after US2 complete
Team 4: US4 (Summarization) - starts after US1 complete
Team 5: US5 (UI) - starts after US1-US4 have APIs ready
Team 6: US6 (Contracts) - ongoing throughout
```

---

## MVP Definition (Minimum for Demo)

**Week 12 Stakeholder Demo Requires:**

✅ **US1**: Document upload → OCR → text extraction (T058-T077)  
✅ **US2**: Classification with >95% accuracy (T082-T102)  
✅ **US3**: Field extraction with >90% completeness (T103-T137)  
✅ **US4**: Summaries with citations (T138-T170)  
✅ **US5**: Viewer UI with clickable citations (T171-T208)  
✅ **Evaluation**: All metrics documented (T256-T262)

**Optional for MVP (can defer to production):**
- US6: Full data contracts (can document patterns during POC)
- US5: Feedback mechanism (Q-005 - can add post-demo)
- Phase 11: Full polish and security hardening

---

## Implementation Strategy

### Week-by-Week Breakdown

| Week | Phase | Key Deliverables | Tasks |
|------|-------|------------------|-------|
| 1-2 | Setup | Infrastructure, schemas, data | T001-T030 |
| 2-3 | Foundational | Database, clients, API framework | T031-T057 |
| 3-4 | Ingestion/OCR (US1) | Document upload, OCR pipeline | T058-T081 |
| 4-5 | Classification (US2) | Classification model, evaluation | T082-T102 |
| 5-7 | Extraction (US3) | Field extraction, validation | T103-T137 |
| 7-9 | Summarization (US4) | Summaries with citations | T138-T170 |
| 9-10 | UI (US5) | Viewer interface | T171-T208 |
| 10-11 | Contracts (US6) | Model registry, documentation | T209-T235 |
| 11 | Monitoring | Dashboards, drift detection | T236-T255 |
| 12 | Evaluation & Demo | Final metrics, demo, funding decision | T256-T283 |

### Staffing Recommendations

**Minimum Team (Sequential Execution):**
- 1 Data Scientist (classification, extraction, summarization models)
- 1 Backend Engineer (APIs, services, database)
- 1 Frontend Engineer (UI)
- 1 DevOps/MLOps (Azure infrastructure, monitoring)

**Optimal Team (Parallel Execution):**
- 2 Data Scientists (one for classification/extraction, one for summarization)
- 2 Backend Engineers (one for ingestion/OCR, one for APIs)
- 1 Frontend Engineer (UI)
- 1 DevOps/MLOps (infrastructure, monitoring)
- 1 Product Owner (requirements, SME coordination, demo)

---

## Open Questions & Decision Points

| Q ID | Question | Owner | Deadline | Blocking Tasks |
|------|----------|-------|---------|----------------|
| Q-001 | Which 2 specific application forms will be used? | Product Owner | Week 1 | T014 |
| Q-002 | What are the 5-6 fields per document type? | Product Owner / SME | Week 1 | T015 |
| Q-003 | What are the summary evaluation criteria? (Anish to provide) | SME (Anish) | Week 2 | T160 |
| Q-004 | Is summary of summaries in scope for POC? | Product Owner | Week 1 | (Optional feature) |
| Q-005 | What feedback mechanism is needed for POC? | Product Owner | Week 3 | T196-T200 |
| Q-006 | Azure SQL or Cosmos DB for structured storage? | Technical Lead | Week 1 | T005, T031 |
| Q-007 | Is Azure AI Document Intelligence provisioned and accessible? | Engineering | Week 1 | T003 |
| Q-008 | Is Azure OpenAI Service provisioned with sufficient quota? | Engineering / Security | Week 1 | T004 |

---

## Success Criteria (POC Goals)

### POC Success = ALL of the following:

✅ **G-001: Classification Accuracy**: >95% precision and recall on test set (T099-T102)  
✅ **G-002: Extraction Completeness**: >90% completeness and correctness on test set (T133-T137)  
✅ **G-003: Summary Quality**: ROUGE-L >0.6, BERTScore >0.8, SME rating >4/5 (T163-T170)  
✅ **G-004: Pipeline Functional**: End-to-end upload → OCR → classification → extraction → summarization (T058-T159)  
✅ **G-005: OCR Quality**: >98% character accuracy for typed English text (T078)  
✅ **G-006: Architecture Patterns**: Reusable patterns, data contracts, schemas documented (T209-T235)  

### Production Readiness (Post-POC):

- Security audit completed (T285)
- Compliance validation completed (T273)
- Performance testing at scale (T293)
- Multi-language support implemented (deferred from POC)
- Full HITL workflows designed (deferred from POC)
- Production infrastructure provisioned

---

**Total Tasks**: 294  
**Task Count by Phase**:
- Phase 1 (Setup): 30 tasks
- Phase 2 (Foundational): 27 tasks
- Phase 3 (US1 - Ingestion/OCR): 24 tasks
- Phase 4 (US2 - Classification): 21 tasks
- Phase 5 (US3 - Extraction): 35 tasks
- Phase 6 (US4 - Summarization): 33 tasks
- Phase 7 (US5 - UI): 38 tasks
- Phase 8 (US6 - Contracts): 27 tasks
- Phase 9 (Monitoring): 20 tasks
- Phase 10 (Evaluation): 28 tasks
- Phase 11 (Polish): 11 tasks

**Parallel Opportunities**: 85+ tasks marked [P] can run in parallel within their phases

**MVP Scope**: Phases 1-7 + Phase 10 (evaluation) = ~230 tasks for stakeholder demo

---

**Document Version**: 1.0  
**Generated**: 2025-12-11  
**Next Review**: End of Week 2 (after Q&A answers)

**Alignment**:
- Feature Spec: `/docs/specs/feature-spec-poc.md`
- PRD: `/docs/prds/hnw-underwriting-poc.md`
- Constitution: `/.specify/memory/constitution.md`
