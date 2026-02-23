---
title: "Contoso Document Intelligence Platform - Architecture Diagram"
description: "Technical architecture diagram for the Document Intelligence Platform"
author: "Contoso IWPB Engineering Team"
ms.date: 2026-01-14
marp: true
theme: default
paginate: true
style: |
  :root {
    --contoso-blue: #0078D4;
  }
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 0.9em;
  }
  h1, h2 {
    color: var(--contoso-red);
  }
  pre {
    font-size: 0.7em;
  }
  .small {
    font-size: 0.8em;
  }
---

# Architecture Overview

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Vue 3 + Vuetify Frontend                          │   │
│  │  • Dashboard • Onboarding Wizard • Results Viewer • PDF Annotator   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 API LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Backend                              │   │
│  │  Routes: /cases /documents /extraction /onboarding /processing      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │    Case      │ │   Document   │ │  Processing  │ │    Queue     │       │
│  │   Service    │ │   Service    │ │   Service    │ │   Service    │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Core Processing Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WorkflowOrchestrator │ PipelineBuilder │ ComponentRegistry         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│  CLASSIFICATION │        │   EXTRACTION    │        │ SUMMARIZATION   │
│                 │        │                 │        │                 │
│ DirectDocument  │        │ SchemaExtraction│        │ Summarization   │
│ Classifier      │        │ Service         │        │ Service         │
│                 │        │                 │        │                 │
│ • Azure CU      │        │ • Model Adapters│        │ • LLM Summarizer│
│ • Confidence    │        │ • Schema Service│        │ • Templates     │
│ • Page-level    │        │ • Field Mapping │        │ • Citations     │
└─────────────────┘        └─────────────────┘        └─────────────────┘
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVALUATION LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EvaluationService │ CorrectnessEvaluator │ CompletenessEvaluator   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Extraction Model Adapters

## Pluggable Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ExtractionModelAdapter (Base Interface)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  extract() │ get_confidence() │ supports_document_type()            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
     │  AzureOpenAI    │    │   DocIntel      │    │    Future       │
     │  VisionAdapter  │    │   OCRAdapter    │    │    Adapters     │
     │                 │    │                 │    │                 │
     │ • GPT-4o        │    │ • Layout API    │    │ • Claude        │
     │ • GPT-4 Vision  │    │ • Read API      │    │ • Gemini        │
     │ • Structured    │    │ • Table Extract │    │ • Local LLMs    │
     │   Output        │    │                 │    │                 │
     └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

# Data Flow Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───▶│ Classify │───▶│ Extract  │───▶│ Evaluate │───▶│Summarize │
│          │    │          │    │          │    │          │    │          │
│ PDF/Image│    │ Azure CU │    │ GPT-4o   │    │ AI Eval  │    │ LLM      │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COSMOS DB                                       │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐     │
│  │   cases   │ │ documents │ │ entities  │ │ summaries │ │ schemas   │     │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BLOB STORAGE                                      │
│  ┌───────────────────────┐    ┌───────────────────────┐                     │
│  │    Raw Documents      │    │   Processed Results   │                     │
│  │    (PDF, Images)      │    │   (JSON, Annotations) │                     │
│  └───────────────────────┘    └───────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Repository Pattern

## Data Access Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REPOSITORY LAYER                                   │
└─────────────────────────────────────────────────────────────────────────────┘
              │
   ┌──────────┼──────────┬──────────┬──────────┬──────────┐
   │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Case   │ │Document│ │ Entity │ │Summary │ │Counter │ │Schema  │
│ Repo   │ │ Repo   │ │ Repo   │ │ Repo   │ │ Repo   │ │ Repo   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
   │          │          │          │          │          │
   └──────────┴──────────┴──────────┴──────────┴──────────┘
                                │
                    ┌───────────┴───────────┐
                    │    CosmosClient       │
                    │    (Async SDK)        │
                    └───────────────────────┘
```

---

# Interface Contracts

## Python Protocols for Pluggability

```python
# src/interfaces/

class IClassifier(Protocol):
    def classify(document) -> ClassificationResult
    def get_supported_types() -> List[str]

class IEntityExtractor(Protocol):
    def extract(document) -> List[Entity]
    def get_entity_types() -> List[str]
    def set_confidence_threshold(threshold: float)

class ISummarizer(Protocol):
    def summarize(entities) -> Summary
    def get_templates() -> List[Template]

class IDocumentProcessor(Protocol):
    def process(document) -> ProcessingResult
    def supports_format(format: str) -> bool
