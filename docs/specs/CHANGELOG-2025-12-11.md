---
description: "Changelog for feature spec and tasks updates based on stakeholder clarifications"
---

# Changelog: Feature Spec & Tasks Updates

**Date:** 2025-12-11  
**Updated Documents:**
- `feature-spec-poc.md` (v1.0 → v1.1)
- `tasks.md` (updated with scope changes)
- `underspecified-areas.md` (resolved all 38 questions)

---

## Summary of Changes

All 38 underspecified areas identified in the gap analysis have been resolved through stakeholder input. Major scope simplifications made to focus POC on core value demonstration.

---

## Feature Specification Updates (v1.1)

### 1. Scope Simplification: Single Form Type

**Before:**
- 2 form types (Form A, Form B) requiring classification
- Multi-class classifier with >95% accuracy target
- Training data: 20-50 labeled examples per class
- Confusion matrix and precision/recall metrics

**After:**
- **Single form type**: HNW CMB APP 2 (insurance application, 30 pages)
- **No classification needed**: All uploads assumed to be HNW CMB APP 2
- Classification feature deferred to production when additional form types onboarded
- Document type validation via optional filename pattern matching

**Impact:** Removed entire classification feature (FR-2.1, FR-2.2, FR-2.3), simplified architecture

---

### 2. Bilingual Document Support

**Before:**
- English-only documents
- Single language OCR and extraction

**After:**
- **Bilingual support**: English + Simplified Chinese
- OCR handles mixed-language content
- LLM extraction prompts adapted for bilingual text
- Field schemas support Chinese characters (UTF-8)
- Summary generation handles bilingual documents

**Impact:** Updated OCR, extraction, summarization requirements; increased processing time targets (30-page bilingual: <3 min OCR, <30s extraction, <40s summarization)

---

### 3. Field Schema Definition (7 Fields)

**Before:**
- Example schema with 6 placeholder fields (TBD with business)
- Separate schemas for Form A and Form B

**After:**
- **7 specific fields defined** for HNW CMB APP 2:
  1. `family_name` (string, required)
  2. `given_name` (string, required)
  3. `address` (string, required, kept as-is)
  4. `date_of_birth` (date, required, ISO8601 format)
  5. `place_of_birth` (string, required)
  6. `health_details` (object, optional, complex nested structure)
  7. `financial_information` (object, required, income/assets/liabilities)
- Single schema version: `hnw_cmb_app2_schema.json` v1.0
- Currency normalization: Infer from document (USD, HKD, CNY)
- Date normalization: Format `1-Jan-25` → `2025-01-01`

**Impact:** Concrete extraction targets, no cross-field validation rules for POC

---

### 4. Database Technology: Azure Cosmos DB

**Before:**
- "Azure SQL/Cosmos DB" (decision pending)
- SQL schema examples provided

**After:**
- **Azure Cosmos DB (NoSQL)** selected
- Partition key: `document_id`
- Collections: documents, extractions, summaries, feedback
- No relational integrity, no foreign keys
- Schema-on-write (no migrations)
- Multiple schema versions coexist
- Simple lookups only (no complex joins)

**Rationale:** 
- Expected volume: ~100 documents/month (low scale)
- Access pattern: Simple lookups by document_id
- No complex analytics needed for POC
- JSON-native storage (no ORM complexity)
- Schema flexibility for rapid iteration

**Impact:** Removed SQL migrations, SQLAlchemy models; added Cosmos DB SDK integration

---

### 5. Technology Stack Finalized

**Before:**
- Frontend: "React or Vue.js"
- Backend: "Flask or FastAPI"
- OCR: "Prebuilt Read model (or Layout for table extraction)"

**After:**
- **Frontend: Vue.js 3** with Composition API (team preference)
- **Backend: FastAPI** (async support, auto-generated OpenAPI docs)
- **OCR: Layout API for all documents** (comprehensive table extraction needed)
- **LLM: GPT-4o** (120 TPM quota confirmed)

**Impact:** Framework initialization can proceed, async architecture enables concurrent processing

---

### 6. Authentication Removed

**Before:**
- Basic authentication (username/password) for POC
- User management, password policies
- JWT token or session-based auth decision needed

