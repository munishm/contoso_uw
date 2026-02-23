---
title: "Contoso Bank Document Intelligence Platform"
description: "Executive presentation showcasing the Document Intelligence Platform capabilities for insurance underwriting automation"
author: "Contoso Bank IWPB Engineering Team"
ms.date: 2026-01-14
marp: true
theme: default
paginate: true
style: |
  :root {
    --contoso-blue: #0078D4;
    --contoso-black: #000000;
    --contoso-white: #FFFFFF;
  }
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
  }
  h1, h2 {
    color: var(--contoso-blue);
  }
  section.title {
    background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
    color: white;
  }
  section.title h1, section.title h2 {
    color: white;
  }
  .highlight {
    color: var(--contoso-blue);
    font-weight: bold;
  }
  table {
    font-size: 0.85em;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .checkmark {
    color: #28a745;
  }
  .crossmark {
    color: #dc3545;
  }
---

<!-- _class: title -->

# Contoso Bank Document Intelligence Platform

## Next-Generation Document Processing for Insurance Underwriting

**Technical Deep Dive**

---

# Agenda

1. **Current State vs. Platform Capabilities**
2. **Self-Service Document Type Onboarding**
3. **AI-Powered Evaluation Framework**
4. **Pluggable Architecture**
5. **Human-in-the-Loop Workflows**
6. **Extensible Orchestration**
7. **Live Demo**
8. **Future Extensibility**

---

# Current Pilot vs. Platform

| Capability | Current Pilot | This Platform |
|------------|---------------|---------------|
| Document Extraction | ✅ OCR + GPT | ✅ OCR + GPT (Multiple Models) |
| Output Format | JSON Key-Value | JSON + Citations + Confidence |
| Evaluation | ⚠️ Limited | ✅ AI-Powered (Correctness + Completeness) |
| New Document Types | ❌ Developer Required | ✅ Self-Service Onboarding |
| Quality Assurance | ❌ Manual Review | ✅ Automated Scoring |
| Architecture | Monolithic | Pluggable Components |
| Workflow Extensibility | Limited | Full Orchestration Engine |

---

# The Challenge: Adding New Document Types

## Current Process

```
New Document Type Request
        ↓
Developer writes custom extraction logic
        ↓
Manual testing with sample documents
        ↓
No way to measure accuracy
        ↓
Deploy and hope it works
        ↓
Issues discovered in production
```

**Timeline**: Weeks to months per document type

---

# The Solution: Self-Service Onboarding

## 4-Step Wizard for Business Users

<div class="columns">
<div>

### Step 1: Upload & Classify
- Upload sample document
- Auto-classification with confidence
- Optional ground truth

### Step 2: Configure
- Select extraction model
- Define field schema
- Customize prompts

</div>
<div>

### Step 3: Test & Evaluate
- Real-time extraction preview
- AI-powered quality scores
- Iterate until satisfied

### Step 4: Finalize
- One-click deployment
- Version control
- Instant availability

</div>
</div>

**Timeline**: Minutes to hours

---

# AI-Powered Evaluation Framework

## The Problem

**How do you know extraction is correct?**

- Without ground truth data, accuracy is unknown
- Issues discovered only in production
- Manual review of every extraction is not scalable

## Our Solution: Dual AI Evaluators

| Evaluator | Purpose |
|-----------|--------|
| **Correctness** | Is the value present in source document? |
| **Completeness** | Is the full value captured? |

---

# Evaluation: No Ground Truth Required

## How It Works

**Correctness Evaluator**
- Tokenizes extracted value and source text
- Measures token-level coverage ratio
- 100% = all tokens found in source

**Completeness Evaluator**
- Uses LLM to assess extraction quality
- Checks if full context was captured
- Provides reasoning for scores

---

# Evaluation in Action

## Per-Field Quality Scores

| Field | Extracted Value | Correctness | Completeness | Status |
|-------|-----------------|-------------|--------------|--------|
| Applicant Name | John Smith | 95% 🟢 | 100% 🟢 | ✅ Pass |
| Policy Amount | $500,000 | 100% 🟢 | 100% 🟢 | ✅ Pass |
| Coverage Start | 2026-01-15 | 88% 🟢 | 92% 🟢 | ✅ Pass |
| Medical History | Diabetes Type 2 | 72% 🟡 | 65% 🟡 | ⚠️ Review |

**Scores are color-coded**: 🟢 ≥80% | 🟡 50-79% | 🔴 <50%

**Each field links to source text** for visual verification

---

# Pluggable Architecture

## Swap Components Without Code Changes

| Layer | Current | Can Add |
|-------|---------|--------|
| **Classification** | Azure CU | Custom ML |
| **Extraction** | GPT-4o, GPT-4V | Claude, Gemini |
| **Summarization** | GPT-4o | Any LLM |
| **OCR** | Azure Doc Intel | Tesseract |

---

# How Pluggable Architecture Works

## Interface-Driven Design

- Each component implements a **Python Protocol**
- Swap implementations via **configuration**
- Register new models in **Model Registry**
- **No redeployment** needed for new models

## Benefits

- Future-proof: adopt new AI models easily
- Vendor flexibility: avoid lock-in
- Test alternatives: compare performance

---

# Human-in-the-Loop

## Smart Routing Based on Confidence

| Confidence | Action | Effort |
|------------|--------|--------|
| 🟢 High (≥80%) | Auto-approve | None |
| 🟡 Medium (50-79%) | Quick review | Minimal |
| 🔴 Low (<50%) | Full review | Full |

**Result**: Reviewers focus only on uncertain extractions

---

# Citation Highlighting

## Visual Verification in Seconds

- **Click any field** → Source highlighted in PDF
- **Side-by-side view**: Data + Document
- **Approve or Edit** directly in UI
- **Audit trail**: All changes logged

---

# Extensible Orchestration

## Define Custom Workflows

```python
workflow = (
    PipelineBuilder()
    .add_step("ingest", IngestDocument())
    .add_step("classify", ClassifyDocument())
    .add_step("extract", ExtractEntities())
    .add_step("validate", BusinessRules())
    .add_step("summarize", GenerateSummary())
    .build()
)
```

---

# Orchestration Capabilities

## Built-in Features

| Capability | Description |
|------------|-------------|
| **Retry Logic** | Automatic retry with backoff |
| **Error Handling** | Graceful fallbacks |
| **Audit Logging** | Full traceability |
| **Async Execution** | Non-blocking processing |
| **Component Discovery** | Auto-register new steps |

---

# Architecture Benefits

<div class="columns">
<div>

## For Development

- **Monorepo Structure**: Single source of truth
- **Typed Interfaces**: Python Protocols
- **Independent Testing**: Per-component tests
- **Version Control**: Schema versioning

</div>
<div>

## For Operations

- **Azure Native**: Cosmos DB, Blob Storage, OpenAI
- **Observability**: Trace IDs, metrics, logs
- **Scalability**: Stateless components
- **Security**: Managed identities, RBAC

</div>
</div>

---

# Demo Walkthrough

## Demo 1: Self-Service Onboarding

Upload → Configure → Test → Evaluate → Deploy

## Demo 2: Extraction Results

Field scores → Citation links → PDF overlay

## Demo 3: Human Review

Flagged items → Verify → Approve/Edit

---

# Beyond Insurance Underwriting

## The Platform is Use-Case Agnostic

| Use Case | Document Types | Key Fields |
|----------|---------------|------------|
| **Insurance Underwriting** | Applications, Medical Reports | Applicant info, Coverage, Conditions |
| **Claims Processing** | Claim Forms, Invoices, Reports | Claim details, Amounts, Dates |
| **Credit Insurance** | Financial Statements, Credit Reports | Exposures, Ratings, Terms |
| **Trade Finance** | Letters of Credit, Bills of Lading | Parties, Amounts, Shipping details |
| **KYC/AML** | ID Documents, Utility Bills | Identity verification, Address proof |

**Same platform, different configurations**

---

# Roadmap: Designed for Scale

## Ready for Future Requirements

| Capability | Status |
|------------|--------|
| Multi-language (Chinese) | Architecture ready |
| Multi-document scenarios | Designed for |
| Real-time processing | Event-driven ready |
| Legacy integration | API-first design |

---

# Roadmap: Pluggable Extensions

## Easy to Add

- **New AI Models**: As they emerge (GPT-5, etc.)
- **Business Rules**: Custom validation engines
- **Industry Validators**: Domain-specific checks
- **Data Enrichment**: External API integration
- **Fraud Detection**: Pattern recognition modules

---

# Key Differentiators Summary

| Feature | Business Value |
|---------|---------------|
| **Self-Service Onboarding** | Days → Hours for new document types |
| **AI Evaluation** | Quality assurance without labeled data |
| **Pluggable Architecture** | Future-proof, swap components easily |
| **Human-in-the-Loop** | Smart routing reduces review burden |
| **Extensible Orchestration** | Adapt workflows to any business process |
| **Citation Linking** | Visual verification of extracted data |

---

<!-- _class: title -->

# Questions?

## Ready for Live Demo

---

# Appendix: Technical Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Vue 3, Vuetify, TypeScript |
| **Backend API** | FastAPI, Python 3.11+ |
| **AI/ML** | Azure OpenAI (GPT-4o, GPT-4V), Azure Document Intelligence |
| **Database** | Azure Cosmos DB |
| **Storage** | Azure Blob Storage |
| **Infrastructure** | Azure Bicep (IaC) |
| **Testing** | Pytest, Playwright |

---

# Appendix: Evaluation Metrics Detail

## Correctness Evaluator

- Tokenizes extracted value and source text
- Measures token-level coverage
- Score = matched tokens / total extracted tokens
- 100% = all extracted tokens found in source

## Completeness Evaluator

- Uses GPT-4 to assess extraction quality
- Checks if full context was captured
- Identifies missing information
- Provides reasoning for scores
