---
title: "Underwriting Case Management API"
description: "FastAPI backend for the HSBC IWPB Underwriting POC - provides REST API for case and document management"
author: "HSBC IWPB UW Team"
ms.date: 2025-12-18
ms.topic: reference
---

# Underwriting Case Management API

FastAPI-based REST API for managing underwriting cases and documents. This API enables underwriters to create cases, upload documents for automatic processing (classification, entity extraction, summarization), and retrieve analysis results.

## Features

- **Case Management**: Create, update, delete, and list underwriting cases
- **Document Upload**: Upload documents with automatic processing queue
- **Entity Extraction**: Retrieve AI-extracted entities from documents
- **Summarization**: Get AI-generated document and case summaries
- **Status Tracking**: Monitor processing status and case workflow

## Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (recommended) or pip
- Azure services (or local emulators for development):
  - Azure Cosmos DB (or Cosmos DB Emulator)
  - Azure Blob Storage (or Azurite)
  - Azure Service Bus (optional for local development)
  - Azure AD (optional - can be disabled for local testing)

## Quick Start

### 1. Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew (macOS)
brew install uv
```

### 2. Set Up Environment

```bash
# Navigate to project root
cd /path/to/HSBC_IWPB_UW

# Sync dependencies (creates .venv automatically)
uv sync --extra api

# For development (includes test dependencies)
uv sync --extra api --extra dev
```

### 3. Configure Environment Variables

```bash
# Copy the template
cp src/api/.env.template .env

# Edit .env with your values
# For local development with emulators, see "Local Development Setup" below
```

### 4. Run the Application

```bash
# Development mode with auto-reload (using uv run)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or activate the venv first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the API

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## Local Development Setup

For local development without Azure services, you can use emulators:

### Option A: Minimal Setup (No Azure Services)

Set the following in your `.env` file to run without any Azure dependencies:

```bash
# Disable authentication
DISABLE_AUTH=true

# Leave Azure service configs empty - app will start with warnings
# but health endpoint and Swagger UI will work
```

### Option B: With Azure Emulators

#### Cosmos DB Emulator

1. Install [Azure Cosmos DB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator)

2. Configure in `.env`:

```bash
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=underwriting
```

#### Azurite (Blob Storage Emulator)

1. Install Azurite:

```bash
npm install -g azurite
# Or use VS Code extension: "Azurite"
```

2. Start Azurite:

```bash
azurite --silent --location ./azurite-data --debug ./azurite-debug.log
```

3. Configure in `.env`:

```bash
BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1
BLOB_CONTAINER_NAME=documents
```

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with service status |

### Cases

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cases` | List cases with pagination and filtering |
| POST | `/api/v1/cases` | Create a new case |
| GET | `/api/v1/cases/{caseId}` | Get case details |
| PUT | `/api/v1/cases/{caseId}` | Update case |
| DELETE | `/api/v1/cases/{caseId}` | Soft delete case |
| POST | `/api/v1/cases/{caseId}/restore` | Restore deleted case |
| GET | `/api/v1/cases/{caseId}/status-history` | Get case status history |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cases/{caseId}/documents` | List case documents |
| POST | `/api/v1/cases/{caseId}/documents` | Upload document |
| GET | `/api/v1/cases/{caseId}/documents/{documentId}` | Get document details |
| PUT | `/api/v1/cases/{caseId}/documents/{documentId}` | Update document metadata |
| DELETE | `/api/v1/cases/{caseId}/documents/{documentId}` | Delete document |
| GET | `/api/v1/cases/{caseId}/documents/{documentId}/download` | Get download URL |

