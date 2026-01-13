# Document Type Onboarding - Quick Start Guide

## Overview
This guide walks you through onboarding a new document type for automated extraction.

## Prerequisites
- Admin/Power user access
- Sample document(s) of the type you want to onboard
- (Optional) Ground truth JSON file with expected values

## Step-by-Step Guide

### 1. Access Onboarding Screen
1. Navigate to the Dashboard
2. Click **"Document Type Onboarding"** button (top-right)

### 2. Upload & Classify

#### Option A: Create New Document Type
1. Select **"Create New Document Type"** mode
2. Upload a sample PDF document
3. Click **"Classify Document"**
4. Review the suggested document type name and confidence score
5. (Optional) Upload a ground truth JSON file for evaluation
6. Click **"Next"**

#### Option B: Edit Existing Document Type
1. Select **"Edit Existing Document Type"** mode
2. Choose the document type from the dropdown
3. Upload a new sample document (or use existing configuration)
4. Click **"Next"**

### 3. Configure Extraction

#### Basic Information
- **Document Type Name**: Enter a descriptive name (e.g., "Bank Statement - HSBC")
- **Description**: Add context about this document type
- **Version**: Specify version number (e.g., "1.0.0")

#### Select Extraction Model
- Choose from available models in the dropdown
- Model capabilities are shown (e.g., OCR, structured extraction)
- The model will be used to extract data from documents of this type

#### Custom Prompt (Optional)
```
Example prompt:
"Extract financial information from this bank statement. 
Focus on account number, balance, and transaction details."
```

#### Define Schemas

**Input Schema** (Fields to extract):
```json
{
  "account_number": {
    "type": "string",
    "description": "Bank account number"
  },
  "account_holder": {
    "type": "string",
    "description": "Name of account holder"
  },
  "balance": {
    "type": "number",
    "description": "Current balance"
  },
  "statement_date": {
    "type": "string",
    "format": "date",
    "description": "Statement date"
  }
}
```

**Output Schema** (Structure of extracted data):
```json
{
  "account_number": {
    "type": "object",
    "properties": {
      "value": {"type": "string"},
      "confidence": {"type": "number"}
    }
  },
  "account_holder": {
    "type": "object",
    "properties": {
      "value": {"type": "string"},
      "confidence": {"type": "number"}
    }
  }
}
```

#### Confidence Threshold
- Set the minimum confidence level (0.0 - 1.0)
- Lower values extract more fields but may be less accurate
- Recommended: 0.7

Click **"Test Extraction"** when ready.

### 4. Test & Review

The system will run extraction on your sample document and show:

#### Evaluation Metrics
- **Average Confidence**: Overall extraction confidence
- **Completeness Score**: How many fields were found
- **Correctness Score**: How accurate the extractions are

#### Recommendation
- 🟢 **FINALIZE** - Results are good, ready to deploy
- 🟡 **ADJUST** - Results are okay but could be improved
- 🔴 **RETRY** - Results need improvement

#### Review Extracted Fields
The right panel shows all extracted fields with:
- Field name
- Extracted value
- Confidence score
- Data type
- Model source
- Review flags (if any)

#### Options
1. **Adjust Configuration** - Go back to Step 2 to modify settings
2. **Re-run Test** - Test again with current configuration
3. **Compare Models (A/B Test)** - Compare results from different models

### 5. Finalize Onboarding

Review the summary:
- Document type name
- Version
- Extraction model
- Number of fields

Click **"Complete Onboarding"** to save the configuration.

## Ground Truth Format

If you have expected values for evaluation, create a JSON file:

```json
{
  "account_number": "1234567890",
  "account_holder": "John Doe",
  "balance": 5000.00,
  "statement_date": "2024-01-15"
}
```

Upload this during Step 2 for more accurate evaluation metrics.

## Tips & Best Practices

### Schema Design
- ✅ Use descriptive field names (snake_case)
- ✅ Add descriptions for each field
- ✅ Specify data types (string, number, date, etc.)
- ✅ Keep schemas focused (10-20 fields max)

### Model Selection
- **Vision Models** (e.g., GPT-4 Vision) - Best for complex layouts, tables, images
- **Document Intelligence** - Fast, good for structured forms
- **Hybrid Approach** - Use multiple models (configured in extraction_config)

### Custom Prompts
- Be specific about what to extract
- Mention document structure if known
- Include edge cases or special handling
- Keep prompts concise (1-3 sentences)

### Testing
- Test with multiple sample documents if available
- Try documents with variations (different formats, quality)
- Use ground truth for critical fields
- Iterate on prompts and thresholds

### Confidence Thresholds
- **0.9+** - Very high confidence, may miss some fields
- **0.7-0.8** - Balanced (recommended)
- **0.5-0.6** - Permissive, may need more review
- **<0.5** - Not recommended for production

## Troubleshooting

### Low Completeness Score
- Check if all fields are present in the sample document
- Adjust input schema to match actual document content
- Try a different extraction model
- Lower confidence threshold

### Low Correctness Score
- Improve custom prompt with more specific instructions
- Increase confidence threshold
- Use ground truth to identify problem fields
- Try a more capable model

### Model Comparison
Use A/B testing when:
- Results are inconsistent
- Multiple models support your document type
- Trying to optimize cost vs. accuracy
- Evaluating new model versions

## Next Steps

After onboarding:
1. The document type is available for case processing
2. Upload documents of this type to cases
3. Extraction will automatically use your configuration
4. Monitor results and iterate as needed

## API Reference

For programmatic access, see:
- API Documentation: `/docs` (Swagger UI)
- Service: `/src/frontend/src/services/onboardingService.ts`
- Implementation: `/docs/features/document-type-onboarding.md`

## Support

For issues or questions:
- Check logs: `/src/api/routes/onboarding.py` (backend)
- Browser console (frontend errors)
- Azure Content Understanding service health
- Cosmos DB connectivity
