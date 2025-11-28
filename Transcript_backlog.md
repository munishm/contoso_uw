# Underwriting Assessment Backlog

## Epic 1: Automated Insurance Underwriting Assessment

**Description:**
Automate preparation of insurance underwriting assessments (currently 2–3 hours manually) to reduce cycle time and improve consistency vs. manual sampling audits. Generates summary + recommended assessment from heterogeneous document sets.
**Priority:** 1

### User Story 1.1: Generate Underwriting Assessment Summary

**As a** Insurance Underwriter **I want to** receive an auto‑generated underwriting summary from uploaded case documents **so that** I can review and approve decisions faster.

**Acceptance Criteria:**

- [ ] When I upload a full case document set the system produces a structured summary (sections: Applicant Profile, Risk Factors, Supporting Evidence, Recommendation)
- [ ] Summary is generated within 5 minutes for an average case (< 50 pages total)
- [ ] Summary cites source document IDs / page references for each key data point
- [ ] If required documents are missing a “Data Gaps” section is appended
- [ ] Audit log entry stored with generation timestamp & model version

**Story Points:** 8  
**Status:** Ready

### User Story 1.2: Consistency Validation Checklist

**As a** Product Owner **I want to** ensure each generated assessment includes a standardized validation checklist **so that** quality and compliance reviews are consistent.

**Acceptance Criteria:**

- [ ] Checklist covers: Identity Match, Document Completeness, Currency, Language Coverage, High‑Risk Indicators
- [ ] Each checklist item is auto-evaluated (Pass / Attention / Fail)
- [ ] Fail or Attention items appear in a “Review Required” section
- [ ] Stored with summary payload in persistence layer
- [ ] Exportable as JSON for downstream analytics

**Story Points:** 5  
**Status:** Ready

### User Story 1.3: Multi-Case Batch Processing Queue

**As a** Operations Coordinator **I want to** submit multiple underwriting cases for batch processing **so that** overnight throughput is maximized.

**Acceptance Criteria:**

- [ ] Can enqueue 25+ cases via API or UI upload bundle
- [ ] Queue exposes per-case status: Pending / Processing / Complete / Error
- [ ] Retries on transient failures (≥ 2 attempts) with exponential backoff
- [ ] Metrics exported: average processing time, success rate, error categories
- [ ] Processing stops gracefully if fraud signal is detected (see Epic 5)

**Story Points:** 8  
**Status:** Refinement (Need volume SLA + infra sizing)

### Spike 1.4: Throughput & Latency Benchmark

**Description:** Benchmark end‑to‑end assessment generation pipeline (Document Intelligence + AI Search + GPT orchestration) across representative case sizes.
**Technical Context:** Current manual baseline 2–3 hours. Target automated < 10 minutes. Need cost vs. latency trade‑offs.

**Acceptance Criteria:**

- Benchmark plan covering small / medium / large case archetypes
- Measured latencies per stage with p50 / p95 stats
- Bottleneck analysis & optimization recommendations
- Cost per case estimated for each configuration
- Output stored in /docs/benchmarks/underwriting_assessment.md

**Status:** Ready

---

## Epic 2: Multi-Language & Mixed Script Document Processing

**Description:**
Support English + Traditional Chinese + Simplified Chinese documents (including mixed-language cases & occasional mixed-language pages) to ensure completeness of analysis.
**Priority:** 1

### User Story 2.1: Language Detection & Routing

**As a** System Architect **I want to** auto-detect document language(s) **so that** the correct extraction & prompt templates are applied.

**Acceptance Criteria:**

- [ ] Each document assigned primary language + confidence
- [ ] Mixed-language pages flagged for dual‑pass processing
- [ ] Routing table maps language to tailored summarization prompt variant
- [ ] Detection accuracy ≥ 95% on validation sample
- [ ] Metrics exported: detection distribution, confidence histogram

**Story Points:** 5  
**Status:** Ready

### User Story 2.2: Mixed-Language Aggregation Handling

**As a** Data Scientist **I want to** merge extracted fields across languages **so that** the final summary is de‑duplicated and coherent.

**Acceptance Criteria:**

- [ ] Duplicate semantic fields (e.g., Name in EN / 中文) resolved with precedence rules
- [ ] Fields retain original-language variant where material (e.g., legal names)
- [ ] Conflicting values produce a discrepancy alert with both sources cited
- [ ] Unit tests cover bilingual & trilingual examples
- [ ] Output schema unchanged for downstream consumers

**Story Points:** 8  
**Status:** Refinement (Need final conflict resolution policy)

### Spike 2.3: Prompt Strategy for Code-Switch Pages

**Description:** Evaluate effectiveness of single unified prompt vs. language-segmented prompts for mixed-language paragraphs.
**Technical Context:** Some pages contain English headers with Chinese handwritten annotations.