**After:**
- **No authentication required for POC**
- Open access (internal trusted environment only)
- Azure AD integration deferred to production

**Impact:** Removed auth middleware, user management, API key logic; simplified API access

---

### 7. Simplified Error Handling & Monitoring

**Before:**
- Retry 3x with exponential backoff
- Circuit breaker pattern
- Complex fallback strategies
- Real-time drift detection
- Alert thresholds for all metrics
- Performance testing with JMeter/Locust

**After:**
- **Basic error handling only**: Log errors, return 500 (no automatic retries)
- **Technical error messages**: Full details for debugging (no user-friendly sanitization)
- **Simplified monitoring**: Azure Monitor dashboard, optional Application Insights
- **Alert if accuracy drops >50%** (no recipients, manual monitoring)
- **No drift detection** for POC
- **No automated performance testing**: Manual validation acceptable
- **DEBUG logging for all** (maximum verbosity, no PII redaction)

**Impact:** Removed retry utilities, circuit breaker logic, complex alerting; faster implementation

---

### 8. Data Retention & Backup

**Before:**
- "POC duration + 30 days" (vague)
- Daily database backups

**After:**
- **Retention: 2 weeks** (POC duration only)
- **No automated backups** (data loss acceptable for non-production)
- Manual cleanup post-POC
- Preprocessed images stored for auditability

**Impact:** Removed backup configuration tasks, simplified data lifecycle

---

### 9. UI Viewer Enhancements

**Before:**
- Basic viewer (PDF rendering, citations, zoom)
- Responsive design (unspecified)
- Bounding box citations (optional)

**After:**
- **Desktop-only** (1920x1080 primary, 1024x768 secondary, no mobile)
- **Side-by-side view**: Original document (left) vs extracted data (right)
- **Page-level citations**: Clickable links to page numbers (no bounding boxes required)
- **No download, print, or annotations** for POC
- **No keyboard navigation** (mouse/touch only)

**Impact:** Simplified UI requirements, focused on core functionality

---

### 10. Feedback Mechanism

**Before:**
- Scope decision by Week 3
- Thumbs up/down per component (summary, fields)
- Actionable feedback (trigger reprocessing)

**After:**
- **Nice to have** (not critical)
- **Document-level feedback only** (not component-level)
- Thumbs up/down + optional comment
- **Logged only** (no reprocessing triggers)
- Reviewed manually by underwriters weekly

**Impact:** Simplified feedback implementation, deferred advanced annotation features

---

### 11. Summarization Evaluation

**Before:**
- Manual summaries for 20-50 test documents
- Criteria TBD by SME (Anish)

**After:**
- **Manual summaries for 1-5 documents only** (limited POC scope)
- **Precision evaluation**: 1-5 scale across 5 dimensions (accuracy, completeness, citation quality, readability, conciseness)
- **Success threshold: >90% precision** (avg rating >4/5)
- ROUGE-L >0.6, BERTScore >0.8 (if ground truth available)
- **No inter-rater reliability checks** (single evaluator acceptable)

**Impact:** Reduced evaluation workload, clear success criteria

---

### 12. Summary of Summaries Deferred

**Before:**
- FR-4.3 marked Optional (P2), decision by Week 1

**After:**
- **Not included in POC**
- Single-document processing only
- Multi-document case handling (combined summaries, cross-document citations) deferred to production

**Impact:** Removed multi-document architecture complexity

---

### 13. No Training Data Required

**Before:**
- Training set: 20-50 labeled documents per class
- Validation set: 20-30 labeled documents per class
- Test set: 50+ labeled documents
- Manual labeling process needed

**After:**
- **No training data required**
- **Zero-shot or few-shot prompting** with GPT-4o
- Test set: 5-10 HNW CMB APP 2 samples with ground truth for validation
- No model fine-tuning for POC

**Impact:** Removed data collection, labeling tasks; faster POC start

---

### 14. Concurrent Processing

**Before:**
- Sequential processing implied
- Performance targets: "<1 min per 10 pages"

**After:**
- **Concurrent processing**: 10 documents simultaneously
- Task queue implementation (Azure Service Bus or Redis)
- Async FastAPI backend
- Performance targets updated for 30-page bilingual documents

