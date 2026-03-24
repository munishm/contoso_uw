---
title: Orchestrator High-Level Design
description: >
  High-level design for a YAML-driven, configurable pipeline orchestrator that introduces a new
  coordination layer on top of existing services and processors, supporting claims processing,
  insurance underwriting, and future use cases without modifying existing code.
author: HSBC AI Engineering
ms.date: 2026-03-25
ms.topic: concept
keywords:
  - pipeline orchestrator
  - claims processing
  - insurance underwriting
  - azure durable functions
  - high-level design
---


This document proposes a configurable pipeline orchestrator that coordinates our existing document
processing services (classification, OCR, NER) into reusable, YAML-defined pipelines. The
orchestrator is a new layer; it does not restructure or modify any existing service, processor, or
utility code. It wraps them as thin adapter "steps" and composes those steps into pipelines driven
by configuration files.

The initial scope covers two use cases: **insurance underwriting** (classification, extraction,
and summarization) and **claims processing** (classification, extraction,
summarization, and fraud detection). Adding a new use case (e.g., credit underwriting, insurance re-evaluation)
requires writing only the use-case-specific step classes and a new YAML file. No changes to the orchestrator, shared steps,
existing services, or Azure Function infrastructure are needed.

A single Azure Durable Functions orchestrator handles all pipelines. The YAML config determines
which steps run, in what order, and whether they execute sequentially or in parallel.

## Problem Statement

Today each document processing workflow is wired directly in Azure Function entry points. Adding a
new use case means writing new function code, duplicating service calls, and managing execution
order manually. This approach does not scale:

* Shared capabilities (classification, OCR, NER) are re-implemented per workflow instead of reused.
* No standard interface exists for processing steps, making them hard to compose and test.
* Adding parallel execution or failure policies requires custom code per workflow.
* There is no way for a non-developer to understand or modify a pipeline's structure.

## Proposed Solution

