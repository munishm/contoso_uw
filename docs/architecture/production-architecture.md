---
title: "Document Intelligence Platform - Production Architecture"
description: "Scalable production architecture for document processing platform"
author: "ISE Team"
ms.date: 2026-01-18
---

# Document Intelligence Platform - Production Architecture

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Platform-First** | Extensible beyond underwriting; pluggable document types |
| **Cost-Optimized** | Consumption-based services; scale to zero when idle |
| **Async Processing** | Queue-based pipeline; tolerates bursts |
| **Data Residency** | All data stays in Asia region |
| **Audit Ready** | Complete logging for HK regulatory compliance |

## Architecture Overview

```mermaid
flowchart TB
    subgraph Ingestion["Document Ingestion"]
        Email["📧 Email"]
        Dataverse["📊 Dataverse"]
        API["🔌 API Upload"]
    end

    subgraph Platform["Document Intelligence Platform"]
        subgraph Gateway["API Gateway"]
            APIM["🚪 Azure API Management<br/>(Consumption Tier)"]
        end

        subgraph Queue["Message Queue"]
            ServiceBus["📨 Azure Service Bus<br/>(Standard)"]
        end

        subgraph Processing["Processing Layer"]
            Functions["⚡ Azure Functions<br/>(Consumption Plan)"]
        end

        subgraph AI["AI Services"]
            AOAI["🤖 Azure OpenAI<br/>(GPT-4.1)"]
            DocIntel["📋 Document Intelligence"]
            ACU["📄 Content Understanding"]
        end

        subgraph Data["Data Layer"]
            Cosmos[("🗄️ Cosmos DB<br/>(Serverless)")]
            Blob[("📦 Blob Storage<br/>(Standard)")]
        end

        subgraph Config["Configuration"]
            SchemaStore["📝 Schema Store"]
            ModelRegistry["🤖 Model Registry"]
            PromptStore["💬 Prompt Store"]
        end
    end

    subgraph Consumers["Downstream Systems"]
        PullAPI["🔄 Pull API"]
        Downstream["📊 Downstream Systems"]
    end

    subgraph Observability["Monitoring"]
        Monitor["📊 Azure Monitor"]
        AppInsights["🔍 Application Insights"]
        AuditLogs["📋 Audit Logs"]
    end

    Email --> Dataverse
    Dataverse --> APIM
    API --> APIM
    APIM --> ServiceBus
    ServiceBus --> Functions
    Functions --> AI
    Functions --> Data
    Functions --> Config
    Config --> Cosmos
    PullAPI --> Cosmos
    PullAPI --> Downstream
    Functions --> Monitor
    APIM --> AppInsights
    Functions --> AuditLogs
```

## Component Details

### 1. Document Ingestion

```mermaid
flowchart LR
    subgraph Sources["Document Sources"]
        Email["📧 Email Inbox"]
        Manual["👤 Manual Upload"]
        RPA["🤖 RPA Bot"]
    end

    subgraph Dataverse["Microsoft Dataverse"]
        Trigger["⚡ Power Automate<br/>Trigger"]
        Queue["📋 Document Queue"]
    end

    subgraph Platform["Platform API"]
        Endpoint["POST /documents"]
    end

    Email --> Trigger
    Manual --> Trigger
    RPA --> Trigger
    Trigger --> Queue
    Queue --> Endpoint
```

### 2. Processing Pipeline

```mermaid
flowchart TB
    subgraph Receive["1. Receive"]
        SB["Service Bus Queue"]
        Trigger["Function Trigger"]
    end

    subgraph Store["2. Store Raw"]
        Blob["Blob Storage"]
        Metadata["Cosmos DB<br/>(metadata)"]
    end

    subgraph Classify["3. Classify"]
        ACU["Content Understanding"]
        DocType["Document Type"]
    end

    subgraph LoadConfig["4. Load Config"]
        Schema["Get Schema"]
        Model["Get Model Config"]
        Prompt["Get Prompt"]
    end

    subgraph Extract["5. Extract"]
        AOAI["Azure OpenAI<br/>(GPT-4.1)"]
        DocIntel["Document Intelligence<br/>(Citations)"]
    end

    subgraph Validate["6. Validate & Score"]
        Confidence["Calculate Confidence"]
        Route["Route Decision"]
    end

    subgraph Persist["7. Persist"]
        Results["Cosmos DB<br/>(results)"]
        Audit["Audit Log"]
    end

    SB --> Trigger
    Trigger --> Blob
    Trigger --> Metadata
    Blob --> ACU
    ACU --> DocType
    DocType --> Schema
    DocType --> Model
    DocType --> Prompt
    Schema --> AOAI
    Model --> AOAI
    Prompt --> AOAI
    AOAI --> DocIntel
    DocIntel --> Confidence
    Confidence --> Route
    Route --> Results
    Route --> Audit
```

