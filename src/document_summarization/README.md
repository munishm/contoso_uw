# Document Summarization Component

## Purpose

Generates concise summaries of documents using Azure AI services. This component creates executive summaries that highlight key points, enabling underwriters to quickly understand document contents without reading full texts.

## Structure

```
document_summarization/
├── __init__.py              # Module exports
├── summarizer.py           # Main summarization logic
├── templates/              # Summary templates by document type
├── config.py               # Component configuration
└── pyproject.toml          # Component dependencies
```

## Interfaces Implemented

- `ISummarizer` from `src/interfaces/summarizer.py`
- `IDocumentProcessor` from `src/interfaces/processor.py`

## Dependencies

See `pyproject.toml` for component-specific dependencies.

## Usage

```python
from document_summarization import DocumentSummarizer

summarizer = DocumentSummarizer()
summary = summarizer.summarize(document, max_length=200)
print(summary.text)
print(f"Key points: {summary.key_points}")
```

## Testing

Unit tests are located in `test/unit/document_summarization/`.

```bash
uv run pytest test/unit/document_summarization/
```

## Configuration

Configuration is managed through environment variables (see `.env.example`):
- `DOCUMENT_SUMMARIZATION_MODEL`: Model to use (default: azure-openai)
- Additional Azure-specific settings

## Deployment

This component can be deployed independently as it has its own `pyproject.toml`.

```bash
cd src/document_summarization
uv build
```