Introduce a new `src/orchestrator/` package that sits between the Azure Function triggers and the
existing services layer:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        Azure Function Triggers                      │
│   function_http.py    function_queue_durable.py    function_app.py  │
│                    (additive changes only)                          │
├─────────────────────────────────────────────────────────────────────┤
│                     NEW: Orchestrator Layer                          │
│                                                                     │
│   YAML Config ──► PipelineFactory ──► PipelineEngine                │
│                                           │                         │
│                               ┌───────────┼───────────┐             │
│                               ▼           ▼           ▼             │
│                          Step A       Step B      Step C            │
│                        (classify)    (OCR)      (fraud)             │
│                     thin adapters wrapping existing services         │
├─────────────────────────────────────────────────────────────────────┤
│                   EXISTING: Services Layer (UNCHANGED)               │
│   classifier_service.py   ocr_service.py   ocr_service_auto.py     │
│   ner_service.py                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                   EXISTING: Processors Layer (UNCHANGED)             │
│   classifier_processors/   ocr_processors/   ocr_processors_auto/   │
│   ner_processors/                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                   EXISTING: Utilities Layer (UNCHANGED)              │
│   open_ai.py   storage_blob.py   document_intelligence.py   ...    │
└─────────────────────────────────────────────────────────────────────┘
```

## Impact on Existing Code

### What does NOT change

The following directories and files remain untouched. No refactoring, no interface changes, no
behavioral modifications:

| Layer      | Path                                    | Status      |
|------------|-----------------------------------------|-------------|
| Services   | `src/services/classifier_service.py`    | No change   |
| Services   | `src/services/ner_service.py`           | No change   |
| Services   | `src/services/ocr_service.py`           | No change   |
| Services   | `src/services/ocr_service_auto.py`      | No change   |
| Processors | `src/processors/classifier_processors/` | No change   |
| Processors | `src/processors/ner_processors/`        | No change   |
| Processors | `src/processors/ocr_processors/`        | No change   |
| Processors | `src/processors/ocr_processors_auto/`   | No change   |
| Utilities  | `src/utils/` (all files)                | No change   |
| Schemas    | `src/schemas/` (all files)              | No change   |
| Config     | `src/config/settings.py`                | No change   |
| Config     | `src/config/global_versions.yaml`       | No change   |
| Prompts    | `prompt/` (all directories)             | No change   |
| Tests      | `test/` (existing tests)                | No change   |
| Pipelines  | `Pipelines/` (CI/CD YAML)              | No change   |
| Scripts    | `scripts/` (all files)                  | No change   |

### What gets additive changes (4 existing files)

These files receive new code alongside their current content. Existing routes, triggers, and
functionality remain intact.

| File                        | What is added                                                               |
|-----------------------------|-----------------------------------------------------------------------------|
| `function_http.py`          | One new HTTP trigger route: `POST /api/pipeline` to launch a named pipeline |
| `function_queue_durable.py` | One orchestrator function and one generic activity function registration     |
| `function_app.py`           | Blueprint registration for the new orchestrator functions                    |
| `requirements.txt`          | One new dependency: `pyyaml`                                                |

### What is entirely new (21 files)

All new code lives under `src/orchestrator/` and `test/orchestrator/`. These directories do not
exist today.

## Architecture

### Core Concepts

* **Step**: A Python class implementing `BaseStep` with a single async method
  `execute(context) -> context`. Each step reads inputs from the pipeline context, delegates to an
  existing service or utility, and writes its output back. Steps have no knowledge of which pipeline
  they belong to.

* **Stage**: A named group of one or more steps defined in YAML. Steps within a stage run in
  parallel when `parallel: true` is set. Stages themselves run sequentially. This provides
  parallelism without the complexity of a full DAG.

* **PipelineContext**: A dataclass that flows through every step. It carries the document
  identifier, blob path, metadata, accumulated step results (keyed by step name), error list, and
  correlation ID for tracing.

* **StepRegistry**: A singleton mapping `(step_name, version)` tuples to step classes. Steps
  self-register via a `@register_step("name", "version")` decorator at import time. The registry
  auto-discovers all modules in `src/orchestrator/steps/` on app startup.

* **PipelineEngine**: Reads a `PipelineDefinition` (parsed from YAML), resolves each step from the
  registry, and executes stages in order. Parallel stages use `asyncio.gather`; sequential stages
  iterate one step at a time. Each step's timing, status, and errors are recorded in context.

* **Durable Functions Adapter**: Wraps the `PipelineEngine` for Azure Durable Functions. Each step
  becomes a `call_activity` invocation. Parallel stages use `task_all` (fan-out/fan-in). This
  provides retry, checkpointing, and timeout management for long-running pipelines.

### Request Flow

```text
1. HTTP POST /api/pipeline
   Body: { "pipeline_name": "claims_processing", "document_id": "abc", "blob_path": "..." }

2. function_http.py validates the request and starts a durable orchestration

3. The durable orchestrator:
   a. Loads claims_processing.yaml
   b. Resolves all step classes from the registry
   c. Creates a PipelineContext with the document_id, blob_path, and metadata

4. Stage 1 (classify):
   └─ call_activity("execute_step", { step: "classification", version: "v3", context: ... })
      └─ ClassificationStep.execute() calls classifier_service.py
      └─ Writes result to context.step_results["classification"]

5. Stage 2 (extract):
   └─ call_activity("execute_step", { step: "ocr", version: "v2", context: ... })
      └─ OcrStep.execute() routes to ocr_service_auto.py or ocr_service.py
         based on legacy_doc_types config
      └─ Writes result to context.step_results["ocr"]

6. Stage 3 (analyze):
   └─ call_activity("execute_step", { step: "ner", version: "v1", context: ... })
      └─ NerStep.execute() calls ner_service.py

7. Stage 4 (fraud):
   └─ call_activity("execute_step", { step: "fraud_detection", version: "v1", context: ... })
      └─ FraudDetectionStep.execute() calls open_ai.py with fraud prompt
      └─ Uses classification, OCR text, and NER entities for analysis

8. Stage 5 (summarize):
   └─ call_activity("execute_step", { step: "summarization", version: "v1", context: ... })
      └─ SummarizationStep.execute() calls open_ai.py

9. Return final PipelineContext with all step results
```

### One Orchestrator, Many Pipelines

There is one durable orchestrator function, not a separate one per use case. The `pipeline_name`
parameter determines which YAML config to load, and the YAML determines which steps run.

```text
POST /api/pipeline  { "pipeline_name": "claims_processing" }
POST /api/pipeline  { "pipeline_name": "insurance_underwriting" }
POST /api/pipeline  { "pipeline_name": "credit_underwriting" }   ← future use case
                          │
                    Same orchestrator function
                          │
               ┌──────────┴──────────────────┐
               ▼                ▼                 ▼
    claims_processing.yaml   insurance_underwriting.yaml   credit_underwriting.yaml
