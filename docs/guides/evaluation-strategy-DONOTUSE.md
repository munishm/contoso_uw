---
title: Evaluation Strategy: Ground Truth & Metric Discovery
description: A practical guide for establishing ground truth with Underwriters/BAs and enabling data science evaluation.
author: Contoso IWPB UW Team
status: draft
---

# Evaluation Strategy: Ground Truth & Metric Discovery

## Executive Summary

Contoso's Intelligent Underwriting platform requires a robust way to measure accuracy. Currently, we lack component-level evaluation and a defined ground truth strategy. This document outlines a collaborative workflow where **Underwriters (UWs)** and **Business Analysts (BAs)** provide the "Ground Truth" via standardized CSVs, which **Developers** and **Data Scientists (DS)** then use to define and execute evaluation metrics.

## The Workflow

The evaluation process follows a circular lifecycle:

1.  **Data Selection (Dev/BA):** Identifying a representative set of documents.
2.  **Ground Truth Creation (UW/BA):** Manually labeling the correct values in a simplified CSV format.
3.  **Ingestion & Metric Discovery (Dev/DS):** Loading the data and mathematically defining "accuracy" for different field types.
4.  **Automated Evaluation (Dev/DS):** Running the pipeline against the ground truth.
5.  **Review & Feedback (All):** Analyzing discrepancies to improve the model or clarify the ground truth.

---

## Phase 1: Ground Truth Creation (UWs & BAs)

The core of this strategy implies that **Underwriters are the Oracle**. If the model output disagrees with the Underwriter, the model is wrong (unless the Underwriter made a mistake).

### 1. The "Golden Set" Selection
We cannot evaluate every document. We need a **Golden Set** of 50-100 documents that cover:
*   **Simple Cases:** Clean PDFs, standard layouts.
*   **Complex Cases:** Scanned images, handwriting, poor quality.
*   **Edge Cases:** Missing fields, multiple tables, unusual formatting.

**Action:** BAs select these files and assign them unique IDs (e.g., `DOC-001.pdf`).

### 2. The Ground Truth CSV Template
UWs/BAs will work in Excel/CSV. This format must be strict to allow automated processing.

**Recommended Columns:**

| Column Header | Description | Example |
| :--- | :--- | :--- |
| `File_Name` | The exact name of the file in the Golden Set. | `policy_123.pdf` |
| `Field_Name` | The data point being extracted. | `borrower_name` |
| `Ground_Truth_Value` | The correct value as seen by the human. | `John Smith` |
| `Data_Type` | (Optional) Helps DS choose metrics. | `String` / `Date` / `Currency` |
| `Page_Number` | (Optional) Where the data is found. | `3` |
| `Business_Rule` | Any specific logic applied? | `Exclude middle name` |

**Example Row:**
```csv
File_Name,Field_Name,Ground_Truth_Value,Data_Type,Page_Number
DOC-001.pdf,total_income,150000.00,Currency,1
DOC-001.pdf,risk_rating,Medium,Categorical,1
DOC-002.pdf,inception_date,2023-01-01,Date,5
```

### 3. The Labeling Process
1.  BAs prepare the CSV skeleton with `File_Name` and `Field_Name` pre-filled.
2.  UWs open the PDF, find the value, and type it into `Ground_Truth_Value`.
3.  **Crucial Rule:** Type exactly what is essentially correct. Do not worry about formatting (e.g., "$150k" vs "150,000")—Data Science will handle normalization.

---

## Phase 2: Metric Discovery (Developers & Data Scientists)

Once the CSV is handed over, the technical team takes over. The goal is to translate "Human Correctness" into "Machine Accuracy".

### 1. Ingestion & Normalization
Developers write scripts to ingest the CSV.
*   **Challenge:** UW typed "10/12/2023", Model extracted "2023-10-12".
*   **Solution:** Normalization functions. Convert both to standard objects (ISO 8601 dates, floats for currency) before comparing.

### 2. Selecting Evaluation Metrics
The "Accuracy" depends on the data type. DS will select:

*   **Exact Match:** For categorical data (e.g., Risk Rating "High" vs "High").
*   **Levenshtein Distance (Fuzzy Match):** For names/addresses where minor typos are acceptable (e.g., "Jon Smith" vs "John Smith").
*   **Numeric Tolerance:** For financial figures (e.g., within 1% variance).
*   **IOU (Intersection Over Union):** For bounding boxes (if visual extraction is used).

| Field Type | Recommended Metric | Acceptance Criteria |
| :--- | :--- | :--- |
| Names / Address | Levenshtein Ratio | > 0.90 |
| Amounts | Absolute Difference | < 0.01 |
| Dates | Exact Match (after normalization) | True/False |
| Tables | Row/Column F1 Score | > 0.85 |

### 3. Running the Evaluation
The specific execution will happen locally or in the CI/CD pipeline:
1.  Run the IDP pipeline on the **Golden Set** documents.
2.  Capture the `Predicted_Value` for every field.
3.  Compare `Predicted_Value` vs `Ground_Truth_Value` using the metrics above.
4.  Generate a **Scorecard**.

---

## Phase 3: Feedback Loop & Iteration

Evaluation is not a one-time event.

### 1. Discrepancy Analysis
When Score < 100%, we categorize the error:
*   **Extraction Error:** The model missed the text. (Fix: Retrain/Prompt Engineering)
*   **Logic Error:** The model found text but processed it wrong. (Fix: Python Post-processing)
*   **Ground Truth Error:** The Underwriter made a typo or rules were ambiguous. (Fix: Update CSV)

### 2. Updating the Ground Truth
If an error is found in the CSV (e.g., UW typed "100" but document says "1000"):
1.  **Do not** edit the CSV ad-hoc.
2.  Maintain a master version in Git `data/ground_truth/v1.csv`.
3.  Require a Pull Request or a tracked change to update the Golden Set.

### 3. Expanding the Set
As new edge cases are discovered in production, they are added to the Golden Set (with manual labels) to prevent regression.

## Summary of Responsibilities

| Role | Output |
| :--- | :--- |
| **Business Analyst** | Defines the "Golden Set" of documents & CSV skeleton. |
| **Underwriter** | Fills the CSV with "Ground Truth" expert knowledge. |
| **Developer** | Normalizes data & builds the comparison pipeline. |
| **Data Scientist** | Defines the mathematical metrics for "Success". |

