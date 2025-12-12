<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# HNW Underwriting Automation POC - Product Requirements Document (PRD)
Version 1.0 | Status Draft | Owner TBD | Team HSBC Underwriting | Target POC Phase | Lifecycle Pilot

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 95% | Need owner details | 2025-12-11 |
| Problem & Users | 90% | Need persona validation | 2025-12-11 |
| Scope | 95% | Minor refinements | 2025-12-11 |
| Requirements | 85% | Need validation rules | 2025-12-11 |
| Metrics & Risks | 80% | Need baseline data | 2025-12-11 |
| Operationalization | 70% | Need deployment plan | 2025-12-11 |
| Finalization | 50% | Need stakeholder review | 2025-12-11 |
Unresolved Critical Questions: 6 | TBDs: 8

## 1. Executive Summary
### Context
This POC establishes the foundational capabilities for HSBC's HNW Insurance Underwriting Automation platform, focusing on document classification, field extraction, and summarization. The pilot targets 2 English-language application forms with 5-6 key fields per document, validating the technical approach before broader rollout.

### Core Opportunity
Prove the viability of AI-powered document processing for insurance underwriting by demonstrating accurate classification, extraction, and summarization on a constrained dataset. Success validates the approach for scaling to 40-50 document types in production.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Achieve classification correctness | Quality | Manual classification | >95% precision/recall | POC | P0 |
| G-002 | Validate extraction completeness and coverage | Quality | Manual extraction | >90% completeness | POC | P0 |
| G-003 | Demonstrate summary quality with citations | Quality | Manual summaries | Benchmark vs manual | POC | P0 |
| G-004 | Establish ingestion and preprocessing pipeline | Technical | No pipeline | Functional pipeline | POC | P0 |
| G-005 | Validate OCR quality for English documents | Technical | N/A | >98% character accuracy | POC | P1 |
| G-006 | Create reusable schema and config contracts | Architecture | N/A | Documented patterns | POC | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| O-001 | Prove technical feasibility | All P0 goals achieved with evaluation data | P0 | TBD |
| O-002 | Establish architecture patterns | Scalable design validated for production | P0 | TBD |
| O-003 | Define data contracts and schemas | JSON schemas versioned and documented | P1 | TBD |

## 2. Problem Definition
### Current Situation
HSBC underwriters manually review insurance application forms, extracting key information and creating summaries for underwriting decisions. This POC focuses on:
* **Document Types**: 2 English-language application forms
* **Extraction Fields**: 5-6 key fields per document type (e.g., applicant name, policy amount, coverage dates, medical conditions, beneficiaries)
* **Current Process**: Manual reading, data entry, and memo creation
* **Pain Points**: Time-consuming, error-prone, inconsistent quality

### Problem Statement
Before investing in full-scale automation for 40-50 document types, HSBC needs validated proof that AI can accurately classify documents, extract structured fields, and generate quality summaries with proper citations.

### Root Causes
* No automated document processing infrastructure
* Lack of validated OCR and extraction approaches
* Uncertainty about AI accuracy for underwriting documents
* Need for reusable patterns and contracts

### Impact of Inaction
* Inability to secure investment for full platform
* Continued manual inefficiencies
* Risk of pursuing unproven technical approach

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Insurance Underwriter | Validate AI outputs match manual work; Test UI and workflows | Concerned about accuracy and usability | Primary validator - provides feedback |
| Technical Lead | Prove architecture scalability; Establish patterns | Need evidence of technical feasibility | Key decision-maker for production |
| Data Scientist | Evaluate model performance; Tune models | Need quality training data and metrics | Model optimization owner |
| Product Owner | Demonstrate ROI potential; Secure funding | Need measurable success metrics | Business case owner |

## 4. Scope
### In Scope
* **Document Types**
  * 2 English-language application forms (specific forms TBD)
  * Per-document classification (not multi-document taxonomy initially)
