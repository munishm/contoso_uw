# Document Type Onboarding - Architecture & Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  DocumentTypeOnboardingView.vue                       │ │
│  │  - 4-step wizard                                      │ │
│  │  - Hybrid layout (config + preview)                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  onboardingService.ts                                 │ │
│  │  - API client wrapper                                 │ │
│  │  - Type-safe interfaces                               │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP REST
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  /api/v1/onboarding/*                                 │ │
│  │  - classify-document                                  │ │
│  │  - test-extraction                                    │ │
│  │  - compare-models                                     │ │
│  │  - finalize                                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌──────────────────────┬──────────────────┬─────────────┐ │
│  │ DirectDocument       │ SchemaExtraction │ Evaluation  │ │
│  │ Classifier           │ Service          │ Service     │ │
│  │ (Azure CU)           │ (Entity Extract) │ (AI Eval)   │ │
│  └──────────────────────┴──────────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Cosmos DB                                │
│  ┌───────────────┬──────────────────┬────────────────────┐ │
│  │ extraction_   │ extraction_      │ extraction_        │ │
│  │ schemas       │ models           │ results            │ │
│  └───────────────┴──────────────────┴────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      STEP 1: Upload & Classify              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Select Mode]                                              │
│    ⚪ Create New                                            │
│    ⚪ Edit Existing → [Select Document Type ▼]             │
│                                                             │
│  [Upload Sample PDF]  📄 sample.pdf                         │
│                                                             │
│  [Classify Document] ──────→ Azure Content Understanding    │
│                                                             │
│  ✅ Detected: "Bank Statement" (95% confidence)            │
│                                                             │
│  [Upload Ground Truth JSON] (Optional)                      │
│                                                             │
│                                      [Next →]              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      STEP 2: Configure                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Document Type Name: [Bank Statement - Contoso          ]     │
│  Description:        [Monthly statements...          ]     │
│  Version:            [1.0.0                          ]     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Extraction Model                                    │   │
│  │ [Select Model ▼] → azure_gpt4_vision (gpt-4v)     │   │
│  │ 🏷️ Vision • OCR • Structured Extraction           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Custom Prompt (Optional)                            │   │
│  │ [Extract financial data from bank statement...   ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Schema Definition                                   │   │
│  │ [Input Schema] [Output Schema]                      │   │
│  │ {                                                   │   │
│  │   "account_number": {                               │   │
│  │     "type": "string",                               │   │
│  │     "description": "Account number"                 │   │
│  │   },                                                │   │
│  │   ...                                               │   │
│  │ }                                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Confidence Threshold: [●────────────] 0.70                │
│                                                             │
│                          [← Back]  [Test Extraction →]     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  STEP 3: Test & Review                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏳ Running extraction...                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🟢 FINALIZE                                         │   │
│  │    Results are good - ready to deploy!              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │ Avg Conf.    │ Completeness │ Correctness  │           │
│  │    85%       │     92%      │     88%      │           │
│  └──────────────┴──────────────┴──────────────┘           │
│                                                             │
│  Extracted Fields:                                          │
│  ✓ account_number: "1234567890" (95%)                      │
│  ✓ account_holder: "John Doe" (90%)                        │
│  ⚠️ balance: "5,000.00" (70%) - Needs Review               │
│  ✓ statement_date: "2024-01-15" (85%)                      │
│                                                             │
│  [⚙️ Adjust Configuration]                                  │
│  [🔄 Re-run Test]                                           │
│  [📊 Compare Models (A/B)]                                  │
│                                                             │
│                          [← Back]  [Finalize →]            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      STEP 4: Finalize                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ℹ️ Review your configuration before finalizing            │
│                                                             │
│  📋 Summary:                                                │
│    • Document Type: Bank Statement - Contoso                   │
│    • Version: 1.0.0                                         │
│    • Extraction Model: azure_gpt4_vision                    │
│    • Fields to Extract: 15 fields                           │
│    • Confidence Threshold: 0.70                             │
│                                                             │
│  ✅ Configuration saved successfully!                       │
│     Redirecting to dashboard...                             │
│                                                             │
│                          [← Back]  [✓ Complete Onboarding] │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

```
User                Frontend              Backend               External Services
 │                     │                     │                         │
 │ Upload PDF          │                     │                         │
 ├────────────────────>│                     │                         │
 │                     │ POST /classify      │                         │
 │                     ├────────────────────>│                         │
 │                     │                     │ Analyze Document        │
 │                     │                     ├────────────────────────>│
 │                     │                     │                   Azure CU
 │                     │                     │<────────────────────────┤
 │                     │ Classification      │                         │
 │                     │<────────────────────┤                         │
 │ View Results        │                     │                         │
 │<────────────────────┤                     │                         │
 │                     │                     │                         │
 │ Configure + Test    │                     │                         │
 ├────────────────────>│                     │                         │
 │                     │ POST /test-extract  │                         │
 │                     ├────────────────────>│                         │
 │                     │                     │ Get Schema/Model        │
 │                     │                     ├─────┐                   │
 │                     │                     │     │ Cosmos DB         │
 │                     │                     │<────┘                   │
 │                     │                     │                         │
 │                     │                     │ Extract Fields          │
 │                     │                     ├────────────────────────>│
 │                     │                     │                   GPT-4V
 │                     │                     │<────────────────────────┤
 │                     │                     │                         │
 │                     │                     │ Evaluate Results        │
 │                     │                     ├─────┐                   │
 │                     │                     │     │ Evaluation Service│
 │                     │                     │<────┘                   │
 │                     │                     │                         │
 │                     │ Extraction Results  │                         │
 │                     │<────────────────────┤                         │
 │ Review Results      │                     │                         │
 │<────────────────────┤                     │                         │
 │                     │                     │                         │
 │ Finalize            │                     │                         │
 ├────────────────────>│                     │                         │
 │                     │ POST /finalize      │                         │
 │                     ├────────────────────>│                         │
 │                     │                     │ Save Config             │
 │                     │                     ├─────┐                   │
 │                     │                     │     │ Cosmos DB         │
 │                     │                     │<────┘                   │
 │                     │ Success             │                         │
 │                     │<────────────────────┤                         │
 │ Redirect Dashboard  │                     │                         │
 │<────────────────────┤                     │                         │
```

## Component Interaction

```
┌────────────────────────────────────────────────────────────────┐
│                     Onboarding Components                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  DocumentTypeOnboardingView.vue                                │
│  │                                                              │
│  ├─ Step 1: Upload & Classify                                  │
│  │   └─ classifyDocument()                                     │
│  │       └─ onboardingService.classifyDocument()               │
│  │           └─ DirectDocumentClassifier                       │
│  │                                                              │
│  ├─ Step 2: Configure                                          │
│  │   ├─ loadExtractionModels()                                 │
│  │   │   └─ onboardingService.getExtractionModels()            │
│  │   │       └─ ExtractionModelRepository                      │
│  │   │                                                          │
│  │   └─ Schema Editor (JSON)                                   │
│  │                                                              │
│  ├─ Step 3: Test & Review                                      │
│  │   ├─ runTestExtraction()                                    │
│  │   │   └─ onboardingService.testExtraction()                 │
│  │   │       ├─ SchemaExtractionService                        │
│  │   │       └─ EvaluationService                              │
│  │   │                                                          │
│  │   └─ compareModels() [A/B Test]                             │
│  │       └─ onboardingService.compareModels()                  │
│  │                                                              │
│  └─ Step 4: Finalize                                           │
│      └─ finalizeOnboarding()                                   │
│          └─ onboardingService.finalizeOnboarding()             │
│              ├─ SchemaService.create_document_type()           │
│              └─ SchemaService.create_schema_version()          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────┐
│                  extraction_schemas                     │
├─────────────────────────────────────────────────────────┤
│ {                                                       │
│   "id": "uuid",                                         │
│   "document_type_id": "uuid",                           │
│   "name": "Bank Statement - Contoso",                      │
│   "version": "1.0.0",                                   │
│   "input_schema": {                                     │
│     "account_number": {"type": "string", ...},          │
│     "balance": {"type": "number", ...}                  │
│   },                                                    │
│   "output_schema": {...},                               │
│   "extraction_config": {                                │
│     "models": [                                         │
│       {                                                 │
│         "model_id": "uuid",                             │
│         "order": 1,                                     │
│         "strategy": "primary",                          │
│         "fields": ["*"]                                 │
│       }                                                 │
│     ],                                                  │
│     "custom_prompt": "Extract financial data...",       │
│     "combination_strategy": "sequential",               │
│     "conflict_resolution": "flag_for_review"            │
│   },                                                    │
│   "citation_level": "bounding_box",                     │
│   "confidence_threshold": 0.7,                          │
│   "created_by": "admin@contoso.com",                       │
│   "is_active": true                                     │
│ }                                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  extraction_models                      │
├─────────────────────────────────────────────────────────┤
│ {                                                       │
│   "id": "uuid",                                         │
│   "name": "azure_gpt4_vision",                          │
│   "type": "vision",                                     │
│   "endpoint": "https://...",                            │
│   "version": "gpt-4-vision-preview",                    │
│   "api_version": "2024-02-15-preview",                  │
│   "capabilities": [                                     │
│     "ocr",                                              │
│     "structured_extraction",                            │
│     "spatial_understanding"                             │
│   ],                                                    │
│   "is_active": true                                     │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

## Evaluation Decision Tree

```
                    Test Extraction
                          │
                          ↓
            ┌─────────────────────────┐
            │  Ground Truth Provided? │
            └─────────────────────────┘
                    │         │
                Yes │         │ No
                    ↓         ↓
        ┌──────────────┐  ┌──────────────────┐
        │   Compare    │  │  AI Evaluators   │
        │   with GT    │  │  - Completeness  │
        │   - Accuracy │  │  - Correctness   │
        └──────────────┘  └──────────────────┘
                    │         │
                    └────┬────┘
                         ↓
            ┌─────────────────────────┐
            │  Calculate Metrics:     │
            │  - Avg Confidence       │
            │  - Completeness Score   │
            │  - Correctness Score    │
            └─────────────────────────┘
                         │
                         ↓
            ┌─────────────────────────┐
            │   All Metrics ≥ 0.8?    │
            └─────────────────────────┘
                    │         │
                Yes │         │ No
                    ↓         ↓
            ┌──────────┐  ┌─────────────────┐
            │ FINALIZE │  │  Metrics ≥ 0.6? │
            └──────────┘  └─────────────────┘
                              │         │
                          Yes │         │ No
                              ↓         ↓
                        ┌────────┐  ┌───────┐
                        │ ADJUST │  │ RETRY │
                        └────────┘  └───────┘
```
