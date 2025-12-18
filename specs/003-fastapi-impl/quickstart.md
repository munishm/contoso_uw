# Quickstart: FastAPI Implementation

**Feature**: 003-fastapi-impl  
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

### 1. Clone and Navigate

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

```bash
pip install -e "backend[dev]"
```

Or manually install core dependencies:

```bash
pip install fastapi[standard]==0.109.2
pip install uvicorn[standard]==0.27.1
pip install pydantic==2.6.1
pip install azure-cosmos==4.5.1
pip install azure-storage-blob==12.19.0
pip install azure-servicebus==7.11.4
pip install azure-identity==1.15.0
pip install azure-monitor-opentelemetry==1.2.0
pip install python-multipart==0.0.9
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

# Azure AD Authentication (for production)
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>
```

### 5. Azure Resource Setup

#### Cosmos DB Containers

Create the database and containers:

```bash
# Using Azure CLI
az cosmosdb sql database create \
  --account-name <account-name> \
  --resource-group <resource-group> \
  --name underwriting

# Create containers
for container in cases documents entities summaries counters; do
  az cosmosdb sql container create \
    --account-name <account-name> \
    --resource-group <resource-group> \
    --database-name underwriting \
    --name $container \
    --partition-key-path "/${container%s}_id"
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

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### With Debugging

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
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

### Create a Case

```bash
curl -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "client_name": "John Smith",
    "policy_type": "Life Insurance - HNW",
    "submission_date": "2025-12-17"
  }'
```

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/cases/CASE-202512-001234/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf"
```

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── cases.py        # Case endpoints
│   │       ├── documents.py    # Document endpoints
│   │       └── health.py       # Health check
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Pydantic settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── case.py             # Case Pydantic models
│   │   ├── document.py         # Document Pydantic models
│   │   ├── entity.py           # Entity Pydantic models
│   │   └── enums.py            # Status enumerations
│   └── services/
│       ├── __init__.py
│       ├── case_service.py     # Case business logic
│       ├── document_service.py # Document business logic
│       ├── cosmos_client.py    # Cosmos DB operations
│       ├── blob_service.py     # Blob Storage operations
│       └── queue_service.py    # Service Bus operations
└── pyproject.toml
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_cases.py -v
```

### Local Integration Testing

For local development without Azure resources, use the Azure Storage Emulator (Azurite):

```bash
# Install and start Azurite
npm install -g azurite
azurite --silent --location /tmp/azurite --debug /tmp/azurite/debug.log
```

For Cosmos DB, use the emulator:

```bash
# Docker-based emulator
docker run -p 8081:8081 -p 10251:10251 -p 10252:10252 -p 10253:10253 -p 10254:10254 \
  --memory 2g \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

## Common Issues

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

For local development, you can disable auth by setting:

```bash
DISABLE_AUTH=true
```

### Cosmos DB Connection

Ensure your IP is whitelisted in Cosmos DB firewall settings, or use Azure Private Link for production.

## Next Steps

1. Review the [OpenAPI specification](../002-case-api/contracts/openapi.yaml)
2. Check the [data model](./data-model.md)
3. Review the [research decisions](./research.md)
4. Begin implementation following the [plan](./plan.md)
