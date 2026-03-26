---
title: "Pipeline Orchestrator: Architecture Proposal"
description: >
  Architecture proposal for a YAML-driven pipeline orchestrator for document processing.
  Intended for architectural review and decision-making.
author: HSBC AI Engineering
ms.date: 2026-03-26
ms.topic: concept
keywords:
  - pipeline orchestrator
  - architecture decision
  - insurance underwriting
  - claims processing
  - azure durable functions
---

## Executive Summary

This proposal introduces a configurable pipeline orchestrator that coordinates existing document
processing services (classification, OCR, NER) into reusable, YAML-defined pipelines. The
orchestrator is a new layer that wraps existing services as thin adapter steps. It does not modify
any existing service, processor, or utility code.

The system handles two request types today:

* **DocumentSummary**: classifies a single attachment, extracts text via OCR, and sends the
  result to a downstream front-end API.
* **CaseSummary**: collects previously extracted OCR outputs for multiple attachments from blob
  storage, runs NER across all of them, and sends the aggregated result.

These are modeled as two separate YAML pipelines triggered by the `requestType` field in the
incoming queue message. CaseSummary is always a separate upstream call that arrives after all
DocumentSummary runs for a case have completed.

Each use case (insurance underwriting, claims processing) runs on its own Azure Function App with
separate infrastructure.

## Problem Statement

The existing orchestration in `function_queue_durable.py` has these limitations:

| Problem | Impact |
|---------|--------|
| Classification and OCR are fused in a single activity | Cannot scale OCR independently of classification |
| Adding a new step requires editing the orchestrator function directly | Every new capability (summarization, fraud detection) needs code changes |
| Request-type branching is hardcoded `if/elif` logic | Pipeline structure modifications require code deployments |
| No standard failure policies or step-level timing | Inconsistent error handling across processing steps |
| Each new workflow requires a new activity function and wiring changes | High development overhead for new use cases |


## Proposed Architecture

### Layered View

[!Layered Architecture](./layered-architecture.png)

### Core Concepts

| Concept | Description |
|---------|-------------|
| Step | A class with a single async `execute(context) → context` method. Wraps an existing service. Has no knowledge of which pipeline it belongs to. |
| Stage | A named group of one or more steps defined in YAML. Steps within a stage run in parallel when `parallel: true` is set. Stages run sequentially. |
| PipelineContext | A dataclass that flows through every step. Carries message fields, the payload array of attachments, accumulated step results, errors, and a correlation ID. |
| StepRegistry | A singleton mapping `(step_name, version)` tuples to step classes. Steps self-register via a decorator at import time. |
| PipelineEngine | Reads a pipeline definition from YAML, resolves steps from the registry, executes stages in order. Parallel stages use `asyncio.gather`; sequential stages iterate one step at a time. |
| Durable Functions Adapter | Wraps the PipelineEngine for Azure Durable Functions. Each step becomes a `call_activity`. Parallel stages use `task_all` (fan-out/fan-in). Provides retry, checkpointing, and timeout management. |

### Message Schema

The incoming queue message uses the existing format. The orchestrator reads `requestType` to
select which YAML pipeline to execute.

```json
{
  "requestType": "DocumentSummary",
  "messageId": "msg-001",
  "timestamp": "2026-03-26T10:00:00Z",
  "recordId": "rec-123",
  "payload": [
    {
      "attachmentId": "att-456",
      "urlOfContainer": "https://storage.blob.core.windows.net/incoming/doc.pdf"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `requestType` | Selects the pipeline: `DocumentSummary` or `CaseSummary` |
| `messageId` | Correlation ID for tracing and telemetry |
| `timestamp` | Message creation time |
| `recordId` | Business record identifier |
| `payload` | Array of attachments. DocumentSummary has one; CaseSummary has many. |

### Pipeline Routing

A configurable map replaces the existing hardcoded `if/elif` branching:

| Request Type | Pipeline Name |
|--------------|---------------|
| `DocumentSummary` | `document_summary` |
| `CaseSummary` | `case_summary` |

This map can be overridden per Function App via app settings for different use cases.

## Request Flows

### DocumentSummary Pipeline

```text
Queue message arrives
    │
    ▼