**Impact:** Added task queue infrastructure, async architecture requirements

---

### 15. Success Criteria Updated

**Before:**
- ✅ Classification: >95% precision and recall
- ✅ OCR: >98% character accuracy for English
- ✅ Extraction: >90% completeness
- ✅ Summarization: ROUGE-L >0.6, BERTScore >0.8, SME >4/5

**After:**
- ~~Classification: Removed~~ (not applicable)
- ✅ OCR: >95% character accuracy for **bilingual** (English + Simplified Chinese)
- ✅ Extraction: >90% completeness for **7 fields**
- ✅ Summarization: ROUGE-L >0.6 (if available), SME **precision** rating >4/5
- ✅ Architecture: Reusable patterns documented
- ✅ Stakeholder Demo: Approval for production funding

---

## Tasks File Updates

### Phase 1: Setup & Infrastructure
- **T005**: Changed from "Azure SQL or Cosmos DB" → "Azure Cosmos DB"
- **T006**: Changed from "Azure ML workspace" → "Task queue (Service Bus/Redis)"
- **T008**: Changed from "Key Vault" → ~~Deferred~~ (no auth)
- **T010**: Updated dependencies: `azure-cosmos` (not `sqlalchemy`)
- **T014-T015**: Marked as **RESOLVED** (single form, 7 fields defined)
- **T016**: Single schema file: `hnw_cmb_app2_schema.json`
- **T020-T021**: ~~Training/validation datasets~~ → **NOT REQUIRED**
- **T022**: Reduced from 50+ to 5-10 test documents
- **T028**: ~~Classification prompt~~ → **DEFERRED**

### Phase 2: Foundational Components
- **T031-T039**: Cosmos DB collections (not SQL tables), removed migrations
- **T035**: ~~Classification model~~ → **DEFERRED**
- **T043**: Changed from `database.py` → `cosmos_db.py`
- **T046**: Added task queue client
- **T050-T051**: ~~Authentication~~ → **NOT REQUIRED**
- **T057**: ~~Retry logic~~ → **SIMPLIFIED**

### Phase 3: Document Ingestion & OCR
- Updated for Layout API (all documents), bilingual support
- Added preprocessing tasks (OpenCV: rotation, deskew, denoise)
- Updated performance targets: <3 min for 30-page bilingual form

### Phase 4: Document Classification
- **ENTIRE PHASE REMOVED** (~30 tasks)
- All US-2.x tasks deferred to production

### Phase 5: Field Extraction
- Updated for 7 specific fields
- Zero-shot LLM extraction (no training tasks)
- Bilingual prompt templates
- Confidence threshold: >0.9 for acceptance, <0.9 flagged for review
- No cross-field validation rules for POC

### Phase 6: Summarization
- Updated for bilingual documents (English + Simplified Chinese)
- Page-level citations only (not bounding boxes)
- Evaluation: 1-5 documents with manual summaries
- Precision-based scoring (1-5 scale)

### Phase 7: POC Viewer UI
- Vue.js 3 frontend (not React)
- Desktop-only responsive design
- Side-by-side document viewer
- Document-level feedback only (nice to have)
- No download/print/annotations

### Phase 8: Data Contracts
- Cosmos DB data models (JSON schemas)
- Schema versioning with coexistence
- Prompt versioning (semantic versioning, Git-tracked)
- No API versioning for POC

### Phase 9: Monitoring & Observability
- Simplified monitoring (basic Azure Monitor)
- No real-time drift detection
- Alert threshold: 50% accuracy drop (no recipients)
- DEBUG logging everywhere
- No automated performance testing

### Phase 10: Evaluation & Demo
- Reduced evaluation scope (1-5 documents)
- Success criteria updated (no classification metrics)
- Demo: 30-min stakeholder presentation

### Phase 11: Polish (Optional)
- Retained as-is (code quality, security review)

---

## Task Count Impact

