---
title: Whole Evaluation Strategy for Underwriting Data Quality
description: End-to-end strategy to create business-approved ground truth with underwriters and business analysts, publish CSV datasets, and enable evaluation metric design by engineering and data science
author: Contoso IWPB UW Team
ms.date: 2026-02-17
ms.topic: concept
keywords:
  - evaluation strategy
  - ground truth
  - underwriting
  - business analyst
  - data science
estimated_reading_time: 12
---

# Whole Evaluation Strategy for Underwriting Data Quality

## Purpose

This strategy defines how we create, validate, and operationalize ground truth for the full underwriting workflow. It aligns underwriters, business analysts, developers, and data science on one shared evaluation lifecycle so that model and system quality can be measured consistently and improved over time.

## Scope

This strategy covers the complete evaluation surface:

* Document classification.
* Entity extraction.
* Summarization.
* Case-level decision support outputs.
* End-to-end workflow quality across all stages.

## Operating Model

Ground truth quality depends on tight collaboration between domain experts and technical teams.

* Underwriters define business-correct outcomes and adjudicate ambiguous cases.
* Business analysts translate policy and process rules into annotation guidance and acceptance criteria.
* Developers implement data contracts, ingestion, and evaluation pipelines.
* Data science defines metrics, baselines, and model-level diagnostics.
* Product and delivery leads govern cadence, scope, and release readiness decisions.

## Ground Truth Creation Workflow

### Phase 1: Define the target and labeling policy

* Define evaluation questions per capability, including what success means in business terms.
* Publish a label taxonomy for each output type.
* Define annotation rules for edge cases, missing values, conflicting sources, and unknown outcomes.
* Define severity levels for errors so evaluation reflects business impact, not only count-based errors.

### Phase 2: Build the candidate evaluation set

* Select representative cases across products, channels, document types, and complexity bands.
* Include common scenarios, rare scenarios, and known difficult samples.
* Track provenance for each record, including source system, ingestion time, and case identifiers.
* Freeze the evaluation snapshot version before annotation begins.

### Phase 3: Perform dual review and adjudication

* Use dual annotation for a defined subset to measure agreement quality.
* Route disagreements to adjudication led by senior underwriters and supported by business analysts.
* Capture adjudication rationale so future labels remain consistent.
* Measure inter-annotator agreement and use thresholds to trigger policy clarification.

### Phase 4: Approve and baseline the gold set

* Approve records only after passing completeness, consistency, and policy-conformance checks.
* Mark each approved record with version, approver role, and approval timestamp.
* Lock the approved dataset as the gold baseline for a defined release cycle.

## Ground Truth CSV Contract

After approval, we publish a standardized CSV that can be consumed by developers and data science without custom transformations.

### Required columns

| Column | Description |
| --- | --- |
| `dataset_version` | Immutable version of the ground-truth snapshot |
| `record_id` | Unique record key in evaluation set |
| `case_id` | Business case identifier |
| `document_id` | Document identifier |
| `page_id` | Optional page-level key when relevant |
| `task_type` | `classification`, `extraction`, `summarization`, or `case_decision` |
| `field_name` | Target label name for extraction or output dimension |
| `ground_truth_value` | Approved expected value |
| `ground_truth_class` | Approved expected class label when applicable |
| `business_criticality` | `high`, `medium`, or `low` |
| `adjudication_status` | `agreed`, `adjudicated`, or `single_review` |
| `annotator_role` | Role of original annotator |
| `approver_role` | Role of final approver |
| `approval_timestamp` | Final approval datetime in ISO format |
| `source_reference` | Traceability pointer to evidence |

### Data quality rules for CSV release

* No duplicate `record_id` values within a dataset version.
* No null values in mandatory identifiers and task descriptors.
* Deterministic encoding for categorical labels.
* Normalized date, currency, and number formats based on agreed standards.
* Release manifest that includes row count, checksum, and schema version.

## Handoff to Development and Data Science

Once the CSV is approved, handoff follows a controlled process.

* Business analysts publish release notes that describe scope, known limitations, and policy assumptions.
* Developers validate schema compatibility and load the dataset into the evaluation pipeline.
* Data science computes metrics and produces a metric review pack.
* Teams jointly review findings and assign remediation actions.
* All metric runs are versioned against both model/system version and dataset version.

## Evaluation Metrics Framework

Metrics should be tied to business impact and broken down by segment.

### Classification metrics

* Accuracy for broad comparability.
* Macro and weighted F1 to account for class imbalance.
* Per-class precision and recall for error localization.
* Confusion matrix slices by product and document family.

### Extraction metrics

* Exact match and token-level F1 per field.
* Numeric tolerance metrics for amounts and percentages.
* Date normalization match rate.
* Critical-field error rate with higher weighting for high-impact fields.

### Summarization metrics

* Human rubric scores for factual correctness, completeness, and clarity.
* Hallucination rate measured through manual factuality checks.
* Business acceptability score from underwriter review panels.

### Case-level decision support metrics

* Agreement rate with final human underwriting outcome.
* Critical miss rate for disqualifying conditions.
* Escalation appropriateness rate for low-confidence recommendations.

### Operational metrics

* Coverage rate of evaluable records.
* Time to evaluate from dataset publication to metric report.
* Drift indicators across periods, segments, and document types.

## Governance and Cadence

* Run weekly tactical quality reviews for active development periods.
* Run monthly governance reviews for trend decisions and release gating.
* Re-baseline the gold dataset on a planned cadence or when policy changes materially.
* Escalate blocking disagreements through a defined decision authority chain.

## Acceptance Gates

A release is considered evaluation-ready only when all gates are satisfied.

* Ground truth agreement and adjudication thresholds are met.
* CSV schema and data quality checks pass.
* Core metrics are computed successfully across all in-scope tasks.
* Business and technical sign-off is captured in release records.

## Risks and Mitigations

* Label ambiguity is reduced through explicit annotation policy and adjudication logs.
* Sampling bias is reduced through stratified case selection and periodic refresh.
* Metric misalignment is reduced through business-critical weighting and cross-team review.
* Version confusion is reduced through strict dataset, schema, and model version tagging.

## Implementation Plan

### First 30 days

* Finalize annotation policy and CSV schema.
* Pilot with a limited, representative dataset.
* Measure agreement and refine instructions.

### Days 31 to 60

* Expand coverage to all in-scope task types.
* Launch recurring metric reporting and issue triage.
* Stabilize handoff and governance routines.

### Days 61 to 90

* Introduce segment-level dashboards and drift monitoring.
* Optimize quality gates based on observed failure patterns.
* Confirm readiness for broader production-scale evaluation.

## Deliverables

* Ground truth policy package with annotation and adjudication rules.
* Versioned gold-standard CSV datasets.
* Evaluation metric catalog and threshold definitions.
* Recurring quality report template with action tracking.

## Decision Log Inputs

For each cycle, capture these inputs to maintain traceability and auditability.

* What changed in policy, data, or model since the previous cycle.
* Which segments improved, degraded, or remained stable.
* Which corrective actions were accepted, deferred, or rejected.
* Which unresolved issues require leadership escalation.