**Acceptance Criteria:**

- Experiment matrix & evaluation criteria defined
- Quality comparison metrics (factual accuracy, hallucination rate)
- Recommended approach documented
- Updated prompt templates (if split strategy wins)
- Decision logged in ADR (docs/adr/)

**Status:** Ready

---

## Epic 3: Accuracy & Extraction Quality Improvement

**Description:**
Achieve >90% accuracy for generated assessments leveraging Azure Document Intelligence + GPT long context, with focus on handwritten + low quality images.
**Priority:** 1

### User Story 3.1: Citation-Based Fact Validation

**As a** Compliance Analyst **I want to** verify each extracted fact is traceable to source text **so that** audit integrity is maintained.

**Acceptance Criteria:**

- [ ] Every key field includes document ID + page + char span or bounding box ref
- [ ] Mismatch or missing citation flags field for manual review
- [ ] Random 5% sample auto re‑validated nightly
- [ ] Validation report exported (pass %, flagged count)
- [ ] Failing threshold (< 90% pass) triggers alert

**Story Points:** 8  
**Status:** Ready

### User Story 3.2: Handwritten Text Quality Metrics

**As a** Data Scientist **I want to** measure OCR accuracy on handwritten segments **so that** we can prioritize model tuning.

**Acceptance Criteria:**

- [ ] Handwritten regions auto‑tagged via layout analysis
- [ ] Accuracy computed vs. labeled sample set
- [ ] Dashboard: printed vs handwritten accuracy trend
- [ ] Threshold breach (< 85%) surfaces optimization task
- [ ] Supports future custom model insertion

**Story Points:** 5  
**Status:** Refinement (Need labeled sample set)

### Spike 3.3: Long Context Window Utilization Strategy

**Description:** Evaluate performance difference between GPT‑4.1 long context and GPT‑4o 128k for full-case summarization.

**Acceptance Criteria:**

- Test plan & metrics (accuracy, latency, cost) defined
- Comparative run logs archived
- Recommendation & cost delta summary
- Prompt adjustments (if needed) committed
- Report saved: docs/benchmarks/context_window.md

**Status:** Ready

### Spike 3.4: Custom Signature Detection Feasibility

**Description:** Assess feasibility & governance lead time for custom model to improve signature cropping accuracy.

**Acceptance Criteria:**

- Precision/recall baseline from generic layout model
- Target performance thresholds defined
- Model governance steps & estimated timeline documented
- Risk assessment (false negative / false positive impact)
- Go / No‑Go recommendation

**Status:** Ready

---

## Epic 4: Governance, Compliance & Monitoring

**Description:**
Implement auditability, model governance controls, Data Visa compliance, and monitoring across pipeline components.
**Priority:** 2

### User Story 4.1: Data Visa & Redaction Workflow Integration

**As a** Compliance Officer **I want to** ensure production samples with PII are processed only after redaction approval **so that** regulatory obligations are met.

**Acceptance Criteria:**

- [ ] Redaction pipeline validates removal/anonymization of PII entities
- [ ] Approval status stored & versioned
- [ ] Unauthorized sample triggers block + alert
- [ ] Audit report lists sample IDs, approval timestamp, reviewer
- [ ] Access governed via role-based policy

**Story Points:** 8  
**Status:** Refinement (Need final Data Visa SLA)

### User Story 4.2: Model & Prompt Version Auditing

**As a** Platform Engineer **I want to** record model, prompt template hash, and feature flag state per output **so that** later reproducibility is guaranteed.

**Acceptance Criteria:**

- [ ] Metadata envelope persisted with each assessment
- [ ] CLI/Report can reconstruct environment for a given ID
- [ ] Hash mismatch raises investigation task
- [ ] 30‑day retention policy reviewed
- [ ] Documentation in /docs/operations/audit.md

**Story Points:** 5  
**Status:** Ready

### Spike 4.3: Monitoring & Alerting Baseline

**Description:** Define metrics, SLOs, and alert thresholds (latency, accuracy, extraction failures, fraud triggers).

**Acceptance Criteria:**

- Metric inventory drafted
- SLO doc published
- Initial alert rules proposed
- Gap analysis vs. production readiness
- Output saved: docs/operations/monitoring_baseline.md

**Status:** Ready

---

## Epic 5: Fraud & Malicious Document Defense

**Description:**
Detect malicious, adversarial, or jailbreak‑attempt documents early and quarantine processing to protect downstream models.
**Priority:** 2

### User Story 5.1: Malicious Pattern Detection Gate

**As a** Fraud Analyst **I want to** scan documents for exploit or jailbreak signatures **so that** unsafe content is blocked.

**Acceptance Criteria:**

- [ ] Rule set includes known prompt injection & obfuscation patterns
- [ ] High severity detection stops pipeline prior to LLM call
- [ ] Detection event logged with hash & rule ID
- [ ] False positive rate < 5% on validation set
- [ ] Quarantined items accessible for review workflow