```

### Adding a New Use Case

To add a new use case (e.g., credit underwriting):

1. Write any new step classes in `src/orchestrator/steps/` (e.g., `credit_scoring.py`,
   `income_verification.py`) with `@register_step` decorators
2. Create a new YAML file `src/orchestrator/pipelines/credit_underwriting.yaml` composing shared
   and new steps
3. Deploy the function app through the existing CI/CD pipeline (same as any other code change)

No changes required to the orchestrator, existing steps, services, or Azure Functions infrastructure.
The step registry auto-discovers the new classes on app restart.

## Step Definitions

Each step class follows the same pattern: read from context, delegate to an existing service, write
back to context. Below is the concrete definition for every step.

### Shared Steps (reused across all pipelines)

#### Classification Step

`src/orchestrator/steps/classification.py` wraps `src/services/classifier_service.py`.

```python
@register_step("classification", "v3")
class ClassificationStep(BaseStep):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        result = await classify_document(
            blob_path=context.blob_path,
            metadata=context.metadata,
        )
        context.step_results["classification"] = result
        return context
```

Reads the document from blob storage, classifies it using the v3 classifier processor, and writes
the document category (e.g., "claim_form", "medical_report") to context.

#### OCR Step

`src/orchestrator/steps/ocr.py` wraps both `src/services/ocr_service_auto.py` and
`src/services/ocr_service.py`. The step uses config-driven routing to determine which processor
handles each document type.

The codebase has two OCR processor paths:

* **`ocr_processors_auto`** — A prompt-driven, config-based generic processor that handles most
  document types through `ocr_service_auto.py`.
* **`ocr_processors`** — Legacy per-type processors with dedicated subdirectories for each document
  type (e.g., `claim_form/`, `medical_report/`), served through `ocr_service.py`.

The OCR step routes document types to the appropriate processor based on a `legacy_doc_types` list
in the YAML pipeline config. Document types in the list use the legacy processor; all others use
the auto processor.

```python
@register_step("ocr", "v2")
class OcrStep(BaseStep):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        doc_type = context.step_results.get("classification", {}).get("category")
        legacy_doc_types = self.config.get("legacy_doc_types", [])

        if doc_type in legacy_doc_types:
            result = await extract_text_legacy(
                blob_path=context.blob_path,
                doc_type=doc_type,
            )
        else:
            result = await extract_text_auto(
                blob_path=context.blob_path,
                doc_type=doc_type,
            )

        context.step_results["ocr"] = result
        return context
```

Calls Azure Document Intelligence to extract text, tables, and key-value pairs from document
images. Uses the classification result to select the appropriate OCR processor:

* If the document type appears in `legacy_doc_types`, the step delegates to
  `ocr_service.py` which routes to the matching per-type processor under `ocr_processors/`.
* Otherwise, the step delegates to `ocr_service_auto.py` which uses the generic
  `ocr_processors_auto/common_processor.py` with prompt-based extraction.

As document types are onboarded to `ocr_processors_auto`, remove them from the `legacy_doc_types`
list. When the list is empty, the legacy path can be retired entirely.

#### NER Step

`src/orchestrator/steps/ner.py` wraps `src/services/ner_service.py`.

```python
@register_step("ner", "v1")
class NerStep(BaseStep):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        entity_types = self.config.get("entity_types", None)
        result = await extract_entities(
            text=context.step_results["ocr"]["text"],
            entity_types=entity_types,
        )
        context.step_results["ner"] = result
        return context
```

Uses OpenAI to extract named entities from OCR text. The `config.entity_types` field in the YAML
controls which entities to extract (e.g., person, date, amount, policy_number).

#### Summarization Step

`src/orchestrator/steps/summarization.py` uses `src/utils/open_ai.py`.

```python
@register_step("summarization", "v1")
class SummarizationStep(BaseStep):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        result = await generate_summary(
            text=context.step_results["ocr"]["text"],
            entities=context.step_results.get("ner", {}),
        )
        context.step_results["summarization"] = result
        return context
