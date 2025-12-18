# HSBC_IWPB_UW Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- Python 3.11 + FastAPI, Pydantic v2, Azure SDK (azure-storage-blob, azure-servicebus, azure-cosmos) (002-case-api)
- Azure Blob Storage (documents), Azure Cosmos DB (structured data) (002-case-api)
- Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity (003-fastapi-impl)
- Azure Cosmos DB (cases, documents, entities, summaries), Azure Blob Storage (files) (003-fastapi-impl)
- Azure Cosmos DB (cases, documents, entities, summaries, counters), Azure Blob Storage (files) (004-fastapi-src)

- N/A (Structure is technology-agnostic; components will determine specific languages - likely Python 3.11+ for backend services based on Azure AI stack) + N/A at structure level (Per-component package.json/requirements.txt for dependency management) (001-project-structure)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

N/A (Structure is technology-agnostic; components will determine specific languages - likely Python 3.11+ for backend services based on Azure AI stack): Follow standard conventions

## Recent Changes
- 004-fastapi-src: Added Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity
- 004-fastapi-src: Added Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity
- 003-fastapi-impl: Added Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