Stage 1: classify (sequential)
    └─ ClassificationStep
       ├─ Copy blob from incoming container to src-raw-doc
       ├─ ClassifierService → DOCOutput
       └─ Write serialized DOCOutput to pipeline context
    │
    ▼
Stage 2: extract (sequential)
    └─ OcrStep
       ├─ Read DOCOutput from pipeline context
       ├─ Route to OCRService or OCRAutoService (config-driven)
       ├─ Produce OCROutput
       └─ Persist document-output.json to blob storage
    │
    ▼
Stage 3: deliver (sequential)
    └─ SendStep
       ├─ Retrieve function key from Key Vault
       └─ POST OCR result to front-end API
```

### CaseSummary Pipeline

```text
Queue message arrives (multiple attachments)
    │
    ▼
Stage 1: analyze (sequential)
    └─ NerStep
       ├─ For each attachmentId in payload:
       │   └─ Read document-output.json from blob storage
       ├─ Assemble all OCR outputs into NERInput
       └─ NERService → NEROutput
    │
    ▼
Stage 2: deliver (sequential)
    └─ SendStep
       ├─ Retrieve function key from Key Vault
       └─ POST NER result to front-end API
```

### Data Flow Through Pipeline Context

**DocumentSummary**:

| After Stage | Context Contents |
|-------------|------------------|
| classify | `step_results["classification"]` = serialized DOCOutput (doc_type, confidence, etc.) |
| extract | `step_results["ocr"]` = OCROutput with summary_json |
| deliver | `step_results["send"]` = delivery status and message_id |

**CaseSummary**:

| After Stage | Context Contents |
|-------------|------------------|
| analyze | `step_results["ner"]` = NEROutput with aggregated entities |
| deliver | `step_results["send"]` = delivery status and message_id |

## Step Inventory

| Step | Version | Scope | Wraps | Responsibility |
|------|---------|-------|-------|----------------|
| classification | v3 | Shared | ClassifierService | Blob copy from incoming to internal container, classify document, produce DOCOutput |
| ocr | v2 | Shared | OCRService / OCRAutoService | Read DOCOutput from context, route to legacy or auto processor via config, produce OCROutput, persist to blob |
| ner | v1 | Shared | NERService | Read OCR outputs from blob storage for each attachment, assemble NERInput, produce NEROutput |
| send | v1 | Shared | Key Vault + HTTP POST | Read result from context, retrieve function key, POST to configurable front-end endpoint |
| fraud_detection | v1 | Claims only | OpenAI | Score document for fraud indicators, produce risk score and flags |

### Classification and OCR Split

The key architectural change is splitting the current fused activity into two independent steps.

**Current state**: A single activity performs blob copy + classification + OCR extraction.

**Proposed state**: Classification (with blob copy) and OCR are separate `call_activity`
invocations, connected through serialized `DOCOutput` in the pipeline context.

**Benefits**:

* OCR can scale independently (scheduled on a different compute instance)
* Future multi-attachment DocumentSummary can run OCR in parallel via `task_all`
* Each step has focused responsibility, simplifying testing

**Tradeoff**: One extra Durable Functions checkpoint between classification and OCR. For documents
requiring 5-30 seconds of OCR processing, this overhead (typically 50-100ms) is negligible.

### OCR Processor Routing

The OCR step uses a config-driven `legacy_doc_types` list to route documents:

* Document types in the list route to the legacy `OCRService` (per-type processors)
* All other types route to `OCRAutoService` (common processor with prompt-based extraction)
* As document types are migrated, remove them from the list
* When the list is empty, the legacy path can be retired

## YAML Pipeline Configuration

### Failure Policies

Each step supports an `on_failure` field:

| Policy | Behavior |
|--------|----------|
| `stop` | Halt the entire pipeline immediately (default) |
| `skip` | Log the error and continue. Downstream steps must handle missing inputs. |
| `retry` | Retry up to 3 times with exponential backoff before applying fallback (stop or skip) |

### DocumentSummary (Underwriting)

```yaml
pipeline:
  name: document_summary
  version: "1.0"
  description: "Single-document classification, OCR extraction, and delivery"

  stages:
    - name: classify
      steps:
        - name: classification
          version: v3
          on_failure: stop

    - name: extract
      steps:
        - name: ocr
          version: v2
          on_failure: stop

    - name: deliver
      steps:
        - name: send
          version: v1
          config:
            result_key: ocr
