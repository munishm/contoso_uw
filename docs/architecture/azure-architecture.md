---
title: "HNW Insurance Intelligence Platform - Azure Architecture"
description: "Azure architecture diagram for the Document Intelligence Platform"
author: "ISE Team"
ms.date: 2026-01-14
---

# HNW Insurance Intelligence Platform - Azure Architecture

## Overview

This document describes the Azure architecture for the Document Intelligence Platform, designed for insurance underwriting automation with extensibility for other document processing use cases.

## High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph Users["Users"]
        UW[("👤 Underwriter")]
        Admin[("👤 Admin/Power User")]
    end

    subgraph Frontend["Presentation Layer"]
        WebApp["🌐 Vue 3 Web Application<br/>(Azure Static Web App)"]
    end

    subgraph API["API Layer"]
        FastAPI["⚡ FastAPI Backend<br/>(Azure App Service)"]
    end

    subgraph Processing["Document Processing"]
        direction TB
        Classification["📑 Document Classification"]
        Extraction["🔍 Entity Extraction"]
        Summarization["📝 Summarization"]
        Evaluation["✅ AI Evaluation"]
    end

    subgraph AIServices["Azure AI Services"]
        AOAI["🤖 Azure OpenAI<br/>GPT-4o / GPT-4 Vision"]
        ACU["📄 Azure Content<br/>Understanding"]
        DocIntel["📋 Azure Document<br/>Intelligence"]
    end

    subgraph Storage["Data Layer"]
        CosmosDB[("🗄️ Azure Cosmos DB")]
        BlobStorage[("📦 Azure Blob Storage")]
    end

    subgraph Messaging["Async Processing"]
        ServiceBus["📨 Azure Service Bus"]
    end

    subgraph Security["Security & Identity"]
        EntraID["🔐 Microsoft Entra ID"]
        ManagedID["🔑 Managed Identity"]
    end

    Users --> WebApp
    WebApp --> FastAPI
    FastAPI --> Processing
    Processing --> AIServices
    Processing --> Storage
    FastAPI --> Messaging
    Messaging --> Processing
    
    EntraID --> WebApp
    EntraID --> FastAPI
    ManagedID --> AIServices
    ManagedID --> Storage
```

## Component Architecture

```mermaid
flowchart LR
    subgraph Input["Document Input"]
        PDF["📄 PDF"]
        Image["🖼️ Image"]
        Scan["📠 Scanned Doc"]
    end

    subgraph Pipeline["Processing Pipeline"]
        direction TB
        P1["1️⃣ Ingest & Store"]
        P2["2️⃣ Classify Document"]
        P3["3️⃣ Extract Entities"]
        P4["4️⃣ Evaluate Quality"]
        P5["5️⃣ Generate Summary"]
        P1 --> P2 --> P3 --> P4 --> P5
    end

    subgraph Output["Results"]
        Entities["📊 Structured Data"]
        Scores["📈 Quality Scores"]
        Summary["📝 Summary"]
    end

    Input --> Pipeline --> Output
```

## Azure Services Used

| Service | Purpose |
|---------|----------|
| **Azure App Service** | Host FastAPI backend |
| **Azure Static Web Apps** | Host Vue 3 frontend |
| **Azure Cosmos DB** | Store cases, documents, entities, schemas |
| **Azure Blob Storage** | Store raw documents and processed results |
| **Azure OpenAI Service** | GPT-4.1 for extraction |
| **Azure Content Understanding** | Document classification |
| **Azure Document Intelligence** | OCR, layout extraction, and citations |
| **Azure Service Bus** | Async message processing |
| **Microsoft Entra ID** | Authentication and authorization |
| **Azure Key Vault** | Secrets management |
| **Azure Monitor** | Logging and observability |

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant WebApp as Vue Frontend
    participant API as FastAPI
    participant Blob as Blob Storage
    participant ACU as Content Understanding
    participant AOAI as Azure OpenAI (GPT-4.1)
    participant DocIntel as Azure Document Intelligence
    participant Cosmos as Cosmos DB

    User->>WebApp: Upload Document
    WebApp->>API: POST /documents
    API->>Blob: Store Raw Document
    API->>ACU: Classify Document
    ACU-->>API: Document Type + Confidence
    API->>AOAI: Extract Entities (GPT-4.1)
    AOAI-->>API: Extracted Fields
    API->>DocIntel: Get Citations
    DocIntel-->>API: Document Citations
    API->>AOAI: Evaluate Extraction
    AOAI-->>API: Correctness + Completeness Scores
    API->>AOAI: Generate Summary
    AOAI-->>API: Document Summary
    API->>Cosmos: Store Results
    API-->>WebApp: Processing Complete
    WebApp-->>User: Display Results
```

## Cosmos DB Collections

