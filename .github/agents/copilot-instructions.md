# HSBC_IWPB_UW Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- Python 3.11 + FastAPI, Pydantic v2, Azure SDK (azure-storage-blob, azure-servicebus, azure-cosmos) (002-case-api)
- Azure Blob Storage (documents), Azure Cosmos DB (structured data) (002-case-api)

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
- 002-case-api: Added Python 3.11 + FastAPI, Pydantic v2, Azure SDK (azure-storage-blob, azure-servicebus, azure-cosmos)

- 001-project-structure: Added N/A (Structure is technology-agnostic; components will determine specific languages - likely Python 3.11+ for backend services based on Azure AI stack) + N/A at structure level (Per-component package.json/requirements.txt for dependency management)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