```

### CaseSummary (Underwriting)

```yaml
pipeline:
  name: case_summary
  version: "1.0"
  description: "Multi-attachment NER extraction and delivery"

  stages:
    - name: analyze
      steps:
        - name: ner
          version: v1
          on_failure: stop

    - name: deliver
      steps:
        - name: send
          version: v1
          config:
            result_key: ner
```

### DocumentSummary (Claims)

```yaml
pipeline:
  name: document_summary_claims
  version: "1.0"
  description: "Claims document processing with fraud detection"

  stages:
    - name: classify
      steps:
        - name: classification
          version: v3
          on_failure: stop

    - name: extract
      steps:
        - name: ocr
          version: v2
          on_failure: stop

    - name: fraud
      steps:
        - name: fraud_detection
          version: v1
          on_failure: skip

    - name: deliver
      steps:
        - name: send
          version: v1
          config:
            result_key: ocr
            url: "${CLAIMS_FRONT_END_URL}"
            key_vault_url: "${CLAIMS_KEY_VAULT_URL}"
            secret_name: "${CLAIMS_SECRET_NAME}"
```

The claims pipeline demonstrates:

* An additional fraud detection stage inserted between extract and deliver
* `on_failure: skip` so fraud detection failures do not block document delivery
* Configurable send endpoint via environment variables specific to the claims Function App

### CaseSummary (Claims)

```yaml
pipeline:
  name: case_summary_claims
  version: "1.0"
  description: "Claims multi-attachment NER with fraud scoring and delivery"

  stages:
    - name: analyze
      steps:
        - name: ner
          version: v1
          on_failure: stop

    - name: deliver
      steps:
        - name: send
          version: v1
          config:
            result_key: ner
            url: "${CLAIMS_FRONT_END_URL}"
            key_vault_url: "${CLAIMS_KEY_VAULT_URL}"
            secret_name: "${CLAIMS_SECRET_NAME}"
```

## Infrastructure Model

### Separate Function Apps Per Use Case

```text
┌─────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
│  Function App: Underwriting             │  │  Function App: Claims                   │
│                                         │  │                                         │
│  Queue: {queue_name}durable             │  │  Queue: {queue_name}durable             │
│    ▼                                    │  │    ▼                                    │
│  pipeline_orchestrator                  │  │  pipeline_orchestrator                  │
│    ▼                                    │  │    ▼                                    │
│  document_summary.yaml                  │  │  document_summary_claims.yaml           │
│  case_summary.yaml                      │  │  case_summary_claims.yaml               │
│                                         │  │                                         │
│  Storage: uw-ai-sa                      │  │  Storage: claims-sa                     │
│  Plan: uw-ai-plan                       │  │  Plan: claims-plan                      │
│  App Insights: uw-ai-ai                 │  │  App Insights: claims-ai                │
└─────────────────────────────────────────┘  └─────────────────────────────────────────┘
```

Both Function Apps deploy from the same source repository. The `PIPELINE_MAP` app setting routes
`requestType` values to different YAML files per deployment.

### Infrastructure Per Use Case

| Resource | Underwriting | Claims |
|----------|-------------|--------|
| Function App | uw-ai-func | claims-func |
| Storage Account | uw-ai-sa | claims-sa |
| App Service Plan | uw-ai-plan | claims-plan |
| Application Insights | uw-ai-ai | claims-ai |
| VNet integration | Separate | Separate |

**Why separate infrastructure?**

* Fault isolation: a scaling event or outage in one use case does not affect the other
* Independent scaling: claims processing may have different throughput requirements
* Environment-specific configuration: each Function App has its own app settings and connection
  strings without cross-contamination
* Compliance boundaries: separate infrastructure simplifies audit trails and access control

### Deployment Model

```text
Source Repository (shared codebase)
├── function_app.py
├── function_queue_durable.py
├── requirements.txt
├── Pipelines/
│   ├── func-app-deploy-uw-ai-*.yml       (deploys to underwriting)
│   └── func-app-deploy-claims-*.yml      (deploys to claims)
└── src/
    ├── services/       (unchanged)
    ├── processors/     (unchanged)
    ├── utils/          (unchanged)
    ├── schemas/        (unchanged)
    └── orchestrator/   (new)
        ├── Framework files (engine, registry, context, config)
        ├── steps/      (classification, ocr, ner, send, fraud_detection)
        └── pipelines/  (YAML configs per use case)