```mermaid
erDiagram
    CASES ||--o{ DOCUMENTS : contains
    DOCUMENTS ||--o{ ENTITIES : has
    DOCUMENTS ||--o| SUMMARIES : has
    EXTRACTION_SCHEMAS ||--o{ EXTRACTION_MODELS : uses
    
    CASES {
        string case_id PK
        string case_number
        string status
        datetime created_at
    }
    
    DOCUMENTS {
        string document_id PK
        string case_id FK
        string filename
        string classification
        string processing_status
        object extraction
    }
    
    ENTITIES {
        string entity_id PK
        string document_id FK
        string entity_type
        string value
        float confidence
    }
    
    SUMMARIES {
        string summary_id PK
        string document_id FK
        string content
        object citations
    }
    
    EXTRACTION_SCHEMAS {
        string schema_id PK
        string document_type
        object fields
        string version
    }
    
    EXTRACTION_MODELS {
        string model_id PK
        string name
        string adapter_type
        object config
    }
```
flowchart TB
    subgraph BusinessCases["Business Cases"]
        IUW["🏥 Insurance Underwriting"]
        CUW["💳 Credit Underwriting"]
        KYC["🔍 KYC Processing"]
        Claims["📋 Claims Processing"]
    end

    subgraph Config["Business Case Configuration (Cosmos DB)"]
        BC_Config[("Business Case Configs<br/>• Pipeline Steps<br/>• Document Types<br/>• Extraction Schemas<br/>• Evaluation Rules")]
    end

    subgraph Orchestrator["Durable Functions Orchestrator"]
        Start([Start])
        LoadBC["Load Business Case Config"]
        DynamicPipeline["Execute Dynamic Pipeline"]
        End([Complete])
        
        Start --> LoadBC --> DynamicPipeline --> End
    end

    subgraph Activities["Activity Registry"]
        A1["IngestActivity"]
        A2["ClassifyActivity"]
        A3["ExtractActivity"]
        A4["EvaluateActivity"]
        A5["SummarizeActivity"]
        A6["RiskScoreActivity"]
        A7["ComplianceCheckActivity"]
        A8["FraudDetectionActivity"]
        AN["...Custom Activities"]
    end

    BusinessCases --> Config
    Config --> Orchestrator
    Orchestrator --> Activities

## Document Type Onboarding Flow

```mermaid
flowchart TB
    subgraph Step1["Step 1: Upload & Classify"]
        Start([Power User])
        Upload["📄 Upload Sample Document"]
        Mode{"Select Mode"}
        CreateNew["Create New Type"]
        EditExisting["Edit Existing Type"]
        Classify["🔍 Classify Document"]
        ACU["Azure Content Understanding"]
        Result1["Document Type + Confidence"]
        GroundTruth["📋 Upload Ground Truth<br/>(Optional)"]
    end

    subgraph Step2["Step 2: Configure"]
        Config["⚙️ Configure Document Type"]
        TypeName["Document Type Name"]
        ModelSelect["🤖 Select Extraction Model"]
        ModelRegistry[("Model Registry")]
        CustomPrompt["✏️ Custom Prompt<br/>(Optional)"]
        Schema["📝 Define Schema<br/>(Input/Output)"]
        Threshold["🎚️ Set Confidence Threshold"]
    end

    subgraph Step3["Step 3: Test & Review"]
        TestExtract["🧪 Test Extraction"]
        AOAI["Azure OpenAI (GPT-4.1)"]
        Evaluate{"Evaluate Results"}
        WithGT["With Ground Truth<br/>Accuracy Metrics"]
        WithoutGT["Without Ground Truth<br/>AI Evaluators"]
        Metrics["📊 Metrics<br/>• Confidence<br/>• Completeness<br/>• Correctness"]
        Decision{"Results OK?"}
        ABTest["📊 A/B Compare Models"]
        Adjust["⚙️ Adjust Configuration"]
    end

    subgraph Step4["Step 4: Finalize"]
        Review["📋 Review Summary"]
        Save["💾 Save Configuration"]
        Cosmos[("Cosmos DB<br/>• extraction_schemas<br/>• extraction_models")]
        Complete([✅ Onboarding Complete])
    end

    Start --> Upload
    Upload --> Mode
    Mode -->|New| CreateNew
    Mode -->|Edit| EditExisting
    CreateNew --> Classify
    EditExisting --> Classify
    Classify --> ACU
    ACU --> Result1
    Result1 --> GroundTruth
    GroundTruth --> Config

    Config --> TypeName
    TypeName --> ModelSelect
    ModelSelect --> ModelRegistry
    ModelRegistry --> CustomPrompt
    CustomPrompt --> Schema
    Schema --> Threshold
    Threshold --> TestExtract

    TestExtract --> AOAI
    AOAI --> Evaluate
    Evaluate -->|Has GT| WithGT
    Evaluate -->|No GT| WithoutGT
    WithGT --> Metrics
    WithoutGT --> Metrics
    Metrics --> Decision
    Decision -->|No| ABTest
    Decision -->|No| Adjust
    ABTest --> TestExtract
    Adjust --> Config
    Decision -->|Yes| Review

    Review --> Save
    Save --> Cosmos
    Cosmos --> Complete
```

## Monitoring & Observability

```mermaid
flowchart TB
    subgraph Apps["Applications"]
        API["FastAPI"]
        Web["Vue App"]
    end

    subgraph Monitoring["Azure Monitor"]
        AppInsights["📊 Application Insights"]
        LogAnalytics["📋 Log Analytics"]
        Alerts["🔔 Alerts"]
        Dashboards["📈 Dashboards"]
    end

    Apps --> AppInsights
    AppInsights --> LogAnalytics
    LogAnalytics --> Alerts
    LogAnalytics --> Dashboards
```

---

*Architecture Version: 1.0*  
*Last Updated: January 2026*
