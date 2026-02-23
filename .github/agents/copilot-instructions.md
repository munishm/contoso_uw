# CONTOSO_IWPB_UW Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- TypeScript 5.x, Vue.js 3.x + Vue 3 (Composition API), Vuetify 3.x, Vue Router, Pinia (state management), Axios/Fetch (HTTP client), PDF.js (document viewer) (001-underwriter-and-workflow)
- Backend handles all persistence (Azure Blob Storage + Azure SQL/Cosmos DB via REST API) (001-underwriter-and-workflow)
- Python 3.11 + FastAPI, Pydantic v2, Azure SDK (azure-storage-blob, azure-servicebus, azure-cosmos) (002-case-api)
- Azure Blob Storage (documents), Azure Cosmos DB (structured data) (002-case-api)
- Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity (003-fastapi-impl)
- Azure Cosmos DB (cases, documents, entities, summaries), Azure Blob Storage (files) (003-fastapi-impl)
- Azure Cosmos DB (cases, documents, entities, summaries, counters), Azure Blob Storage (files) (004-fastapi-src)
- Python 3.11 + FastAPI, Pydantic, Azure SDK (azure-ai-formrecognizer, azure-ai-openai), jsonschema (005-document-extraction-schema)
- Azure Cosmos DB (schema registry), Azure Blob Storage (documents) (005-document-extraction-schema)

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
- 005-document-extraction-schema: Added Python 3.11 + FastAPI, Pydantic, Azure SDK (azure-ai-formrecognizer, azure-ai-openai), jsonschema
- 005-document-extraction-schema: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 004-fastapi-src: Added Python 3.11 + FastAPI 0.109+, Pydantic 2.5+, azure-cosmos, azure-storage-blob, azure-servicebus, azure-identity


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