```

### CI/CD Pipelines

| Pipeline | Target |
|----------|--------|
| func-app-deploy-uw-ai-sit/uat/prod.yml | Underwriting (existing) |
| func-app-deploy-claims-sit/uat/prod.yml | Claims (new) |

## Key Design Decisions

### 1. Split classification and OCR into separate steps

Classification (with blob copy) and OCR become independent activity functions. This enables OCR
to scale on separate compute instances and supports future parallel OCR for multi-attachment
scenarios. The tradeoff is one extra Durable Functions checkpoint (approximately 50-100ms).

### 2. Blob copy inside classification, not a separate step

Blob copy always precedes classification and has no standalone reuse value. A separate step would
add a checkpoint round-trip for zero benefit.

### 3. Two pipelines per request type, not conditional stages

DocumentSummary and CaseSummary have fundamentally different step sequences. CaseSummary skips
classification and OCR entirely. Modeling this as a single pipeline with conditions would add
complexity for no benefit.

### 4. NER handles multi-attachment assembly internally

The NER step iterates the payload, reads each attachment's OCR output from blob storage, and
assembles a single NER input. This matches existing behavior exactly and avoids large intermediate
data flowing through pipeline context serialization.

### 5. Configurable send step over hardcoded endpoints

The send step reads its target URL, Key Vault URL, and secret name from the YAML config block.
Defaults fall back to application settings. This enables claims pipelines to send results to a
different front-end API through configuration alone.

### 6. Queue trigger as primary entry point

The existing system receives work via queue messages. The orchestrator preserves this pattern. An
HTTP trigger can be added later for testing or direct invocation.

### 7. Stage-based parallelism over full DAG

Steps within a stage can run in parallel. Stages themselves always run sequentially. This avoids
DAG complexity, topological sorting, and cycle detection. The engine can be extended to support
full DAG later if needed.

### 8. YAML for pipeline configuration

Non-developers can read and modify pipeline structure. Version-control friendly with meaningful
diffs. Separates "what to run" (YAML) from "how to run" (engine code).

### 9. Config-driven OCR processor routing

A `legacy_doc_types` list in YAML determines routing between legacy per-type processors and the
auto processor. Remove types from the list as they migrate. When the list is empty, retire the
legacy path.

### 10. Separate infrastructure, shared codebase

Each use case runs on its own Function App. The same source deploys to all Function Apps; only
app settings differ. This provides fault isolation, independent scaling, and compliance boundaries.

## Adding a New Use Case

To add a new use case (e.g., credit underwriting):

1. Write any new step classes with the `@register_step` decorator
2. Create new YAML pipeline files composing shared and new steps
3. Add `requestType` → pipeline name entries to the routing map
4. Provision a new Function App with its own infrastructure
5. Create CI/CD pipeline files targeting the new Function App
6. Deploy through the new pipeline

No changes required to the orchestrator framework, existing steps, or services.


## Risks and Considerations

| Risk | Mitigation |
|------|------------|
| DOCOutput serialization between classification and OCR | All fields are already JSON-serializable (verified in existing code). Add serialization round-trip tests. |
| PipelineContext must be JSON-serializable across activity boundaries | Design context with primitive and dict types only. Each step re-establishes its own connections. |
| NER reads from blob storage, not from pipeline context | By design. Blob storage is the interface between DocumentSummary and CaseSummary pipelines. |
| OCR step must persist output to blob storage | Required for downstream CaseSummary NER. If OCR only wrote to context, the CaseSummary path would break. |
| YAML config errors surface at invocation, not deploy time | Add a startup validation hook that loads and validates all configs on cold start. |
| Durable Functions replay behavior | Orchestrator must be deterministic (no datetime.now, no I/O). All non-deterministic work belongs in activity functions. |
| Cold start latency with step auto-discovery | Profile cold start after adding more than 20 step files. |
| Infrastructure drift between Function Apps | Maintain shared IaC templates with environment-specific parameter files. Add CI validation for app settings parity. |


