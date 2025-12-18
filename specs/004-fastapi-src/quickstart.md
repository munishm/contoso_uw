# Quickstart: FastAPI Structure and API Implementation

**Feature**: 004-fastapi-src  
**Date**: 2025-12-17

## Prerequisites

- Python 3.11+
- Azure subscription with access to:
  - Cosmos DB (Core SQL API)
  - Blob Storage
  - Service Bus
  - Application Insights
- Azure CLI installed and authenticated

## Environment Setup

### 1. Navigate to Project Root

```bash
cd /home/ksharma/microsoft/hsbc/poc/HSBC_IWPB_UW
```

### 2. Create Python Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 3. Install Dependencies

Install the project with API dependencies:

```bash
pip install -e ".[api]"
```

Or manually install core dependencies:

```bash
pip install fastapi[standard]==0.109.2
pip install uvicorn[standard]==0.27.1
pip install pydantic==2.6.1
pip install pydantic-settings==2.1.0
pip install azure-cosmos==4.5.1
pip install azure-storage-blob==12.19.0
pip install azure-servicebus==7.11.4
pip install azure-identity==1.15.0
pip install azure-monitor-opentelemetry==1.2.0
pip install python-multipart==0.0.9
pip install httpx==0.27.0
```

### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
# Azure Cosmos DB
COSMOS_ENDPOINT=https://<account-name>.documents.azure.com:443/
COSMOS_DATABASE_NAME=underwriting
COSMOS_KEY=<your-cosmos-key>  # Or use Managed Identity

# Azure Blob Storage
BLOB_ACCOUNT_URL=https://<account-name>.blob.core.windows.net
BLOB_CONTAINER_NAME=documents
BLOB_CONNECTION_STRING=<your-connection-string>  # Or use Managed Identity

# Azure Service Bus
SERVICE_BUS_NAMESPACE=<namespace>.servicebus.windows.net
SERVICE_BUS_QUEUE_NAME=document-processing
SERVICE_BUS_CONNECTION_STRING=<your-connection-string>  # Or use Managed Identity

# Application Settings
API_VERSION=v1
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=50
SAS_TOKEN_EXPIRY_HOURS=1

# Azure AD Authentication
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>

# Development Only (disable auth for local testing)
DISABLE_AUTH=false
```

### 5. Azure Resource Setup (if not provisioned)

#### Cosmos DB Containers

```bash
# Using Azure CLI
az cosmosdb sql database create \
  --account-name <account-name> \
  --resource-group <resource-group> \
  --name underwriting

# Create containers
for container in cases documents entities summaries counters; do
  pk="/${container%s}_id"
  if [ "$container" = "counters" ]; then pk="/counter_id"; fi
  az cosmosdb sql container create \
    --account-name <account-name> \
    --resource-group <resource-group> \
    --database-name underwriting \
    --name $container \
    --partition-key-path "$pk"
done
```

#### Blob Storage Container

```bash
az storage container create \
  --name documents \
  --account-name <account-name> \
  --auth-mode login
```

#### Service Bus Queue

```bash
az servicebus queue create \
  --resource-group <resource-group> \
  --namespace-name <namespace> \
  --name document-processing \
  --max-size 1024
```

## Running the Application

### Development Mode

From project root:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### With Debugging

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### API Documentation

Once running, access:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

## Quick Verification

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "cosmos_db": "connected",
  "blob_storage": "connected",
  "service_bus": "connected"
}
```

### Create a Case (with auth disabled)

```bash
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "John Smith",
    "policy_type": "Life Insurance - HNW",
    "submission_date": "2025-12-17"
  }'
```

### Create a Case (with auth enabled)

```bash
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-azure-ad-token>" \
  -d '{
    "client_name": "John Smith",
    "policy_type": "Life Insurance - HNW",
    "submission_date": "2025-12-17"
  }'
```

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/cases/CASE-202512-000001/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf"
```

## Project Structure

After implementation, the `src/api/` folder will contain:

```
src/
├── api/                           # FastAPI application
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── dependencies.py            # Dependency injection
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Pydantic BaseSettings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── case.py
│   │   ├── document.py
│   │   ├── entity.py
│   │   ├── summary.py
│   │   ├── common.py
│   │   └── enums.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── cases.py               # 7 endpoints
│   │   ├── documents.py           # 6 endpoints
│   │   ├── processing.py          # 8 endpoints
│   │   └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── case_service.py
│   │   ├── document_service.py
│   │   ├── storage_service.py
│   │   └── queue_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── case_repository.py
│   │   ├── document_repository.py
│   │   ├── entity_repository.py
│   │   ├── summary_repository.py
│   │   └── counter_repository.py
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py
│       ├── error_handler.py
│       ├── logging.py
│       └── correlation.py
├── shared/                        # Existing (unchanged)
├── interfaces/                    # Existing (unchanged)
└── [other existing modules]       # Unchanged
```

## Testing

### Run Tests

```bash
# All API tests
pytest tests/api/ -v

# With coverage
pytest tests/api/ --cov=src/api --cov-report=html

# Specific test file
pytest tests/api/integration/test_cases_api.py -v
```

### Local Integration Testing

For local development without Azure resources, use emulators:

**Azurite (Blob Storage Emulator)**:

```bash
npm install -g azurite
azurite --silent --location /tmp/azurite --debug /tmp/azurite/debug.log
```

**Cosmos DB Emulator** (Docker):

```bash
docker run -p 8081:8081 -p 10251:10251 -p 10252:10252 -p 10253:10253 -p 10254:10254 \
  --memory 2g \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

## Common Issues

### Import Errors

If you get `ModuleNotFoundError: No module named 'src'`, ensure you're running from the project root:

```bash
cd /home/ksharma/microsoft/hsbc/poc/HSBC_IWPB_UW
uvicorn src.api.main:app --reload
```

### CORS Errors

If testing from a browser, ensure CORS is configured in `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication Issues

For local development, disable auth:

```bash
export DISABLE_AUTH=true
uvicorn src.api.main:app --reload
```

### Cosmos DB Connection

Ensure your IP is whitelisted in Cosmos DB firewall settings, or use Azure Private Link.

## Next Steps

1. Review the [OpenAPI specification](../002-case-api/contracts/openapi.yaml)
2. Check the [data model](./data-model.md)
3. Review the [research decisions](./research.md)
4. Run `/speckit.tasks` to generate the task breakdown
5. Begin implementation following the tasks
