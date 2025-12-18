# HSBC_IWPB_UW Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- TypeScript 5.x, Vue.js 3.x + Vue 3 (Composition API), Vuetify 3.x, Vue Router, Pinia (state management), Axios/Fetch (HTTP client), PDF.js (document viewer) (001-underwriter-and-workflow)
- Backend handles all persistence (Azure Blob Storage + Azure SQL/Cosmos DB via REST API) (001-underwriter-and-workflow)

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
- 001-underwriter-and-workflow: Added TypeScript 5.x, Vue.js 3.x + Vue 3 (Composition API), Vuetify 3.x, Vue Router, Pinia (state management), Axios/Fetch (HTTP client), PDF.js (document viewer)

- 001-project-structure: Added N/A (Structure is technology-agnostic; components will determine specific languages - likely Python 3.11+ for backend services based on Azure AI stack) + N/A at structure level (Per-component package.json/requirements.txt for dependency management)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