### 3. Data Model

```mermaid
erDiagram
    DOCUMENT_TYPES ||--o{ EXTRACTION_SCHEMAS : has
    DOCUMENT_TYPES ||--o{ PROMPTS : has
    EXTRACTION_SCHEMAS ||--o{ EXTRACTION_MODELS : uses
    DOCUMENTS ||--o{ EXTRACTION_RESULTS : produces
    DOCUMENTS }o--|| DOCUMENT_TYPES : classified_as
    EXTRACTION_RESULTS }o--|| EXTRACTION_SCHEMAS : uses
    AUDIT_LOGS }o--|| DOCUMENTS : tracks

    DOCUMENT_TYPES {
        string type_id PK
        string name
        string description
        boolean is_active
        datetime created_at
    }

    EXTRACTION_SCHEMAS {
        string schema_id PK
        string type_id FK
        string version
        object input_schema
        object output_schema
        float confidence_threshold
        boolean is_active
    }

    EXTRACTION_MODELS {
        string model_id PK
        string name
        string deployment_name
        string api_version
        object config
    }

    PROMPTS {
        string prompt_id PK
        string type_id FK
        string version
        string system_prompt
        string user_prompt_template
        boolean is_active
    }

    DOCUMENTS {
        string document_id PK
        string type_id FK
        string source
        string blob_path
        string status
        datetime received_at
        datetime processed_at
    }

    EXTRACTION_RESULTS {
        string result_id PK
        string document_id FK
        string schema_id FK
        object extracted_data
        object citations
        float confidence_score
        string review_status
    }

    AUDIT_LOGS {
        string log_id PK
        string document_id FK
        string action
        string actor
        object details
        datetime timestamp
    }
```

## Azure Services Selection

| Service | Choice | Rationale |
|---------|--------|-----------|
| **Compute** | Azure Functions (Consumption) | Pay-per-execution; scales to zero; cost-effective for async |
| **API Gateway** | API Management (Consumption) | Pay-per-call; built-in rate limiting |
| **Message Queue** | Service Bus (Standard) | Reliable delivery; dead-letter support; sessions for ordering |
| **Database** | Cosmos DB (Serverless) | Pay-per-RU; auto-scale; rich querying; global distribution ready |
| **File Storage** | Blob Storage (Standard) | Cost-effective; lifecycle management |
| **AI - Extraction** | Azure OpenAI (Pay-as-you-go) | GPT-4.1 for intelligent extraction |
| **AI - Classification** | Content Understanding | Document type detection |
| **AI - Citations** | Document Intelligence | OCR, layout, bounding boxes |
| **Monitoring** | Azure Monitor + App Insights | Centralized logging; audit trail |

## Cost Optimization

| Strategy | Implementation |
|----------|----------------|
| **Scale to Zero** | Functions Consumption plan; no idle costs |
| **Serverless DB** | Cosmos DB Serverless; pay only for operations |
| **Tiered Storage** | Hot → Cool → Archive lifecycle policies |
| **Batch Processing** | Group documents; reduce function invocations |
| **Caching** | Cache schemas/prompts; reduce Cosmos reads |
| **Reserved AI** | Consider PTU if volume grows predictably |

### Estimated Monthly Cost (Low Volume)

| Service | Estimated Cost |
|---------|----------------|
| Azure Functions | ~$20 (1000 docs/day) |
| Cosmos DB Serverless | ~$50-100 |
| Blob Storage | ~$10 |
| Service Bus | ~$10 |
| Azure OpenAI | ~$100-300 (depends on doc size) |
| Document Intelligence | ~$50-100 |
| API Management | ~$30 |
| **Total** | **~$300-600/month** |

*Note: Actual costs depend on document volume and size*

## Compliance & Audit

### HK Data Regulations

