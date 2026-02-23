---
title: Evaluation Strategy — Ground Truth Acquisition & Metric-driven Quality Assurance
description: Strategy paper defining how Contoso acquires ground truth through Underwriter/BA collaboration, applies an existing evaluation framework at every integration point, and enables Data Science to measure extraction, classification, and summarization quality
author: Contoso IWPB UW Team
ms.date: 2026-02-17
ms.topic: concept
keywords:
  - evaluation strategy
  - ground truth
  - underwriting
  - RACI
  - entity extraction
  - classification
  - summarization
estimated_reading_time: 15
---

# Evaluation Strategy — Ground Truth Acquisition & Metric-driven Quality Assurance

## Executive Summary

Contoso's Intelligent Underwriting platform automates three core AI capabilities — **Entity Extraction**, **Document Classification**, and **Document Summarization** — as part of the underwriting workflow. To measure and continuously improve the quality of these capabilities we need **ground truth data** that represents the business-correct answer for a curated set of documents.

Today, Contoso does not perform component-level evaluation and does not have a ground truth dataset. This paper defines how we close that gap by:

1. Engaging **Underwriters (UWs)** and **Business Analysts (BAs)** to produce labelled ground truth in a standardised CSV format.
2. Handing that ground truth to **Developers (Dev)** and **Data Scientists (DS)** who define and compute evaluation metrics.
3. Plugging the evaluation into the **existing evaluation framework** (`src/evaluation/`) at every integration point so quality is measured automatically and continuously.

The paper includes a RACI matrix, phased delivery plan, stakeholder engagement stages, and a risk-and-mitigation register.

## Context — Existing Evaluation Framework

We already have a functional evaluation framework in the codebase. The strategy in this document does **not** propose building a new framework. Instead it focuses on **feeding the framework with ground truth** and **activating it at every integration point**.

### What already exists

| Capability | Framework Location | Evaluators Available |
| :--- | :--- | :--- |
| Entity Extraction | `src/evaluation/entity_extraction/` | `ExtractionCorrectnessEvaluator` (token-level), `ExtractionCompletenessEvaluator` (LLM-based) |
| Summarization | `src/evaluation/document_summarization/` | `EntityCoverageEvaluator`, `GroundednessEvaluator`, `SemanticFidelityEvaluator` |
| Classification | *Not yet implemented* | Planned: Precision, Recall, F1, Confusion Matrix |

### What is missing

* **Ground truth datasets** — no labelled data exists for any capability.
* **Classification evaluator** — the extraction and summarization evaluators exist but classification evaluation has no code yet.
* **Automated pipeline trigger** — evaluation runs inline today; it is not triggered in CI/CD or on ground truth refresh.

This paper addresses all three gaps.

## Stakeholder Roles

| Abbreviation | Role | Responsibility |
| :--- | :--- | :--- |
| **UW** | Underwriter (SME) | Provides authoritative field-level answers; adjudicates disputes |
| **BA** | Business Analyst | Designs the labelling template; coordinates UW sessions; ensures data quality |
| **DS** | Data Scientist | Defines metrics; runs evaluations; reports scores; identifies model improvements |
| **Dev** | Developer / Engineer | Builds ingestion scripts; integrates evaluation framework; maintains CI/CD hooks |
| **PM** | Product Manager | Prioritises evaluation work; governs cadence and release decisions |
| **QA** | Quality Assurance | Validates CSV integrity; performs sanity checks on evaluation reports |

## RACI Matrix

Each row is a key activity. Columns show the responsible (R), accountable (A), consulted (C), and informed (I) parties.

| Activity | UW | BA | DS | Dev | PM | QA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Define Golden Set document selection criteria | C | R | C | I | A | I |
| Select and curate Golden Set documents | C | R | I | I | A | I |
| Design CSV labelling template | I | R | C | C | I | I |
| Label ground truth — Entity Extraction | R | A | I | I | I | C |
| Label ground truth — Classification | R | A | I | I | I | C |
| Label ground truth — Summarization | R | A | C | I | I | C |
| Review and adjudicate labelling disputes | R | A | C | I | I | I |
| Approve final ground truth CSV release | C | R | I | I | A | C |
| Build CSV ingestion and normalisation scripts | I | C | C | R | I | A |
| Define evaluation metrics per capability | I | C | R | C | I | I |
| Implement classification evaluator | I | I | R | R | I | C |
| Integrate evaluation at pipeline integration points | I | I | C | R | I | A |
| Run evaluation and produce scorecards | I | I | R | C | I | I |
| Analyse discrepancies and recommend actions | C | C | R | C | A | I |
| Update ground truth based on feedback | R | A | C | I | I | C |
| Govern evaluation cadence and release decisions | I | C | I | I | R | I |