**Story Points:** 8  
**Status:** Ready

### User Story 5.2: Document Integrity & Tamper Signals

**As a** Security Engineer **I want to** validate file integrity (hash, structure) **so that** altered or corrupted documents are flagged.

**Acceptance Criteria:**

- [ ] Hash captured on ingest & post‑processing
- [ ] Structural anomaly detection (unexpected mime / truncated data)
- [ ] Integrity failure routes to quarantine
- [ ] Metrics: anomaly count per 1000 docs
- [ ] Incident playbook referenced

**Story Points:** 5  
**Status:** Refinement (Need anomaly threshold definition)

### Spike 5.3: Fraud Agent Design Evaluation

**Description:** Evaluate agentic approach for layered fraud defense (pre‑OCR, post‑OCR, pre‑LLM phases).

**Acceptance Criteria:**

- Threat model drafted
- Proposed agent responsibilities & orchestration diagram
- Cost/performance impact estimate
- Decision logged in ADR
- Next steps backlog items created (if adopted)

**Status:** Ready

---

## Epic 6: Environment & Region Architecture

**Description:**
Stand up regional architecture (HK insurance, UK/Singapore credit) with Azure Document Intelligence, AI Search, Functions, Power Platform UI, GPT 4.1 long context in compliant regions.
**Priority:** 3

### User Story 6.1: Regional Deployment Configuration

**As a** Cloud Architect **I want to** define region-specific deployment parameters **so that** latency and compliance requirements are met.

**Acceptance Criteria:**

- [ ] Parameter file per region (HK, UK, SG)
- [ ] GPT model region + fallback documented
- [ ] Data residency notes included
- [ ] Infra diagram versioned in /docs/architecture
- [ ] Deployment script consumes parameter files

**Story Points:** 5  
**Status:** Ready

### User Story 6.2: Reusable Agentic Components Library

**As a** Platform Engineer **I want to** abstract reusable components (ingest, extraction, summarization, fraud hooks) **so that** claims & credit underwriting can reuse.

**Acceptance Criteria:**

- [ ] Components packaged (internal Python/Function modules)
- [ ] Versioning & changelog started
- [ ] Example integration guide
- [ ] Unit tests for core abstractions
- [ ] Published to internal artifact repository

**Story Points:** 8  
**Status:** Refinement (Need final component boundary definitions)

### Spike 6.3: Cost Optimization Strategy

**Description:** Evaluate cost levers (context window size, batch size, parallelism) across regions.

**Acceptance Criteria:**

- Cost model spreadsheet
- Scenario comparison (baseline vs. optimized)
- Recommendations prioritized
- Implementation tasks created
- Summary stored /docs/cost/optimization.md

**Status:** Ready

---

## Epic 7: Team Onboarding & Collaboration Enablement

**Description:**
Accelerate ISE + HSBC team alignment (onboarding 3–4 weeks) with clear role definitions & early collaboration materials.
**Priority:** 3

### User Story 7.1: Role & Responsibility Matrix

**As a** TPM **I want to** document RACI across roles **so that** handoffs & ownership are unambiguous.

**Acceptance Criteria:**

- [ ] RACI table published
- [ ] Reviewed by ISE + HSBC leads
- [ ] Linked from project README
- [ ] Updated when new roles onboard
- [ ] Version tagged (v1.0)

**Story Points:** 3  
**Status:** Ready

### User Story 7.2: Pre-Onboarding Knowledge Pack

**As a** New Team Member **I want to** access a curated knowledge pack **so that** I can contribute before formal access completes.

**Acceptance Criteria:**

- [ ] Pack includes architecture overview, data flow, glossary, key decisions
- [ ] Accessible without production data access
- [ ] Time-to-first-PR target < 5 days
- [ ] Feedback loop survey after first sprint
- [ ] Stored in /docs/onboarding/

**Story Points:** 5  
**Status:** Refinement (Need final doc structure)

### Spike 7.3: Early Advisory Async Workflow

**Description:** Explore async collaboration tooling to enable ISE advisory before full access (whiteboard exports, synthetic samples).

**Acceptance Criteria:**

- Tooling options compared
- Security constraints validated
- Proposed workflow documented
- Pilot success criteria defined
- Decision recorded in ADR

**Status:** Ready

---

## Summary Metrics & Next Steps

Initial focus: Epics 1–3 (core value + accuracy) then governance & security (Epics 4–5). Parallelize onboarding enablement (Epic 7) to reduce ramp time.

Backlog generated from transcript: `Transcript.docx` (treated as plain text). Items marked Refinement require additional policy, data samples, or threshold decisions.

---

**Generated:** 2025-11-06  
**Generator:** Automated backlog derivation based on provided transcript content.
