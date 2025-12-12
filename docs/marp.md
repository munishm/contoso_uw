---
marp: true
title: Underwriting Automation Pilot Plan
theme: default
paginate: true
---

# **HNW Underwriting Automation POC**
## Document Classification, Extraction & Summarization

---

#  Scoping & Requirements
- Define target document types
    - 2 Application forms, English to be extracted
- Define extraction field schema per document type
    - TBD, 5-6 fields in the 
- Build classification taxonomy
    - Per document for now (TBD)
- Define summarization
    - summarization of fields extracted in the document
- Establish KPIs:
  - Classification precision/recall
    - Correctness of entities
    - Completeness/Coverage
  - Summary Quality


---

# Ingestion & Preprocessing
## Pipeline Setup
- Implement ingestion API or event triggers
- Store raw docs with metadata
## OCR & Layout
- Evaluate different OCR engines
- Preprocess: denoise, rotate etc
    - TBD
- Extract layout: blocks, lines, tables
    - Normalization: line breaks, text cleanup etc.


---

# Document Classification
## Taxonomy
- Set primary & secondary classes
- Define unknown/other category

## Baselines & Models
- Experiment with various options

## Evaluation
- Confusion matrix?

---

# Field Extraction
## Schema Setup
- Define required/optional fields
- Configure validation rules

## Extraction
- Rule-based (forms)
- LLM based

## Post-processing
- Normalize dates, currencies, addresses
- Cross-field checks

---

# Summarization
## Requirements
- Build summary for provided documents
- Build summary of summaries - TBC if we get more documents

## Extractive Summary
- Extract key facts with linked spans

## Abstractive Summary
- Include citations to source text

## Evaluation
- Anish to provide 


---

# Workflows
## UI
- Summary with citations
- Summary of summaries
- Extracted fields
- Document viewer 

## Feedback
- TBD

---

# NFR's

## Config contracts
- Structured schema
- Prompt library

## Data Contracts
- Define canonical JSON schemas
- Schema versoining

## Storage
- DB for Structured outputs
- Audit logging

## Model registry
---

# Monitoring & Observability


## Drift Detection
- OCR quality?
- Classification distribution drift
- Extraction confidence shifts

## Observability
- Trace IDs across components
