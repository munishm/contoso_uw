# Document Classification Component

## Purpose

Classifies incoming insurance documents into predefined types using Azure AI services. This component determines the document category (e.g., Lab Report, Medical Report, Invoice, Application) to route it to the appropriate processing pipeline.

## Three Classification Approaches

This module provides three different methods for document classification:

1. **ACU Only** - Uses Azure Content Understanding's built-in classification (most efficient)
2. **ACU + LLM Text** - Extracts text with ACU, classifies with Azure OpenAI (balanced)
3. **ACU + LLM Image** - Uses GPT-4 Vision for image-based classification (most flexible)

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed comparison and usage.

## Quick Start

### 1. Configure

Create `.env` file in this directory:

```bash
# Classification method
CLASSIFICATION_METHOD=acu_only  # or acu_llm_text, llm_image

# Azure Content Understanding
CU_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_TENANT_ID=your-tenant-id

# Azure OpenAI (for LLM methods)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1
```

### 2. Use via Interface

```python
from interfaces.classifier import get_classifier

# Create classifier (automatically uses configured method)
classifier = get_classifier()

# Classify a document
result = classifier.classify({'path': '/path/to/document.pdf'})

print(f"Document Type: {result['document_type']}")
print(f"Confidence: {result['confidence']:.3f}")

# Get available document types
types = classifier.get_document_types()
```

## Structure

```
document_classification/
├── __init__.py                    # Module exports
├── utils/
│   ├── config.py                  # Configuration management
│   ├── factory.py                 # Classifier factory
│   ├── auth.py                    # Azure authentication
│   └── acu_client.py             # ACU API client
├── acu_classifier.py             # ACU-only implementation
├── acu_llm_text_classifier.py    # ACU+LLM text implementation
├── llm_image_classifier.py       # LLM image implementation
├── notebooks/                     # Analysis notebooks
├── output/                        # Classification results
├── .env                          # Configuration (create from template)
├── pyproject.toml                # Dependencies
├── README.md                     # This file
└── IMPLEMENTATION.md             # Detailed implementation guide
```

## Interfaces Implemented

- `IClassifier` from `src/interfaces/classifier.py`
- `IDocumentProcessor` from `src/interfaces/processor.py`

## Dependencies

See `pyproject.toml` for component-specific dependencies.

## Usage

```python
from document_classification import DocumentClassifier

classifier = DocumentClassifier()
result = classifier.classify(document)
print(f"Document type: {result.document_type}")
print(f"Confidence: {result.confidence}")
```

## Testing

Unit tests are located in `test/unit/document_classification/`.

```bash
uv run pytest test/unit/document_classification/
```

## Configuration

Configuration is managed through environment variables (see `.env.example`):
- `DOCUMENT_CLASSIFICATION_MODEL`: Model to use (default: azure-openai)
- Additional Azure-specific settings

## Deployment

This component can be deployed independently as it has its own `pyproject.toml`.

```bash
cd src/document_classification
uv build
```