```

**Benefits**: Swap implementations without code changes

---

# Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ONBOARDING API ROUTES                                │
│  POST /classify-document │ POST /test-extraction │ POST /finalize           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Upload          Step 2: Configure       Step 3: Test & Evaluate   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ • Upload PDF    │───▶│ • Select Model  │───▶│ • Run Extraction│         │
│  │ • Classify      │    │ • Define Schema │    │ • Get Eval Scores│         │
│  │ • Get Doc Type  │    │ • Set Prompts   │    │ • Review Results │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                          │                  │
│                              Step 4: Finalize ◀──────────┘                  │
│                              ┌─────────────────┐                            │
│                              │ • Save Schema   │                            │
│                              │ • Version Config│                            │
│                              │ • Activate      │                            │
│                              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Evaluation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVALUATION SERVICE                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  evaluate() │ evaluate_batch() │ to_json()                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
              ▼                                               ▼
     ┌─────────────────────────┐                 ┌─────────────────────────┐
     │  CorrectnessEvaluator   │                 │  CompletenessEvaluator  │
     │                         │                 │                         │
     │  • Token matching       │                 │  • LLM-based assessment │
     │  • Source text lookup   │                 │  • Missing info detect  │
     │  • Coverage ratio       │                 │  • Reasoning output     │
     │                         │                 │                         │
     │  Input: extracted_value │                 │  Input: extracted_value │
     │         source_text     │                 │         source_text     │
     │  Output: score (0-1)    │                 │  Output: score (0-1)    │
     └─────────────────────────┘                 └─────────────────────────┘
```

---

# Azure Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AZURE RESOURCE GROUP                               │
└─────────────────────────────────────────────────────────────────────────────┘
              │
   ┌──────────┼──────────┬──────────┬──────────┬──────────┐
   │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Azure   │ │Azure   │ │Azure   │ │Azure   │ │Azure   │ │Azure   │
│OpenAI  │ │Cosmos  │ │Blob    │ │Content │ │Service │ │App     │
│        │ │DB      │ │Storage │ │Under-  │ │Bus     │ │Service │
│        │ │        │ │        │ │standing│ │        │ │        │
│• GPT-4o│ │• cases │ │• docs  │ │• class-│ │• queue │ │• API   │
│• GPT-4V│ │• docs  │ │• result│ │  ifier │ │        │ │• web   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

**Deployment**: Azure Bicep (IaC)

---

# Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VUE 3 APPLICATION                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         App.vue (Root)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
              │
   ┌──────────┼──────────┬──────────┬──────────┐
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Views  │ │ Stores │ │Services│ │ Router │ │Components│
│        │ │(Pinia) │ │        │ │        │ │        │
│Dashboard│ │cases   │ │caseAPI │ │ /cases │ │StatusBadge│
│Onboard │ │docs    │ │docAPI  │ │ /docs  │ │PDFViewer│
│Results │ │ui      │ │onboard │ │/onboard│ │FieldList│
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

---

# Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION & AUTHORIZATION                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Azure AD      │────────▶│  Managed        │────────▶│   RBAC          │
│   (Entra ID)    │         │  Identity       │         │   Policies      │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  User Auth      │         │  Service Auth   │         │  Resource       │
│  (OAuth 2.0)    │         │  (No secrets)   │         │  Access Control │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

# Component Dependencies

```
src/
├── api/                      # REST API Layer
│   ├── routes/              # HTTP endpoints
│   ├── services/            # Business logic
│   ├── repositories/        # Data access
│   └── models/              # Request/Response DTOs
│
├── orchestration/           # Workflow Engine
│   ├── pipeline.py          # PipelineBuilder
│   ├── workflow.py          # WorkflowOrchestrator
│   └── registry.py          # ComponentRegistry
│
├── document_classification/ # Classification Component
├── entity_extraction/       # Extraction Component
│   ├── adapters/           # Model adapters (pluggable)
│   └── services/           # Extraction services
├── document_summarization/ # Summarization Component
├── evaluation/             # Quality Evaluation
│   └── entity_extraction/  # Extraction evaluators
│
├── interfaces/             # Python Protocols (contracts)
└── shared/                 # Common utilities
```

---

# Summary: Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **API Framework** | FastAPI | Async, type-safe, auto-docs |
| **Frontend** | Vue 3 + Vuetify | Reactive, component-based |
| **Database** | Cosmos DB | Scalable NoSQL, Azure native |
| **AI Services** | Azure OpenAI | Enterprise-grade, compliant |
| **Classification** | Azure Content Understanding | Built-in doc intelligence |
| **Architecture** | Pluggable adapters | Future-proof, extensible |
| **Evaluation** | Dual AI evaluators | No ground truth required |
| **IaC** | Azure Bicep | Declarative, repeatable |