| Requirement | Implementation |
|-------------|----------------|
| **Data Residency** | All services deployed in East Asia / Southeast Asia |
| **Encryption at Rest** | Azure-managed keys (AES-256) |
| **Encryption in Transit** | TLS 1.3 enforced |
| **Access Control** | Managed Identity; no stored credentials |
| **Audit Logging** | All operations logged to Cosmos DB + Azure Monitor |

### Audit Log Schema

```json
{
  "log_id": "uuid",
  "timestamp": "2026-01-18T10:30:00Z",
  "document_id": "doc-123",
  "action": "extraction_completed",
  "actor": "system/function-app",
  "details": {
    "schema_version": "1.2.0",
    "model_used": "gpt-4.1",
    "prompt_version": "2.0.0",
    "confidence_score": 0.92,
    "processing_time_ms": 4500
  },
  "source_ip": "10.0.0.1",
  "correlation_id": "corr-456"
}
```

## Pull API for Downstream

```mermaid
sequenceDiagram
    participant DS as Downstream System
    participant API as Platform API
    participant Cosmos as Cosmos DB

    DS->>API: GET /extractions?status=completed&since=timestamp
    API->>Cosmos: Query results
    Cosmos-->>API: Results array
    API-->>DS: JSON response

    DS->>API: GET /extractions/{id}
    API->>Cosmos: Get by ID
    Cosmos-->>API: Full extraction + citations
    API-->>DS: JSON response

    DS->>API: PATCH /extractions/{id}/status
    Note over API: Mark as consumed/processed
    API->>Cosmos: Update status
    API-->>DS: 200 OK
```

### Pull API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extractions` | GET | List extractions (filter by status, date, type) |
| `/extractions/{id}` | GET | Get single extraction with full details |
| `/extractions/{id}/document` | GET | Get original document (SAS URL) |
| `/extractions/{id}/status` | PATCH | Update status (consumed, reviewed) |

## Platform Extensibility

### Adding New Document Type (No Code Deployment)

```mermaid
flowchart LR
    subgraph UI["Admin UI"]
        Upload["1. Upload Sample"]
        Classify["2. Auto-Classify"]
        Schema["3. Define Schema"]
        Prompt["4. Configure Prompt"]
        Test["5. Test Extraction"]
        Publish["6. Publish"]
    end

    subgraph DB["Cosmos DB"]
        TypeStore["document_types"]
        SchemaStore["extraction_schemas"]
        PromptStore["prompts"]
    end

    Upload --> Classify --> Schema --> Prompt --> Test --> Publish
    Publish --> TypeStore
    Publish --> SchemaStore
    Publish --> PromptStore
```

### Future Extensions

| Extension | Effort | Notes |
|-----------|--------|-------|
| New document type | Hours | Self-service via UI |
| New extraction model | Config change | Add to model registry |
| New region | Medium | Deploy same infra via Bicep |
| Multi-tenant | Medium | Partition by tenant in Cosmos |
| Real-time processing | Low | Add Event Grid trigger |

## Deployment

### Infrastructure as Code (Bicep)

```
infrastructure/
├── main.bicep
├── main.bicepparam
├── modules/
│   ├── functions.bicep
│   ├── cosmos.bicep
│   ├── servicebus.bicep
│   ├── storage.bicep
│   ├── apim.bicep
│   └── monitoring.bicep
```

### CI/CD Pipeline

```mermaid
flowchart LR
    subgraph Dev["Development"]
        Code["Code Commit"]
        Build["Build"]
        Test["Unit Tests"]
    end

    subgraph Deploy["Deployment"]
        DevEnv["Dev Environment"]
        StagingEnv["Staging"]
        ProdEnv["Production"]
    end

    Code --> Build --> Test
    Test --> DevEnv
    DevEnv -->|Manual Approval| StagingEnv
    StagingEnv -->|Manual Approval| ProdEnv
```

## Migration Path from POC

| POC Component | Production Change |
|---------------|-------------------|
| FastAPI on App Service | Azure Functions (Consumption) |
| Vue Frontend | Keep as Static Web App |
| Cosmos DB | Keep, ensure Serverless tier |
| Blob Storage | Keep, add lifecycle policies |
| Azure OpenAI | Keep, monitor quota |
| Service Bus | Add for async processing |
| API Management | Add for gateway/throttling |

---

*Architecture Version: 2.0 (Production)*  
*Last Updated: January 2026*  
*Region: East Asia*
