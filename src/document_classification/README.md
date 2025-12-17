# Document Classification Component

## Purpose

Classifies incoming documents into predefined types using Azure AI services. This component determines the document category (e.g., policy application, claim form, medical record) to route it to the appropriate processing pipeline.

## Structure

```
document_classification/
├── __init__.py              # Module exports
├── classifier.py            # Main classification logic
├── models/                  # Data models specific to classification
├── config.py               # Component configuration
└── pyproject.toml          # Component dependencies
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