| Phase | Original Tasks | Updated Tasks | Change |
|-------|----------------|---------------|--------|
| Phase 1: Setup | 30 | 27 | -3 (removed ML workspace, Key Vault, training data tasks) |
| Phase 2: Foundational | 27 | 24 | -3 (removed auth, SQL models, complex retry) |
| Phase 3: Ingestion/OCR | 24 | 24 | 0 (updated for bilingual, Layout API) |
| Phase 4: Classification | 30 | **0** | **-30 (ENTIRE PHASE REMOVED)** |
| Phase 5: Extraction | 35 | 30 | -5 (no training, simplified validation) |
| Phase 6: Summarization | 33 | 30 | -3 (reduced evaluation scope) |
| Phase 7: UI | 38 | 35 | -3 (simplified viewer, no auth UI) |
| Phase 8: Contracts | 27 | 24 | -3 (Cosmos DB, no SQL migrations) |
| Phase 9: Monitoring | 20 | 12 | -8 (removed drift detection, performance testing) |
| Phase 10: Evaluation | 28 | 25 | -3 (reduced test set) |
| Phase 11: Polish | 11 | 11 | 0 |
| **TOTAL** | **294** | **~220** | **-74 tasks (~25% reduction)** |

---

## Open Questions: All Resolved

All 8 original open questions (Q-001 to Q-008) plus 30 additional underspecified areas identified in gap analysis have been resolved:

### Critical Questions (Week 1)
✅ Q-001: Form types → **HNW CMB APP 2 (single form)**  
✅ Q-002: Fields → **7 fields defined**  
✅ Q-006: Database → **Cosmos DB**  
✅ Q-007: Azure AI DI → **Provisioned**  
✅ Q-008: Azure OpenAI → **GPT-4o, 120 TPM**  

### High Priority (Week 1-2)
✅ Q-003: Evaluation criteria → **Precision 1-5 scale**  
✅ Q-004: Summary of summaries → **Not in POC**  
✅ Q-005: Feedback → **Nice to have, document-level**  
✅ Frontend framework → **Vue.js 3**  
✅ Backend framework → **FastAPI**  
✅ OCR model → **Layout API for all**  
✅ Authentication → **None for POC**  

### Medium Priority (Week 2-4)
✅ Error handling → **Simplified**  
✅ Monitoring → **Basic only**  
✅ Performance testing → **Manual validation**  
✅ Data retention → **2 weeks**  
✅ Multi-language → **English + Simplified Chinese**  
✅ Concurrency → **10 documents**  
✅ Cost budget → **No constraints**  
✅ Logging → **DEBUG everywhere**  
✅ Backup/recovery → **Not required**  
✅ Rate limiting → **Not required**  
✅ ...and 18 more medium-priority items

---

## Implementation Impact

### Faster POC Delivery
- **25% fewer tasks** (74 tasks removed)
- **No training data collection** (weeks saved)
- **No classification model development** (simplified architecture)
- **No authentication implementation** (immediate API access)
- **Simplified monitoring** (basic dashboards only)

### Focused Scope
- **Single form type** enables deep validation of extraction quality
- **7 well-defined fields** with concrete acceptance criteria
- **Bilingual support** demonstrates production readiness for Asian markets
- **Concurrent processing** validates scalability approach

### Production Path Clearer
- **Cosmos DB** establishes NoSQL pattern for future form types
- **Schema versioning** supports backward compatibility
- **Zero-shot LLM** enables rapid onboarding of new form types without retraining
- **Page-level citations** proven before investing in bounding-box precision

---

## Next Steps

1. **Week 1 (Dec 11-15):**
   - ✅ Feature spec updated (v1.1)
   - ✅ Tasks updated with scope changes
   - ✅ Open questions resolved
   - 🔄 Begin Phase 1 implementation (Azure provisioning, schema creation)

2. **Week 2 (Dec 16-22):**
   - Implement Cosmos DB collections
   - Create FastAPI backend skeleton
   - Initialize Vue.js frontend
   - Draft bilingual extraction prompts

3. **Week 3-4:**
   - Implement OCR pipeline (Layout API, preprocessing)
   - Build extraction service (7 fields, GPT-4o zero-shot)
   - Develop summarization with page-level citations

4. **Week 12:**
   - Stakeholder demo
   - Funding decision for production

---

**Document Version:** 1.0  
**Created:** 2025-12-11  
**Next Review:** Weekly during implementation