## Phased Delivery Plan

### Phase 1 — Golden Set & Template Design (Weeks 1–2)

**Goal:** Agree on what documents to evaluate and how UWs will label them.

**Activities:**

* BA selects 50–100 representative documents spanning simple, complex, and edge-case scenarios across all document types the system handles.
* BA designs a CSV labelling template per capability (see [Ground Truth CSV Templates](#ground-truth-csv-templates) below).
* DS reviews the template to confirm it captures enough information to compute the planned metrics.
* PM approves the Golden Set scope.

**Exit criteria:**

* Golden Set document list finalised and stored in a versioned location.
* CSV templates reviewed and signed off by DS and BA.

### Phase 2 — Ground Truth Labelling (Weeks 3–6)

**Goal:** UWs populate the CSV with business-correct values.

**Activities:**

* BA conducts labelling workshops with UWs (recommended: 2–3 sessions per week, 90 minutes each).
* For **Entity Extraction**: UWs open each document, locate each field, and type the correct value into the CSV.
* For **Classification**: UWs assign the correct document type label to each file.
* For **Summarization**: UWs write or approve a reference summary and flag which key entities must appear.
* BA performs a first-pass quality check after each session.
* Disputes or ambiguous cases are logged and escalated to a senior UW for adjudication.

**Labelling guidelines for UWs:**

* Type the value as it should be understood by the business — do not worry about formatting. DS handles normalisation.
* If a field is genuinely not present in the document, enter `NOT_FOUND`.
* If multiple valid interpretations exist, enter the primary value and note the alternative in the `Notes` column.

**Exit criteria:**

* All Golden Set documents labelled for all three capabilities.
* Adjudication log closed — no open disputes.
* BA-approved CSV committed to the repository under `data/ground_truth/v1/`.

### Phase 3 — Metric Definition & Framework Activation (Weeks 5–8)

> This phase overlaps with Phase 2 so DS can start while labelling is still in progress.

**Goal:** DS defines the evaluation metrics and Dev wires them into the existing framework at every integration point.

**Activities:**

* DS defines metrics per capability (see [Evaluation Metrics by Capability](#evaluation-metrics-by-capability)).
* Dev builds normalisation scripts to align UW-provided values with model output formats.
* Dev implements the classification evaluator in `src/evaluation/document_classification/`.
* Dev configures the existing `EvaluationService` and `SummaryEvaluationService` to load ground truth CSVs.
* Dev adds evaluation hooks at each integration point (see [Integration Points for Evaluation](#integration-points-for-evaluation)).

**Exit criteria:**

* All three evaluators runnable against the ground truth CSV.
* Evaluation triggered automatically at each integration point.
* First scorecard produced end-to-end.

### Phase 4 — Baseline Scorecard & Feedback Loop (Weeks 8–10)

**Goal:** Establish the quality baseline and operationalise the feedback cycle.

**Activities:**

* DS runs full evaluation across all capabilities and produces the baseline scorecard.
* DS and Dev perform discrepancy analysis — categorising errors as model errors, logic errors, or ground truth errors.
* Ground truth corrections fed back to BA/UW for approval.
* PM sets acceptance thresholds for each metric.
* Dev integrates scorecard generation into CI/CD so evaluation runs on every model or prompt change.

**Exit criteria:**

* Baseline scores documented and agreed.
* Acceptance thresholds defined.
* Evaluation runs automatically in CI pipeline.
* Feedback loop documented and practised at least once.

## Ground Truth CSV Templates

### Entity Extraction

```csv
File_Name,Field_Name,Ground_Truth_Value,Data_Type,Page_Number,Business_Criticality,Notes
DOC-001.pdf,borrower_name,John Smith,String,1,high,
DOC-001.pdf,total_income,150000.00,Currency,2,high,
DOC-001.pdf,policy_start_date,2024-03-15,Date,1,medium,
```

### Document Classification

```csv
File_Name,Ground_Truth_Class,Confidence_Notes
DOC-001.pdf,income_statement,Clear header and format
DOC-002.pdf,bank_statement,Multiple accounts on single doc
```

### Summarization

```csv
File_Name,Reference_Summary,Required_Entities,Business_Criticality
DOC-001.pdf,"Applicant John Smith reports total annual income of GBP 150000 from employment at Acme Corp.","borrower_name;total_income;employer_name",high
```

### Versioning rules

* Each approved release is tagged `v1`, `v2`, etc.
* CSVs are stored in `data/ground_truth/<version>/`.
* Changes require a Pull Request reviewed by BA and DS.

## Evaluation Metrics by Capability

### Entity Extraction

The existing `ExtractionCorrectnessEvaluator` and `ExtractionCompletenessEvaluator` already produce scores. DS will augment with ground-truth-based metrics:

| Metric | What It Measures | How It Is Computed |
| :--- | :--- | :--- |
| Exact Match Rate | Percentage of fields where model output equals ground truth after normalisation | `matching_fields / total_fields` |
| Fuzzy Match Score | String similarity for name/address fields | Levenshtein ratio; threshold >= 0.90 |
| Numeric Tolerance | Financial figure accuracy | Absolute difference <= 0.01 or relative difference <= 1% |
| Field-level F1 | Precision and recall per field name | Standard F1 formula across the Golden Set |
| Extraction Completeness | Fields expected vs fields returned by model | `extracted_fields / expected_fields` |

### Document Classification

A new evaluator will be implemented in `src/evaluation/document_classification/`:

| Metric | What It Measures | How It Is Computed |
| :--- | :--- | :--- |
| Accuracy | Overall correct classifications | `correct / total` |
| Per-class Precision | False-positive rate per document type | `TP / (TP + FP)` per class |
| Per-class Recall | Miss rate per document type | `TP / (TP + FN)` per class |
| Macro F1 | Balanced measure across all classes | Average of per-class F1 scores |
| Confusion Matrix | Error distribution between classes | Cross-tabulation of predicted vs actual |

### Document Summarization

The existing evaluators (`EntityCoverageEvaluator`, `GroundednessEvaluator`, `SemanticFidelityEvaluator`) already produce a weighted composite score. DS will add:

| Metric | What It Measures | How It Is Computed |
| :--- | :--- | :--- |
| Entity Coverage (existing) | Key entities present in summary | Weighted token overlap — 40% weight |
| Groundedness (existing) | Facts traceable to source document | Containment check — 30% weight |
| Semantic Fidelity (existing) | Meaning preservation | RapidFuzz matching — 30% weight |
| Reference Summary ROUGE | N-gram overlap with UW-approved reference | ROUGE-1, ROUGE-2, ROUGE-L |
| Hallucination Rate | Statements in summary not grounded in source | LLM-judge or manual review |

## Integration Points for Evaluation

The existing framework must be activated at **every** integration point where an AI component produces an output. This is the critical operational step — evaluation must not be a one-off exercise but a continuous gate.

| Integration Point | Trigger | Evaluator(s) Used | Output |
| :--- | :--- | :--- | :--- |
| After Document Classification | Document enters the pipeline and is classified | Classification evaluator | Per-document class correctness |
| After Entity Extraction | `SchemaExtractionService` completes extraction | `EvaluationService` (correctness + completeness) | Per-field scores written to `extraction.evaluation` in Cosmos DB |
| After Summarization | `SummarizationService` produces a summary | `SummaryEvaluationService` (coverage + groundedness + fidelity) | Composite score + per-evaluator breakdown |
| Orchestration Checkpoint | All components complete for a case | All evaluators aggregated | Case-level quality scorecard |
| CI/CD Pipeline | Pull request or model/prompt change | Full evaluation suite against Golden Set | Pass/fail gate with score thresholds |
| Scheduled Regression | Weekly cron job | Full evaluation suite against Golden Set | Trend dashboard; drift alerts |

### Pipeline Flow with Evaluation Gates

```text
Document In
     |
     v
+--------------------+
|  Classification    |----> Eval: Classification Evaluator
+--------------------+
     |
     v
+--------------------+
|  Entity Extraction |----> Eval: Correctness + Completeness Evaluators
+--------------------+
     |
     v
+--------------------+
|  Summarization     |----> Eval: Coverage + Groundedness + Fidelity Evaluators
+--------------------+
     |
     v
+--------------------+
|  Orchestration     |----> Eval: Case-level Aggregate Scorecard
|  (Case Complete)   |
+--------------------+
     |
     v
  Scorecard + Feedback Loop
```

## Stakeholder Engagement Stages

The following table maps **who** is actively involved at **which** phase. "Active" means hands-on work; "Review" means sign-off or consultation; "Informed" means receives updates only.

| Phase | UW | BA | DS | Dev | PM | QA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 — Golden Set & Template | Review | Active | Review | Informed | Active | Informed |
| 2 — Ground Truth Labelling | Active | Active | Informed | Informed | Informed | Review |
| 3 — Metric Definition & Framework | Informed | Review | Active | Active | Informed | Review |
| 4 — Baseline & Feedback Loop | Review | Review | Active | Active | Active | Active |
| Ongoing — Continuous Evaluation | On-demand | Review | Active | Active | Review | Active |

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
| :--- | :--- | :---: | :---: | :--- |
| R1 | **UW availability** — Underwriters are senior, expensive resources with limited bandwidth for labelling sessions. | High | High | Schedule short, focused sessions (90 min). BA pre-fills CSV skeleton so UW effort is minimised. Rotate across UW team to distribute load. |
| R2 | **Labelling inconsistency** — Different UWs may label the same field differently. | Medium | High | Publish a labelling guide with worked examples. Perform dual-annotation on a 20% subset and measure inter-annotator agreement. Adjudicate disagreements with a senior UW. |
| R3 | **Ground truth staleness** — Document formats or business rules change and the Golden Set becomes outdated. | Medium | Medium | Re-baseline the Golden Set quarterly. Add new document types as they are onboarded. Track a `dataset_version` field in every CSV. |
| R4 | **Normalisation errors** — Differences in how UWs type values (e.g., "150k" vs "150000") cause false failures. | High | Medium | Build robust normalisation functions per data type (dates, currency, names). DS validates normalisation logic before first evaluation run. |
| R5 | **Classification evaluator gap** — No evaluator code exists today for classification. | Low | Medium | Prioritise implementation in Phase 3. Classification metrics (accuracy, F1) are well-understood and straightforward to implement. |
| R6 | **Metric gaming** — Teams optimise for metric scores rather than genuine quality. | Low | Medium | Use multiple complementary metrics per capability. Include human spot-checks alongside automated scores. PM reviews scorecard trends, not individual numbers. |
| R7 | **Data sensitivity** — Ground truth CSVs may contain PII or sensitive financial data. | Medium | High | Store CSVs in a restricted repository path with access controls. Anonymise customer data where possible. Follow Contoso data handling policies. |
| R8 | **BA bottleneck** — Single BA managing all labelling coordination. | Medium | Medium | Assign a backup BA. Provide clear written guidance so labelling can continue if primary BA is unavailable. |
| R9 | **Scope creep in labelling** — UWs identify new fields or edge cases that expand the Golden Set beyond planned capacity. | Medium | Low | PM controls scope. New fields are logged as backlog items and included in the next quarterly re-baseline, not mid-cycle. |
| R10 | **Framework drift** — Evaluation framework code diverges from the metrics DS defines. | Low | High | DS and Dev co-own the evaluator code. All metric changes require both a CSV schema update and a code PR reviewed by both roles. |

## Success Criteria

| Criterion | Target |
| :--- | :--- |
| Golden Set size | >= 50 documents covering all active document types |
| Ground truth completeness | 100% of fields labelled for all Golden Set documents |
| Inter-annotator agreement (where dual-labelled) | >= 85% agreement |
| Entity Extraction Exact Match Rate | >= 90% (baseline to improve) |
| Classification Accuracy | >= 95% |
| Summarization Composite Score | >= 0.80 |
| Evaluation runs in CI/CD | Automated on every PR that touches model/prompt code |
| Time to first scorecard | <= 10 weeks from project kick-off |

## Appendix A — Glossary

| Term | Definition |
| :--- | :--- |
| **Golden Set** | A curated, version-controlled collection of documents with human-verified labels used as the evaluation benchmark |
| **Ground Truth** | The business-correct answer for a given field, class, or summary as determined by an Underwriter |
| **Scorecard** | A report summarising evaluation metric scores across all capabilities for a given evaluation run |
| **Adjudication** | The process of resolving disagreements between annotators, led by a senior Underwriter |
| **Normalisation** | Converting both model output and ground truth values into a common format before comparison |
| **Integration Point** | A location in the processing pipeline where an AI component produces an output that can be evaluated |

## Appendix B — Recommended Tooling

| Purpose | Tool | Notes |
| :--- | :--- | :--- |
| Ground truth authoring | Microsoft Excel / Google Sheets | UWs work in a familiar environment; export to CSV |
| Version control | Git | CSVs stored in `data/ground_truth/<version>/` |
| Evaluation framework | `src/evaluation/` (existing) | Extend, do not replace |
| Scorecard visualisation | Jupyter Notebooks / Power BI | DS produces reports for PM review |
| CI/CD evaluation | Azure DevOps Pipelines | Trigger evaluation on PR; publish results as pipeline artifact |
