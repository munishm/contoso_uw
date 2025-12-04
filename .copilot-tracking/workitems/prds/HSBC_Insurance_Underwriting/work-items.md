# Work Items

Date: 2025-11-29
State: Draft

## Epic: AI-Driven Insurance Underwriting Workflow

State: New
Description: End-to-end AI-assisted underwriting workflow covering document intake, verification, summarization, and quality metrics with compliance.
Tags: underwriting;document-processing;ui-ux

### Feature: Document Intake & Classification

State: New
Description: Classify and organize incoming underwriting documents and detect duplicates.
Tags: document-processing

- User Story: Implement document classifier MVP
  State: New
  Description: As an underwriter, I want documents to be automatically classified so I can find relevant items faster.
  Acceptance Criteria:
  - Upload batch of 30+ docs gets classified into known types
  - Confidence score returned per item
  - Misclassifications can be flagged for feedback

- User Story: Document list UI with status indicators
  State: New
  Description: As a user, I need a list showing classification, image quality, and checklist status.
  Acceptance Criteria:
  - Columns: Type, Quality, Checklist, Flags
  - Sort/filter by type and status

### Feature: Image Quality & Criteria Checks

State: New
Description: Assess scan quality and detect malicious or non-compliant documents.
Tags: quality-metrics;compliance

- User Story: Image quality evaluation
  State: New
  Description: As an underwriter, I need automatic quality checks to ensure readability.
  Acceptance Criteria:
  - Metrics: resolution, blur, contrast
  - Thresholds configurable per region

- User Story: Malicious/criteria checks
  State: New
  Description: As a reviewer, I need automated checks against document criteria and malicious content.
  Acceptance Criteria:
  - Flag anomalies and policy violations
  - Exportable report per case

### Feature: Document Checklist Verification

State: New
Description: Verify required documents per case and track missing items.
Tags: compliance

- User Story: Checklist engine
  State: New
  Description: As a case owner, I need a dynamic checklist mapped to product and region.
  Acceptance Criteria:
  - Rules per product/region
  - Missing docs clearly indicated

### Feature: Per-Document Summarization

State: New
Description: Generate concise document-level summaries with preview.
Tags: summarization

- User Story: Summary with preview
  State: New
  Description: As an underwriter, I want AI-generated summaries with preview of the original.
  Acceptance Criteria:
  - Summary + link to source page
  - Feedback capture (agree/disagree)

### Feature: Identity & Signature Verification

State: New
Description: Verify identity across documents and validate signatures.
Tags: identity-verification;signature-verification

- User Story: ID verification
  State: New
  Description: As a compliance officer, I need ID consistency checks across documents.
  Acceptance Criteria:
  - Cross-doc entity matching
  - Confidence score + review queue

- User Story: Signature verification (Azure)
  State: New
  Description: As a security reviewer, I need signature verification using Azure-native services.
  Acceptance Criteria:
  - Replace/augment Tesseract with Azure-based solution
  - No customer training data required

### Feature: Case-Level Summarization & Assessment

State: New
Description: Generate overall case summary and assessment.
Tags: summarization

- User Story: Case summary
  State: New
  Description: As an underwriter lead, I want a single case-level summary that aggregates per-document insights.
  Acceptance Criteria:
  - Summary includes risks, missing items, and recommendations

### Feature: Quality Metrics & User Feedback

State: New
Description: Compute and display quality metrics for outputs and collect user satisfaction.
Tags: quality-metrics

- User Story: Quality metrics computation
  State: New
  Description: As a manager, I need relevancy, consistency, fluency, and coherence scores per case.
  Acceptance Criteria:
  - Scores stored and visible in UI

- User Story: User satisfaction capture
  State: New
  Description: As a user, I want to record an overall satisfaction score per case.
  Acceptance Criteria:
  - 1-5 scale persisted per case

### Feature: UI/UX Workflow & Versioning

State: New
Description: Streamlined workflow with diffs between versions and audit support.
Tags: ui-ux

- User Story: Version diff view
  State: New
  Description: As a reviewer, I need a summary of additional documents between versions.
  Acceptance Criteria:
  - Show added/removed docs and summary changes

### Feature: Regional Compliance & Data Residency

State: New
Description: Ensure data residency (e.g., HK region) and compliance handling.
Tags: compliance

- User Story: Regional routing & residency
  State: New
  Description: As an architect, I need all HK data to remain in-region.
  Acceptance Criteria:
  - Enforce region-scoped processing and storage

### Feature: Model Governance

State: New
Description: Establish governance, evaluation, and monitoring of AI models.
Tags: governance

- User Story: Governance baseline
  State: New
  Description: As a governance lead, I need model evaluation, drift detection, and audit trails.
  Acceptance Criteria:
  - Evaluation datasets and metrics defined
  - Traceability with diagnostics logs