```

Generates a structured document summary incorporating the extracted entities.

### Claims-Specific Steps

#### Fraud Detection Step

`src/orchestrator/steps/fraud_detection.py` is new business logic.

```python
@register_step("fraud_detection", "v1")
class FraudDetectionStep(BaseStep):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        result = await detect_fraud(
            classification=context.step_results.get("classification"),
            ocr_text=context.step_results.get("ocr", {}).get("text"),
            entities=context.step_results.get("ner", {}),
        )
        # result = { "risk_score": 0.82, "flags": ["duplicate_claim", "amount_mismatch"] }
        context.step_results["fraud_detection"] = result
        return context
```

Calls OpenAI with a fraud-detection prompt. Analyzes document content for anomalies,
inconsistencies, and known fraud patterns. Returns a risk score (0.0 to 1.0) and a set of flags.

## YAML Pipeline Configuration Format

Pipelines are defined in YAML files under `src/orchestrator/pipelines/`. Each file declares a
pipeline name, version, and an ordered list of stages. Each stage contains one or more steps.

### Failure Policies

Each step supports an `on_failure` field:

* `stop`: Halt the entire pipeline immediately (default).
* `skip`: Log the error and continue to the next step. The step's output slot in context remains
  empty. Downstream steps must handle missing inputs.
* `retry`: Retry the step up to 3 times with exponential backoff before applying the fallback
  policy (stop or skip).

### Claims Processing Pipeline

```yaml
# src/orchestrator/pipelines/claims_processing.yaml
pipeline:
  name: claims_processing
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
          config:
            legacy_doc_types:
              - heart_echo
              - ECG_report
              - MRI_report
              - ultrasound_report

    - name: analyze
      steps:
        - name: ner
          version: v1
          config:
            entity_types:
              - person
              - date
              - amount
              - policy_number

    - name: fraud
      steps:
        - name: fraud_detection
          version: v1
          on_failure: skip

    - name: summarize
      steps:
        - name: summarization
          version: v1
```

### Insurance Underwriting Pipeline

```yaml
# src/orchestrator/pipelines/insurance_underwriting.yaml
pipeline:
  name: insurance_underwriting
  version: "1.0"
  description: "Insurance underwriting document processing pipeline"

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
          config:
            legacy_doc_types:
              - heart_echo
              - ECG_report
              - MRI_report
              - ultrasound_report

    - name: analyze
      steps:
        - name: ner
          version: v1

    - name: summarize
      steps:
        - name: summarization
          version: v1
