# Entity Extraction Component

## Purpose

Extracts structured entities from unstructured documents using Azure AI services. This component identifies and extracts key information such as policy numbers, names, dates, amounts, and other domain-specific entities from insurance documents.

## Structure

```
entity_extraction/
├── __init__.py              # Module exports
├── extractor.py            # Main extraction logic
├── schemas/                # Entity schemas and definitions
├── config.py               # Component configuration
└── pyproject.toml          # Component dependencies
```

## Interfaces Implemented

- `IEntityExtractor` from `src/interfaces/extractor.py`
- `IDocumentProcessor` from `src/interfaces/processor.py`

## Dependencies

See `pyproject.toml` for component-specific dependencies.

## Usage

```python
from entity_extraction import EntityExtractor

extractor = EntityExtractor()
entities = extractor.extract(document)
for entity in entities:
    print(f"{entity.type}: {entity.value} (confidence: {entity.confidence})")
```

## Testing

Unit tests are located in `test/unit/entity_extraction/`.

```bash
uv run pytest test/unit/entity_extraction/
```

## Configuration

Configuration is managed through environment variables (see `.env.example`):
- `ENTITY_EXTRACTION_MODEL`: Model to use (default: azure-openai)
- Additional Azure-specific settings

## Deployment

This component can be deployed independently as it has its own `pyproject.toml`.

```bash
cd src/entity_extraction
uv build
```