* **Ingestion & Preprocessing**
  * Ingestion API or event-triggered pipeline
  * Raw document storage with metadata (Azure Blob Storage)
  * OCR using Azure AI Document Intelligence (formerly Form Recognizer)
  * Optional preprocessing: denoise, rotate, deskew (TBD)
  * Layout extraction: text blocks, lines, tables (Azure AI Document Intelligence)
  * Text normalization: line breaks, cleanup
* **Document Classification**
  * Binary classification (Form A vs Form B vs Unknown)
  * Confusion matrix evaluation
  * Baseline model experiments
* **Field Extraction**
  * 5-6 fields per document type (specific fields TBD)
  * Rule-based extraction for structured forms
  * LLM-based extraction where needed
  * Required/optional field schema
  * Validation rules per field
  * Post-processing: normalize dates, currencies, addresses
  * Cross-field consistency checks
* **Summarization**
  * Document-level summaries with citations to source text
  * Extractive summary: key facts with linked spans
  * Abstractive summary: generated text with citations
  * Summary of summaries (if multiple documents provided - TBC)
  * Evaluation by SME (Anish to provide criteria)
* **UI/Workflows**
  * Summary viewer with citations
  * Extracted fields display
  * Document viewer (source text)
  * Summary of summaries view (TBC)
  * Feedback mechanism (TBD)
* **Non-Functional Requirements**
  * Configuration contracts: structured schema, prompt library
  * Data contracts: canonical JSON schemas with versioning
  * Storage: database for structured outputs, audit logging
  * Model registry
* **Monitoring & Observability**
  * OCR quality metrics (optional)
  * Classification distribution drift detection
  * Extraction confidence shifts
  * Trace IDs across components

### Out of Scope (POC Phase)
* **Full document taxonomy** (40-50 types deferred to production)
* **Multi-language support** (Chinese deferred)
* **Fraud detection** (deferred to production)
* **Full case management system** (minimal workflow only)
* **Integration with legacy systems** (POC is standalone)
* **Production-grade security** (development security only)
* **Advanced HITL workflows** (basic feedback only)
* **Real-time processing** (batch processing acceptable)
* **Multi-document scenarios** (single document focus, summary of summaries TBC)

### Assumptions
* 2 application forms are representative of broader document set
* Ground truth data available for training and evaluation
* SME availability for evaluation and feedback
* Development environment accessible (Azure)
* Azure AI Document Intelligence available for OCR
* Azure OpenAI Service accessible for LLM capabilities

### Constraints
* **Timeline**: POC duration TBD (estimate 8-12 weeks)
* **Budget**: POC budget TBD
* **Resources**: Small team (2-3 engineers, 1 data scientist, 1 SME)
* **Data**: Limited to 2 document types for POC
* **Infrastructure**: Azure development environment only (internal HSBC Azure subscription)

## 5. Product Overview
### Value Proposition
A proof-of-concept demonstrating that AI can accurately classify insurance application forms, extract structured data fields, and generate quality summaries with citations—validating the technical and business case for full-scale underwriting automation.

**Key Benefits:**
* **Risk Reduction**: Validates approach before major investment
* **Technical Proof**: Demonstrates OCR, extraction, and summarization accuracy
* **Architecture Validation**: Establishes scalable patterns and contracts
* **Stakeholder Confidence**: Provides measurable evidence for funding decisions

### Differentiators (Optional)
* Citation-backed summaries ensuring traceability
* Reusable schema and configuration patterns
* Modular architecture for easy scaling
* Multiple OCR engine evaluation

### UX / UI (Conditional)
**Primary Interface**: Web-based POC viewer

**Key UX Considerations:**
* **Simplicity**: Minimal UI focused on validation tasks
* **Citations**: Clear links from summaries to source text
* **Field Display**: Clean presentation of extracted fields with confidence scores
* **Feedback**: Simple mechanism to mark correct/incorrect outputs