```

## New Files (complete inventory)

All new code resides in two directories that do not exist today.

### Framework (`src/orchestrator/`)

| File                                                    | Purpose                                                       |
|---------------------------------------------------------|---------------------------------------------------------------|
| `src/orchestrator/__init__.py`                          | Package initialization and public exports                     |
| `src/orchestrator/base_step.py`                         | Abstract `BaseStep` class with `execute()`, `validate_input()`, `on_error()` |
| `src/orchestrator/context.py`                           | `PipelineContext` dataclass: document_id, blob_path, metadata, step_results, errors |
| `src/orchestrator/registry.py`                          | `StepRegistry` singleton with `@register_step` decorator and auto-discovery |
| `src/orchestrator/config.py`                            | YAML parser producing `PipelineDefinition` dataclass with validation |
| `src/orchestrator/engine.py`                            | `PipelineEngine`: stage iteration, parallel dispatch, failure handling, timing |
| `src/orchestrator/durable.py`                           | Durable Functions adapter: `call_activity` per step, `task_all` for parallel stages |

### Steps (`src/orchestrator/steps/`)

| File                                                    | Scope             | Wraps                                    |
|---------------------------------------------------------|-------------------|------------------------------------------|
| `src/orchestrator/steps/__init__.py`                    | Auto-discovery    | Imports all step modules on startup       |
| `src/orchestrator/steps/classification.py`              | Shared            | `src/services/classifier_service.py`     |
| `src/orchestrator/steps/ocr.py`                         | Shared            | `src/services/ocr_service_auto.py` and `src/services/ocr_service.py` (config-driven routing) |
| `src/orchestrator/steps/ner.py`                         | Shared            | `src/services/ner_service.py`            |
| `src/orchestrator/steps/summarization.py`               | Shared            | `src/utils/open_ai.py`                   |
| `src/orchestrator/steps/fraud_detection.py`             | Claims only       | New logic using `src/utils/open_ai.py`   |

### Pipeline Configs (`src/orchestrator/pipelines/`)

| File                                                    | Use case            |
|---------------------------------------------------------|---------------------|
| `src/orchestrator/pipelines/claims_processing.yaml`     | Claims processing       |
| `src/orchestrator/pipelines/insurance_underwriting.yaml` | Insurance underwriting |

### Tests (`test/orchestrator/`)

| File                                                    | Coverage                                        |
|---------------------------------------------------------|-------------------------------------------------|
| `test/orchestrator/test_base_step.py`                   | Step interface contract and hook behavior        |
| `test/orchestrator/test_registry.py`                    | Registration, lookup, version resolution, errors |
| `test/orchestrator/test_config.py`                      | YAML parsing, validation, malformed input        |
| `test/orchestrator/test_engine.py`                      | Sequential/parallel execution, failure policies  |
| `test/orchestrator/test_pipelines.py`                   | End-to-end pipeline execution with mock services |

## Changes to Existing Files (detailed)

### `function_http.py`

Add one new route alongside existing routes. Existing HTTP triggers are not modified.

```python
# NEW: added alongside existing triggers
@app.route(route="pipeline", methods=["POST"])
async def start_pipeline(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    pipeline_name = body["pipeline_name"]
    document_id = body["document_id"]
    blob_path = body["blob_path"]

    instance_id = await client.start_new("pipeline_orchestrator", None, {
        "pipeline_name": pipeline_name,
        "document_id": document_id,
        "blob_path": blob_path,
    })
    return func.HttpResponse(json.dumps({"instance_id": instance_id}), status_code=202)
```

### `function_queue_durable.py`

Add one orchestrator function and one generic activity function. Existing durable functions are not
modified.

```python
# NEW: added alongside existing durable functions
@app.orchestration_trigger(binding="context")
def pipeline_orchestrator(context: df.DurableOrchestrationContext):
    input_data = context.get_input()
    # Loads YAML, resolves steps, executes stages via call_activity / task_all
    ...

@app.activity_trigger(input_name="payload")
async def execute_step(payload: dict) -> dict:
    # Resolves step class from registry, calls execute(), returns result
    ...
```

### `function_app.py`

Register the orchestrator blueprint. One line added.

```python
# NEW: added alongside existing blueprint registrations
app.register_functions(pipeline_orchestrator)
app.register_functions(execute_step)
```

### `requirements.txt`

One line added.

```text
pyyaml>=6.0
```

## Deployment Model

The function app deploys as a single unit. Every deployment includes the orchestrator, all
registered steps, and all YAML configs. There is no separate deployment per use case.

```text
Function App (single deployment artifact)
├── function_app.py
├── function_http.py
├── function_queue_durable.py
├── requirements.txt
└── src/
    ├── services/          (unchanged)
    ├── processors/        (unchanged)
    ├── utils/             (unchanged)
    ├── schemas/           (unchanged)
    └── orchestrator/      (new)
        ├── base_step.py
        ├── context.py
        ├── registry.py
        ├── config.py
        ├── engine.py
        ├── durable.py
        ├── steps/
        │   ├── classification.py
        │   ├── ocr.py
        │   ├── ner.py
        │   ├── summarization.py
        │   ├── fraud_detection.py
        │   └── summarization.py
        └── pipelines/
            ├── claims_processing.yaml
            └── insurance_underwriting.yaml
```

The deployment process does not change. The existing CI/CD pipelines
(`Pipelines/func-app-deploy-uw-ai-*.yml`) deploy the same function app. The new files are included
automatically because they are part of the source tree.

## Data Flow: PipelineContext

Every step reads from and writes to the same `PipelineContext` instance. Here is the state of
`step_results` at each stage boundary for the claims pipeline:

```text
After classify:
  step_results = {
    "classification": { "category": "claim_form", "confidence": 0.97 }
  }

After extract:
  step_results = {
    "classification": { ... },
    "ocr": { "text": "...", "tables": [...], "key_values": {...} }
  }

After analyze:
  step_results = {
    "classification": { ... },
    "ocr": { ... },
    "ner": { "person": "John Smith", "date": "2026-01-15", "amount": "$5,000" }
  }

After fraud:
  step_results = {
    "classification": { ... },
    "ocr": { ... },
    "ner": { ... },
    "fraud_detection": { "risk_score": 0.82, "flags": ["amount_mismatch"] }
  }

After summarize:
  step_results = {
    "classification": { ... },
    "ocr": { ... },
    "ner": { ... },
    "fraud_detection": { ... },
    "summarization": { "summary": "Claim form for John Smith dated ..." }
  }
```

## Reference Patterns in Existing Code

The orchestrator follows conventions already present in the codebase:

| Pattern              | Existing example                                        | Orchestrator equivalent               |
|----------------------|---------------------------------------------------------|---------------------------------------|
| Abstract base class  | `src/processors/classifier_processors/base_processor.py` | `src/orchestrator/base_step.py`       |
| Version-based loader | `src/processors/*/loader.py`                            | `src/orchestrator/registry.py`        |
| Request context      | `src/utils/request_context.py`                          | `PipelineContext.request_context`     |
| OpenAI integration   | `src/utils/open_ai.py`, `open_ai_dr.py`                 | Used by summarization, fraud steps    |
| Blob access          | `src/utils/storage_blob.py`                              | Used by classification, OCR steps     |
| Service delegation   | `src/services/classifier_service.py`                     | Wrapped by `ClassificationStep`       |
| Dual-processor routing | `ocr_processors/` and `ocr_processors_auto/`          | Config-driven `legacy_doc_types` routing in `OcrStep` |

## Design Decisions

### Class-based steps over plain functions

Aligns with the existing `base_processor.py` pattern. Supports versioning natively through the
`@register_step` decorator. Encapsulates per-step configuration. Enables dependency injection for
testing (mock the service, test the step in isolation).

### YAML for pipeline configuration

Non-developers can read and modify pipeline structure. Version-control friendly (diffs are
meaningful). Aligns with the existing `global_versions.yaml` convention. Separates "what to run"
(YAML) from "how to run" (Python engine).

### Stage-based parallelism over full DAG

Steps within a stage can run in parallel when `parallel: true` is set. Stages themselves always run
sequentially. The current use cases (claims and insurance underwriting) are fully sequential, but
the parallel capability is available for future use cases where independent steps can run
concurrently. This avoids introducing DAG complexity, topological sorting, or cycle detection. If
full DAG support becomes necessary, the engine can be extended without changing the step interface.

### Single orchestrator function

One durable orchestrator function handles all pipeline types. The `pipeline_name` parameter selects
the YAML config at runtime. This avoids function proliferation and keeps the deployment surface
area constant regardless of how many use cases we support.

### Step versions map to processor versions

`classification v3` resolves to `classifier_processors/v3/processor.py`. This maintains backward
compatibility as processors evolve and allows different pipelines to pin different versions of the
same step.

### Config-driven OCR processor routing

The codebase has two OCR processor paths: the newer `ocr_processors_auto` (generic, prompt-driven)
and the legacy `ocr_processors` (per-type subdirectories). Rather than maintaining two separate OCR
steps or hard-coding the routing logic, the OCR step reads a `legacy_doc_types` list from the YAML
pipeline config. Document types in the list route to `ocr_service.py` (legacy); all others route to
`ocr_service_auto.py` (auto). This approach:

* Keeps routing decisions in YAML where they are auditable and changeable without code
  modifications.
* Follows the same config-driven philosophy as the rest of the orchestrator.
* Provides a clear migration path: remove a document type from `legacy_doc_types` once it is
  onboarded to `ocr_processors_auto`. When the list is empty, the legacy path can be retired.
* Avoids runtime exception-based fallback, which would be harder to observe and debug.

## Verification Plan

1. Run `pytest test/orchestrator/` and confirm all framework unit tests pass.
2. Load `claims_processing.yaml` and verify all referenced steps resolve in the registry.
3. Execute the insurance underwriting pipeline with mock steps and verify sequential stage order.
4. Execute the claims pipeline and verify fraud_detection runs after NER extraction.
5. Trigger a step failure with `on_failure: stop` and confirm the pipeline halts.
6. Trigger a step failure with `on_failure: skip` and confirm the pipeline continues with an empty
   result slot.
7. Start the function app locally with `func start`, POST to the HTTP trigger with a pipeline
   name, and verify the durable orchestration completes end-to-end.
8. Register a new dummy step, add it to a YAML config, and confirm it runs without any changes to
   the orchestrator (extensibility check).

## Scope and Limitations

* Initial delivery covers claims processing and insurance underwriting only.
* No runtime dynamic pipeline modification (pipelines are defined at deploy time via YAML).
* No self-service UI for pipeline management.
* No cross-pipeline dependencies (one pipeline invocation processes one document).
* The orchestrator does not replace existing direct-call patterns in `function_http.py` or
  `function_queue.py`; those continue to work as-is for callers that do not use the pipeline API.

## Gotchas

### Serialization of PipelineContext across activity boundaries

Azure Durable Functions serialize activity inputs and outputs as JSON. `PipelineContext` and all
step results must be JSON-serializable. Custom objects, file handles, or database connections
cannot be passed through context. Each step must re-establish its own connections. Test
serialization early by round-tripping context through `json.dumps` / `json.loads` in unit tests.

### Step ordering within a non-parallel stage

Steps listed in a non-parallel stage execute top-to-bottom as written in YAML. If a step depends
on another step's output, the dependent step must be in a later stage. For example, fraud_detection
needs OCR text and NER entities, so it runs in its own stage after both extract and analyze. The
engine does not infer dependencies from step code.

### Handling fraud_detection failure gracefully

The fraud_detection step in the claims pipeline uses `on_failure: skip`. If it fails, the
pipeline continues to the summarization stage but `context.step_results["fraud_detection"]` will be
empty. Downstream steps or consumers of the final result must handle this case with defensive reads
(`context.step_results.get("fraud_detection", {})`).

### YAML config errors surface at pipeline load time, not deploy time

If a YAML file references a step name that does not exist in the registry, the error occurs when
the pipeline is first invoked, not when the function app starts. Consider adding a startup
validation hook in `function_app.py` that loads and validates all YAML configs on cold start to
catch misconfigurations earlier.

### Cold start latency with auto-discovery

The `steps/__init__.py` module imports all step modules to trigger `@register_step` decorators.
In a function app with many steps, this adds to cold start time. The impact is proportional to the
number of step files and their imports. Profile cold start after adding more than 20 step files.

### Durable Functions replay behavior

Azure Durable Functions orchestrators replay from the beginning on each checkpoint. The
orchestrator function must be deterministic: no `datetime.now()`, no random values, no I/O outside
of `call_activity`. All non-deterministic work belongs in activity functions (the step classes).
Review the Azure Durable Functions
[constraints on orchestrator code](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-code-constraints)
before implementing `src/orchestrator/durable.py`.

### Version mismatch between steps and processors

If a YAML file references `classification v4` but only `v3` exists in the registry, the error
message must clearly indicate the missing version. The registry lookup should raise a descriptive
`StepNotFoundError` with the requested name, version, and list of available versions.

### Shared step config variance across pipelines

The same step (e.g., `ner v1`) may need different `config` values in different pipelines (e.g.,
claims extracts `amount` and `policy_number`, while insurance underwriting extracts `address` and
`date_of_birth`). The YAML `config` block passes through to the step instance at execution time.
Steps must not rely on hardcoded configuration; they must read from `self.config` to support this
variance.

### OCR processor migration from legacy to auto

The OCR step routes document types to either `ocr_service_auto.py` or the legacy
`ocr_service.py` based on the `legacy_doc_types` list in the YAML pipeline config. When
onboarding a document type from `ocr_processors` to `ocr_processors_auto`:

1. Add the document type's prompt and config to `ocr_processors_auto/prompt/`.
2. Validate extraction quality matches or exceeds the legacy per-type processor output.
3. Remove the document type from `legacy_doc_types` in all pipeline YAML files that reference it.
4. The legacy processor subdirectory can remain in place (no deletion required) to avoid risk. It
   simply stops being called once removed from the list.

Keep `legacy_doc_types` in sync across all pipeline YAML files. Different pipelines may have
different lists if they process different document type sets, but a single document type should
use the same processor path everywhere to avoid inconsistent extraction results.

### Testing with real Azure services

Unit tests use mock services and run without Azure credentials. Integration tests that exercise the
Durable Functions adapter require the Azure Functions Core Tools (`func`) and a local storage
emulator (Azurite). Ensure CI/CD pipelines install both before running the full test suite.