### Processing Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cases/{caseId}/documents/{documentId}/entities` | Get extracted entities |
| GET | `/api/v1/cases/{caseId}/documents/{documentId}/entities/{entityId}/explain` | Explain entity extraction |
| GET | `/api/v1/cases/{caseId}/documents/{documentId}/summary` | Get document summary |
| GET | `/api/v1/cases/{caseId}/documents/{documentId}/summary/explain` | Explain summary generation |
| POST | `/api/v1/cases/{caseId}/documents/{documentId}/reprocess` | Reprocess document |
| GET | `/api/v1/cases/{caseId}/entities` | Get aggregated entities for case |
| GET | `/api/v1/cases/{caseId}/summary` | Get case summary |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `hsbc-iwpb-uw` | Application name |
| `APP_ENV` | No | `development` | Environment (development/staging/production) |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_VERSION` | No | `v1` | API version prefix |
| `AZURE_TENANT_ID` | Yes* | - | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Yes* | - | Azure AD application ID |
| `DISABLE_AUTH` | No | `false` | Disable authentication (dev only) |
| `COSMOS_ENDPOINT` | Yes* | - | Cosmos DB endpoint URL |
| `COSMOS_KEY` | Yes* | - | Cosmos DB access key |
| `COSMOS_DATABASE_NAME` | No | `underwriting` | Database name |
| `BLOB_ACCOUNT_URL` | Yes* | - | Blob storage account URL |
| `BLOB_CONTAINER_NAME` | No | `documents` | Container name |
| `BLOB_CONNECTION_STRING` | Alt | - | Alternative to account URL |
| `SERVICE_BUS_NAMESPACE` | No | - | Service Bus namespace |
| `SERVICE_BUS_QUEUE_NAME` | No | `document-processing` | Queue name |
| `MAX_UPLOAD_SIZE_MB` | No | `50` | Max file upload size (MB) |
| `MAX_DOCUMENTS_PER_CASE` | No | `50` | Max documents per case |
| `CORS_ORIGINS` | No | `localhost:3000,8080` | Allowed CORS origins |

*Required for full functionality; app will start with warnings if missing

## Project Structure

```text
src/api/
├── __init__.py              # Package init, version
├── main.py                  # FastAPI app entry point
├── dependencies.py          # FastAPI dependency injection
├── telemetry.py            # Application Insights integration
├── .env.template           # Environment variable template
├── config/
│   └── settings.py         # Pydantic BaseSettings configuration
├── models/
│   ├── case.py             # Case request/response models
│   ├── document.py         # Document models
│   ├── entity.py           # Entity extraction models
│   ├── summary.py          # Summary models
│   ├── common.py           # Shared response models
│   └── enums.py            # Status enumerations
├── repositories/
│   ├── base.py             # Cosmos DB base repository
│   ├── case_repository.py
│   ├── document_repository.py
│   ├── entity_repository.py
│   ├── summary_repository.py
│   └── counter_repository.py
├── services/
│   ├── case_service.py     # Case business logic
│   ├── document_service.py # Document business logic
│   ├── processing_service.py
│   ├── storage_service.py  # Blob storage operations
│   └── queue_service.py    # Service Bus messaging
├── middleware/
│   ├── auth.py             # JWT/JWKS authentication
│   ├── correlation.py      # Correlation ID middleware
│   ├── error_handler.py    # Exception handling
│   └── logging.py          # Request/response logging
└── routes/
    ├── health.py           # Health check endpoint
    ├── cases.py            # Case CRUD endpoints
    ├── documents.py        # Document endpoints
    └── processing.py       # Processing results endpoints
```

## Running Tests

```bash
# Run all tests with UV
uv run pytest

# Run API tests only
uv run pytest tests/api/

# Run with coverage
uv run pytest --cov=src/api tests/api/

# Run specific test file
uv run pytest tests/api/test_cases.py -v
```

## Common UV Commands

```bash
# Sync all dependencies
uv sync --extra api --extra dev

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update all dependencies
uv lock --upgrade

# Show installed packages
uv pip list

# Run any command in the virtual environment
uv run <command>

# Generate requirements.txt (if needed for deployment)
uv pip compile pyproject.toml -o requirements.txt --extra api
```

## Troubleshooting

### App starts but shows warnings about Azure services

This is expected when running locally without Azure services configured. The app will start in degraded mode - basic endpoints work but Azure-dependent features will fail.

### SSL certificate errors with Cosmos DB Emulator

Add this environment variable:

```bash
export COSMOS_SSL_VERIFY=false
```

### Port already in use

Change the port:

```bash
uv run uvicorn src.api.main:app --reload --port 8001
```

### Import errors

Ensure you've synced dependencies with the API extra:

```bash
uv sync --extra api
```

### UV not finding Python 3.11+

Install the required Python version:

```bash
uv python install 3.11
```

## License

Proprietary - HSBC Internal Use Only