UX Status: Basic UI for POC validation

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Ingestion API | Accept document uploads (PDF, image formats) via API | G-004 | Engineer | P0 | API accepts files, returns ingestion ID | REST or event-driven |
| FR-002 | Raw Document Storage | Store uploaded documents with metadata (timestamp, source, type) | G-004 | Engineer | P0 | Documents stored securely with metadata | Azure Blob Storage |
| FR-003 | OCR Implementation | Implement OCR using Azure AI Document Intelligence (formerly Form Recognizer) | G-005 | Data Scientist | P0 | OCR accuracy measured and documented | Azure AI Document Intelligence |
| FR-004 | OCR Preprocessing | Optional preprocessing: denoise, rotate, deskew (TBD based on data quality) | G-005 | Engineer | P2 | Preprocessing improves OCR accuracy (if needed) | Conditional |
| FR-005 | Layout Extraction | Extract layout elements: text blocks, lines, tables | G-004 | Engineer | P1 | Layout extracted and stored | Azure AI Document Intelligence layout analysis |
| FR-006 | Text Normalization | Normalize text: remove artifacts, fix line breaks, standardize whitespace | G-004 | Engineer | P1 | Clean text improves extraction accuracy | Post-OCR cleanup |
| FR-007 | Document Classification | Classify documents into 2 form types (Form A, Form B, Unknown) | G-001 | Data Scientist | P0 | >95% precision/recall on test set | Confusion matrix |
| FR-008 | Classification Implementation | Implement classification using Azure OpenAI or Azure ML | G-001 | Data Scientist | P0 | Best approach identified and documented | Azure-based classification |
| FR-009 | Field Schema Definition | Define 5-6 required/optional fields per document type | G-002 | Product Owner | P0 | Schema documented and versioned | JSON schema |
| FR-010 | Field Validation Rules | Define validation rules per field (format, range, required/optional) | G-002 | Product Owner | P1 | Validation rules documented | Part of schema |
| FR-011 | Rule-Based Extraction | Extract fields using rule-based methods for structured forms | G-002 | Engineer | P0 | Fields extracted with >90% accuracy for structured content | Templates, regex |
| FR-012 | LLM-Based Extraction | Extract fields using Azure OpenAI for unstructured or complex content | G-002 | Data Scientist | P0 | Fields extracted with >90% accuracy | Azure OpenAI prompt engineering |
| FR-013 | Field Post-Processing | Normalize extracted fields (dates, currencies, addresses) | G-002 | Engineer | P1 | Normalized fields follow standard formats | Data cleaning |
| FR-014 | Cross-Field Validation | Validate consistency across fields (e.g., dates, totals) | G-002 | Engineer | P2 | Inconsistencies flagged | Business logic |
| FR-015 | Extractive Summarization | Generate extractive summary highlighting key facts with source spans | G-003 | Data Scientist | P0 | Summaries contain key facts with citations | Span-based |
| FR-016 | Abstractive Summarization | Generate abstractive summary with citations to source text using Azure OpenAI | G-003 | Data Scientist | P0 | Summaries readable and accurate with citations | Azure OpenAI GPT-4 |
| FR-017 | Summary of Summaries | Combine summaries from multiple documents (TBC if multiple docs provided) | G-003 | Data Scientist | P2 | Coherent multi-document summary | Conditional |
| FR-018 | Summary Evaluation | Evaluate summary quality against SME criteria (Anish to provide) | G-003 | SME | P0 | Summaries meet quality benchmarks | Manual evaluation |
| FR-019 | UI - Summary Viewer | Display summaries with clickable citations to source text | G-003 | Engineer | P0 | Users can view summaries and navigate to source | Web UI |
| FR-020 | UI - Field Viewer | Display extracted fields with confidence scores | G-002 | Engineer | P0 | Users can review extracted fields | Web UI |
| FR-021 | UI - Document Viewer | Display source document with highlighting | G-003 | Engineer | P0 | Users can view original document | Web UI |
| FR-022 | UI - Feedback Mechanism | Allow users to mark outputs as correct/incorrect (TBD implementation) | TBD | Engineer | P2 | Feedback captured for analysis | Simple tagging |
| FR-023 | Configuration Contracts | Define structured configuration schema and prompt library | G-006 | Engineer | P1 | Configs versioned and documented | Reusability |
| FR-024 | Data Contracts | Define canonical JSON schemas for outputs with versioning | G-006 | Engineer | P1 | Schemas versioned and validated | API contracts |
| FR-025 | Structured Storage | Store extracted fields and summaries in database | G-006 | Engineer | P0 | Outputs queryable and retrievable | Azure SQL or Cosmos DB |
| FR-026 | Audit Logging | Log all processing steps with timestamps and trace IDs | G-004 | Engineer | P1 | Audit trail available for debugging | Observability |
| FR-027 | Model Registry | Track model versions and configurations using Azure ML Model Registry | G-006 | Data Scientist | P1 | Models versioned and retrievable | Azure ML MLOps |

