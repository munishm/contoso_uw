# Document Type Onboarding Feature - Implementation Summary

## Overview
A comprehensive UI screen and API for power users to onboard new document types with customizable extraction models, schemas, and prompts. The feature supports both creating new document types and editing existing ones.

## Features Implemented

### 1. Backend API (`/src/api/routes/onboarding.py`)

#### Endpoints Created:
- **POST `/api/v1/onboarding/classify-document`** - Classify uploaded document to determine type
- **POST `/api/v1/onboarding/test-extraction`** - Test extraction with configuration
- **POST `/api/v1/onboarding/compare-models`** - A/B test multiple model configurations
- **POST `/api/v1/onboarding/finalize`** - Finalize and save document type configuration

#### Key Capabilities:
- Document classification using Azure Content Understanding
- Test extraction with custom models and prompts
- Evaluation with ground truth (optional) or AI evaluators (completeness/correctness)
- A/B comparison of multiple models
- Support for both creating new and editing existing document types

### 2. Frontend Service (`/src/frontend/src/services/onboardingService.ts`)

Provides TypeScript client for all onboarding operations:
- `classifyDocument()` - Upload and classify
- `getExtractionModels()` - Fetch available models
- `getDocumentTypes()` - List existing document types
- `testExtraction()` - Test with configuration
- `compareModels()` - A/B test
- `finalizeOnboarding()` - Save configuration

### 3. Frontend UI (`/src/frontend/src/views/DocumentTypeOnboardingView.vue`)

#### Hybrid Layout (Left Config + Right Preview):
- **Left Panel**: 4-step wizard for configuration
- **Right Panel**: Real-time extraction results preview

#### Step 1: Upload & Classify
- Mode selection (Create new / Edit existing)
- Sample document upload
- Automatic document classification
- Optional ground truth JSON upload

#### Step 2: Configure
- Document type name, description, version
- Model selection from registry
- Custom extraction prompt (optional)
- Input/Output schema definition (JSON)
- Confidence threshold slider

#### Step 3: Test & Review
- Real-time extraction testing
- Evaluation metrics display:
  - Average confidence
  - Completeness score
  - Correctness score
- Recommendation badges (Finalize/Adjust/Retry)
- Options:
  - Adjust configuration
  - Re-run test
  - A/B compare models

#### Step 4: Finalize
- Review configuration summary
- Complete onboarding
- Save to database

### 4. Router Configuration
- Added `/onboarding` route
- Added navigation button on Dashboard

## Data Flow

```
1. Upload Document
   ↓
2. Classify (Azure Content Understanding)
   ↓
3. Configure (Models, Schemas, Prompts)
   ↓
4. Test Extraction
   ↓
5. Evaluate Results
   ├─ With Ground Truth → Accuracy metrics
   └─ Without Ground Truth → AI Evaluators (Completeness + Correctness)
   ↓
6. Review & Iterate (or Finalize)
   ↓
7. Save to extraction_schemas & extraction_models collections
```

## Evaluation Logic

### With Ground Truth:
- Compares extracted values with expected values
- Calculates accuracy, precision metrics
- Field-by-field evaluation

### Without Ground Truth:
- Uses `EvaluationService` from `/src/evaluation/entity_extraction/`
- Completeness evaluator checks if all expected fields extracted
- Correctness evaluator validates extraction quality
- Aggregates scores and provides recommendations

### Recommendation Thresholds:
- **Finalize**: Avg confidence ≥ 0.8, Completeness ≥ 0.8, Correctness ≥ 0.8
- **Adjust**: Avg confidence ≥ 0.6, Completeness ≥ 0.6
- **Retry**: Below adjustment thresholds

## Database Schema

### Cosmos DB Collections Used:
- `extraction_schemas` - Document types and versions
- `extraction_models` - Available extraction models
- `extraction_results` - Test extraction results

## UI/UX Features

### Visual Indicators:
- Color-coded confidence chips (Green/Yellow/Red)
- Recommendation badges with icons
- Progress indicators during processing
- Sticky results panel for easy comparison

### User Interactions:
- Multi-step wizard with validation
- Real-time JSON schema editing
- Expandable field details
- Model comparison dialog
- Ground truth upload for validation

### Accessibility:
- Vuetify 3 components (WCAG compliant)
- Clear labels and descriptions
- Error messages with guidance
- Loading states

## Testing Recommendations

### Backend Testing:
```bash
# Test classification
curl -X POST http://localhost:8000/api/v1/onboarding/classify-document \
  -F "file=@sample.pdf"

# Test extraction
curl -X POST http://localhost:8000/api/v1/onboarding/test-extraction \
  -F "document_id=test_123" \
  -F "config_json={...}" \
  -F "file=@sample.pdf"
```

### Frontend Testing:
1. Navigate to `http://localhost:5173/onboarding`
2. Upload a sample document
3. Configure extraction model and schema
4. Test extraction
5. Review results and finalize

## Future Enhancements

### Potential Improvements:
- [ ] Version history for document types
- [ ] Schema validation rules (regex, ranges)
- [ ] Batch testing with multiple documents
- [ ] Export/import document type configurations
- [ ] Model performance analytics dashboard
- [ ] Field-level prompt customization
- [ ] Template library for common document types

## Files Modified/Created

### Backend:
- ✅ `/src/api/routes/onboarding.py` (NEW)
- ✅ `/src/api/main.py` (Modified - added onboarding router)

### Frontend:
- ✅ `/src/frontend/src/services/onboardingService.ts` (NEW)
- ✅ `/src/frontend/src/views/DocumentTypeOnboardingView.vue` (NEW)
- ✅ `/src/frontend/src/router/index.ts` (Modified - added route)
- ✅ `/src/frontend/src/views/DashboardView.vue` (Modified - added navigation)

## Dependencies

### Existing:
- Azure Content Understanding (Classification)
- Entity Extraction Service (Extraction)
- Evaluation Service (Completeness/Correctness)
- Cosmos DB (Schema storage)

### No New Dependencies Required ✅

## Notes

- POC version: Single prompt per document (not per-field)
- Single version only (no version history yet)
- Power-user feature (not part of case workflow)
- Uses existing `extraction_schemas` and `extraction_models` DB structure
- Evaluation can work with or without ground truth