### Feature Hierarchy
```plain
HNW Underwriting POC
├── Ingestion & Preprocessing
│   ├── Ingestion API (FR-001)
│   ├── Raw Storage - Azure Blob (FR-002)
│   ├── OCR - Azure AI Document Intelligence (FR-003)
│   ├── OCR Preprocessing (FR-004)
│   ├── Layout Extraction - Azure AI (FR-005)
│   └── Text Normalization (FR-006)
├── Document Classification
│   ├── Classification Model (FR-007)
│   └── Azure OpenAI/ML Implementation (FR-008)
├── Field Extraction
│   ├── Schema Definition (FR-009)
│   ├── Validation Rules (FR-010)
│   ├── Rule-Based Extraction (FR-011)
│   ├── Azure OpenAI Extraction (FR-012)
│   ├── Post-Processing (FR-013)
│   └── Cross-Field Validation (FR-014)
├── Summarization
│   ├── Extractive Summary (FR-015)
│   ├── Abstractive Summary - Azure OpenAI (FR-016)
│   ├── Summary of Summaries (FR-017)
│   └── Evaluation (FR-018)
├── UI & Workflows
│   ├── Summary Viewer (FR-019)
│   ├── Field Viewer (FR-020)
│   ├── Document Viewer (FR-021)
│   └── Feedback (FR-022)
├── Infrastructure
│   ├── Config Contracts (FR-023)
│   ├── Data Contracts (FR-024)
│   ├── Storage - Azure SQL/Cosmos (FR-025)
│   ├── Audit Logging (FR-026)
│   └── Model Registry - Azure ML (FR-027)
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Document processing latency | <5 minutes per document (POC acceptable) | P1 | Benchmark testing | Not production SLA |
| NFR-002 | Performance | OCR processing speed | <1 minute per 10-page document | P1 | Performance testing | Depends on engine |
| NFR-003 | Reliability | System availability | 95% uptime during POC testing | P2 | Monitoring | Development environment |
| NFR-004 | Reliability | Data durability | No data loss during POC | P0 | Backup validation | Basic backup |
| NFR-005 | Scalability | Concurrent documents | Handle 5 concurrent documents | P2 | Load testing | POC baseline |
| NFR-006 | Security | Data encryption at rest | Encrypted storage | P1 | Security review | Development security |
| NFR-007 | Security | Data encryption in transit | HTTPS/TLS | P1 | Security review | Standard protocol |
| NFR-008 | Security | Access control | Basic authentication | P1 | Security testing | POC-level security |
| NFR-009 | Observability | Logging | Structured logs with trace IDs | P0 | Log validation | All components |
| NFR-010 | Observability | Monitoring | Basic monitoring dashboards | P1 | Dashboard validation | OCR quality, extraction confidence |
| NFR-011 | Observability | Drift detection | Classification distribution tracking | P1 | Monitoring validation | Baseline for production |
| NFR-012 | Maintainability | Code quality | Basic code reviews and testing | P1 | Code review | Standard practices |
| NFR-013 | Maintainability | Documentation | Technical documentation for all components | P0 | Doc review | Architecture, APIs, configs |

## 8. Data & Analytics
### Inputs
* **Documents**: 2 English-language application forms (PDF or images)
* **Training Data**: Labeled examples for classification and extraction
* **Evaluation Data**: Ground truth for accuracy measurement
* **Configuration**: Schema definitions, validation rules, prompt templates

### Outputs / Events
* **Classified Documents**: Document type, confidence score
* **Extracted Fields**: Structured JSON with field values and confidence
* **Summaries**: Extractive and abstractive summaries with citations
* **Audit Logs**: Processing steps, timestamps, trace IDs
* **Performance Metrics**: Accuracy, latency, error rates

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Classification precision | Quality | Manual (100%) | >95% | POC | Evaluation set |
| Classification recall | Quality | Manual (100%) | >95% | POC | Evaluation set |
| Extraction completeness | Quality | Manual (100%) | >90% | POC | Evaluation set |
| Extraction correctness | Quality | Manual (100%) | >90% | POC | Evaluation set |
| Summary quality vs manual | Quality | Manual (100%) | Benchmark comparable | POC | SME evaluation |
| OCR character accuracy | Quality | N/A | >98% for typed text | POC | OCR testing |
| Processing time per document | Performance | N/A | <5 minutes | POC | System logs |
| Drift detection baseline | Observability | N/A | Established | POC | Monitoring |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Azure AI Document Intelligence | Technical | High | Engineering | Service availability and accuracy | Provision early, test with sample docs |
| Azure OpenAI Service | Technical | High | Engineering | API quota and access | Secure access early, request quota increase if needed |
| Training Data | Data | High | Data Team | Insufficient labeled data | Prioritize data collection |
| Ground Truth Evaluation Data | Data | High | SME | No validation dataset | Create evaluation set early |
| SME Availability | Business | High | Product Owner | SME time constraints | Schedule dedicated time |
| Development Infrastructure | Infrastructure | Medium | IT | Environment delays | Provision early |
| Document Samples | Business | High | Business | Sample documents not provided | Secure samples in week 1 |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | 2 document types insufficient to prove scalability | High | Medium | Choose representative forms, document generalization patterns | Product Owner | Open |
| R-002 | Azure AI Document Intelligence quality insufficient for forms | High | Medium | Test with sample forms early, implement preprocessing if needed | Engineering | Open |
| R-003 | Insufficient training data | High | High | Prioritize data collection, use few-shot learning | Data Team | Open |
| R-004 | Azure OpenAI extraction accuracy below target | Medium | Medium | Prompt engineering, hybrid rule-based approach, try different GPT models | Data Scientist | Open |
| R-005 | Summary evaluation criteria unclear | Medium | High | Define criteria with SME early (Anish) | Product Owner | Open |
| R-006 | Scope creep beyond POC goals | Medium | Medium | Strict scope management, defer non-P0 items | Product Owner | Open |
| R-007 | Infrastructure delays | Medium | Low | Provision early, have fallback options | Engineering | Open |
| R-008 | SME availability limited | Medium | Medium | Schedule dedicated time, batch review sessions | Product Owner | Open |

## 11. Privacy, Security & Compliance
### Data Classification
* **Sensitive (POC Level)**: 
  * Application form data (names, policy amounts, medical info)
  * Test data with anonymized or synthetic PII acceptable for POC

### PII Handling
* **POC Approach**: Use anonymized or synthetic data where possible
* **Encryption**: Basic encryption at rest and in transit
* **Access Control**: Development team only
* **Retention**: Data retained for POC duration, deleted post-evaluation (unless needed for production)

### Threat Considerations
* **POC Security**: Development-level security acceptable
* **Data Exposure**: Limit access to development team
* **Production Planning**: Full security requirements deferred to production phase

### Regulatory / Compliance
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| GDPR/CCPA | If using real data | Use anonymized data for POC | Legal | TBD |
| Internal Security | Development environment | Follow HSBC dev security policies | Engineering | TBD |

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Azure development environment; Manual deployment acceptable | Internal HSBC Azure subscription |
| Rollback | Manual rollback for POC | Version control for configs and models |
| Monitoring | Basic dashboards: OCR quality, classification accuracy, extraction confidence | Development monitoring |
| Alerting | Email alerts for failures | Simple alerting |
| Support | Engineering team support during POC | No 24/7 support |
| Capacity Planning | Single-user or small team testing | Minimal load |
| Backup & Recovery | Daily backups of outputs and configs | Basic backup |
| Model Management | Basic model versioning in registry | Foundation for MLOps |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Phase 1: Setup & Data Prep | Week 1-2 | Infrastructure ready, sample documents collected, schemas defined | Engineering/Product |
| Phase 2: OCR & Classification | Week 3-4 | OCR engine selected, classification model trained and tested | Data Scientist |
| Phase 3: Extraction & Validation | Week 5-6 | Field extraction working, validation rules implemented | Engineering |
| Phase 4: Summarization | Week 7-8 | Summaries generated with citations, evaluation criteria defined | Data Scientist |
| Phase 5: UI & Integration | Week 9-10 | UI functional, end-to-end workflow tested | Engineering |
| Phase 6: Evaluation & Demo | Week 11-12 | SME evaluation complete, stakeholder demo conducted | Product Owner |

### Success Criteria
* All P0 goals achieved (>95% classification, >90% extraction, quality summaries)
* Architecture patterns documented for scaling
* Data contracts and schemas established
* Stakeholder approval to proceed to production

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| Q-001 | Which 2 specific application forms will be used? | Product Owner | Week 1 | Open |
| Q-002 | What are the 5-6 fields per document type? | Product Owner / SME | Week 1 | Open |
| Q-003 | What are the summary evaluation criteria? (Anish to provide) | SME (Anish) | Week 2 | Open |
| Q-004 | Is summary of summaries in scope for POC? | Product Owner | Week 1 | Open |
| Q-005 | What feedback mechanism is needed for POC? | Product Owner | Week 3 | Open |
| Q-006 | What is the POC timeline and budget? | Executive Sponsor | ASAP | Open |
| Q-007 | Is Azure AI Document Intelligence provisioned and accessible? | Engineering | Week 1 | Open |
| Q-008 | Is Azure OpenAI Service provisioned with sufficient quota? | Engineering / Security | Week 1 | Open |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2025-12-11 | AI Assistant | Initial POC PRD created from Marp presentation | Initial Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Presentation | marp.md | POC scope: 2 forms, 5-6 fields, classification, extraction, summarization | Source document |
| REF-002 | PRD | Original PRD (converted to Word) | Full-scale vision for 40-50 document types | POC is subset |

### Citation Usage
POC scope derived from REF-001 (Marp presentation). This is a focused pilot to validate the approach before scaling to full production requirements.

## 17. Appendices
### Glossary
| Term | Definition |
|------|-----------|
| POC | Proof of Concept - limited pilot to validate approach |
| OCR | Optical Character Recognition - extracting text from images |
| Extractive Summary | Summary created by selecting key sentences from source |
| Abstractive Summary | Summary created by generating new text that captures meaning |
| Citation | Reference to source text (document + location) |
| Trace ID | Unique identifier for tracking requests across components |
| Drift Detection | Monitoring for changes in data distribution over time |
| Model Registry | System for versioning and managing ML models |
| Confusion Matrix | Table showing classification accuracy (true/false positives/negatives) |

### TBD Items
1. Specific application form types (Q-001)
2. Exact field schema per document (Q-002)
3. Summary evaluation criteria from Anish (Q-003)
4. Summary of summaries scope decision (Q-004)
5. Feedback mechanism implementation (Q-005)
6. POC timeline and budget (Q-006)
7. Azure AI Document Intelligence preprocessing requirements (depends on data quality)
8. Classification taxonomy structure (starting with per-document)
9. Azure OpenAI model selection (GPT-4, GPT-4 Turbo, etc.)
10. Azure subscription and resource provisioning

Generated 2025-12-11 by GitHub Copilot (mode: hve.prd-builder)
<!-- markdown-table-prettify-ignore-end -->
