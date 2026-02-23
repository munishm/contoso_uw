<!-- markdownlint-disable-file -->
# Implementation Details: Migrate Schema Storage from Cosmos DB to Azure Table Storage

## Context Reference

Sources: Project files (src/entity_extraction/), architecture documentation (docs/architecture/), existing Cosmos DB implementation

## Implementation Phase 1: Configuration and Dependencies

<!-- parallelizable: true -->

### Step 1.1: Add Azure Table Storage configuration to ExtractionConfig

Update configuration model to support Table Storage connection settings while maintaining backward compatibility with Cosmos DB during transition period.

Files:
* src/entity_extraction/config.py - Add Table Storage configuration fields

Success criteria:
* Configuration supports both Cosmos DB and Table Storage settings
* Environment variables follow EXTRACTION_ prefix convention
* DefaultAzureCredential used for managed identity authentication
* Storage account connection string supported for development

Context references:
* src/entity_extraction/config.py (Lines 17-50) - Existing ExtractionConfig class with Cosmos DB settings
* .env.example (Lines 33-43) - Existing Azure storage configuration patterns

Dependencies:
* None - configuration only

Implementation:
```python
# Add to ExtractionConfig class in src/entity_extraction/config.py

# Azure Table Storage settings (replaces Cosmos DB for schema storage)
table_storage_account_name: Optional[str] = None
table_storage_account_key: Optional[str] = None
table_storage_endpoint: Optional[str] = None  # https://<account>.table.core.windows.net/
table_storage_connection_string: Optional[str] = None  # For development only

# Table names
table_name_document_types: str = "DocumentTypes"
table_name_schema_versions: str = "SchemaVersions"

# Keep cosmos settings for migration period (mark as deprecated)
# TODO: Remove after migration complete
```

### Step 1.2: Add azure-data-tables dependency

Add Azure Table Storage SDK to project dependencies.

Files:
* pyproject.toml - Add azure-data-tables to dependencies

Success criteria:
* Package version pinned to stable release
* Compatible with existing Azure SDK packages

Dependencies:
* None

Implementation:
```toml
# Add to [project.dependencies] in pyproject.toml
"azure-data-tables>=12.5.0",
```

### Step 1.3: Update environment variable documentation

Document new Table Storage configuration in .env.example and configuration guides.

Files:
* .env.example - Add Table Storage variables
* docs/guides/environment_configuration.md - Document Table Storage configuration

Success criteria:
* Clear examples for both development (connection string) and production (managed identity)
* Migration notes for existing Cosmos DB users

Context references:
* .env.example (Lines 1-60) - Existing configuration format
* docs/guides/environment_configuration.md (Lines 100-130) - Cosmos DB configuration section

Dependencies:
* Step 1.1 completion

Implementation:
Add to .env.example:
```bash
# =============================================================================
# Azure Table Storage (Schema Storage)
# =============================================================================
# Table Storage account for schema storage (replaces Cosmos DB)
EXTRACTION_TABLE_STORAGE_ACCOUNT_NAME=your-storage-account
EXTRACTION_TABLE_STORAGE_ENDPOINT=https://your-storage-account.table.core.windows.net/
# Development only - use managed identity in production
EXTRACTION_TABLE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### Step 1.4: Validate phase changes

Run lint and build commands for modified files. Skip validation when it conflicts with parallel phases running the same validation scope.

Validation commands:
* ruff check src/entity_extraction/config.py
* mypy src/entity_extraction/config.py

## Implementation Phase 2: Table Storage Schema Repository

<!-- parallelizable: false -->

### Step 2.1: Create TableStorageSchemaRepository class

Create new repository implementation using Azure Table Storage SDK with same interface as Cosmos DB repository.

Files:
* src/entity_extraction/repositories/table_schema_repository.py - New Table Storage repository

Success criteria:
* Implements same public interface as existing SchemaRepository
* Uses TableClient from azure.data.tables
* Supports both access key and managed identity authentication
* JSON fields serialized properly for storage
* Partition and row key design optimized for access patterns

Context references:
* src/entity_extraction/repositories/schema_repository.py (Lines 1-162) - Current Cosmos DB implementation
* Azure Table Storage design patterns documentation

Dependencies:
* Step 1.1 completion (configuration)
* Step 1.2 completion (azure-data-tables package)

Implementation:
```python
"""Repository for document type schemas in Azure Table Storage."""

import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient
from azure.identity import DefaultAzureCredential

from ..config import get_config
from ..models import DocumentType, DocumentTypeVersion

logger = logging.getLogger(__name__)


class TableStorageSchemaRepository:
    """Repository for managing document types and schema versions using Azure Table Storage."""
    
    def __init__(self):
        """Initialize Table Storage schema repository."""
        config = get_config()
        
        # Initialize Table Service Client
        if config.table_storage_connection_string:
            # Development: connection string
            self._service_client = TableServiceClient.from_connection_string(
                config.table_storage_connection_string
            )
        elif config.table_storage_endpoint:
            # Production: managed identity
            credential = DefaultAzureCredential()
            self._service_client = TableServiceClient(
                endpoint=config.table_storage_endpoint,
                credential=credential
            )
        else:
            raise ValueError("Table Storage configuration missing: set EXTRACTION_TABLE_STORAGE_ENDPOINT or EXTRACTION_TABLE_STORAGE_CONNECTION_STRING")
        
        # Get table clients (create tables if not exist)
        self._document_types_table: TableClient = self._service_client.get_table_client(config.table_name_document_types)
        self._schema_versions_table: TableClient = self._service_client.get_table_client(config.table_name_schema_versions)
        
        # Ensure tables exist
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist."""
        try:
            self._service_client.create_table_if_not_exists(self._document_types_table.table_name)
            self._service_client.create_table_if_not_exists(self._schema_versions_table.table_name)
        except Exception as e:
            logger.warning(f"Could not verify tables exist: {e}")
```

Partition and Row Key Design:
* DocumentTypes table:
  * PartitionKey: "DOCTYPE" (all types in same partition for efficient list operations)
  * RowKey: str(document_type_id) (UUID as string)
* SchemaVersions table:
  * PartitionKey: str(document_type_id) (group versions by document type)
  * RowKey: version string (e.g., "1.0.0" or "2024")

### Step 2.2: Implement DocumentType operations (CRUD)

Implement create, read, update, delete operations for DocumentType entities.

Files:
* src/entity_extraction/repositories/table_schema_repository.py - Add DocumentType methods

Success criteria:
* create_document_type stores entity with proper keys
* get_document_type retrieves by ID
* get_document_type_by_name queries with filter
* list_document_types supports active_only filtering
* JSON serialization handles datetime and UUID types

Context references:
* src/entity_extraction/repositories/schema_repository.py (Lines 35-94) - Cosmos DB DocumentType operations
* src/entity_extraction/models/schema.py (Lines 11-27) - DocumentType model

Dependencies:
* Step 2.1 completion

Implementation:
```python
# Add to TableStorageSchemaRepository class

def _serialize_document_type(self, doc_type: DocumentType) -> dict:
    """Convert DocumentType to Table Storage entity."""
    entity = {
        "PartitionKey": "DOCTYPE",
        "RowKey": str(doc_type.id),
        "id": str(doc_type.id),
        "name": doc_type.name,
        "description": doc_type.description or "",
        "created_at": doc_type.created_at.isoformat(),
        "created_by": doc_type.created_by,
        "is_active": doc_type.is_active,
    }
    return entity

def _deserialize_document_type(self, entity: dict) -> DocumentType:
    """Convert Table Storage entity to DocumentType."""
    return DocumentType(
        id=UUID(entity["id"]),
        name=entity["name"],
        description=entity.get("description") or None,
        created_at=datetime.fromisoformat(entity["created_at"]),
        created_by=entity["created_by"],
        is_active=entity["is_active"],
    )

async def create_document_type(self, document_type: DocumentType) -> DocumentType:
    """Create a new document type."""
    entity = self._serialize_document_type(document_type)
    self._document_types_table.create_entity(entity)
    return document_type

async def get_document_type(self, type_id: UUID) -> Optional[DocumentType]:
    """Get document type by ID."""
    try:
        entity = self._document_types_table.get_entity(
            partition_key="DOCTYPE",
            row_key=str(type_id)
        )
        return self._deserialize_document_type(entity)
    except ResourceNotFoundError:
        return None

async def get_document_type_by_name(self, name: str) -> Optional[DocumentType]:
    """Get document type by name (case-insensitive)."""
    # Table Storage filter query
    filter_query = f"PartitionKey eq 'DOCTYPE' and name eq '{name}' and is_active eq true"
    entities = list(self._document_types_table.query_entities(filter_query))
    
    if not entities:
        # Try case-insensitive by iterating (Table Storage doesn't support LOWER)
        filter_query = "PartitionKey eq 'DOCTYPE' and is_active eq true"
        entities = [e for e in self._document_types_table.query_entities(filter_query) 
                   if e["name"].lower() == name.lower()]
    
    return self._deserialize_document_type(entities[0]) if entities else None

async def list_document_types(self, active_only: bool = True) -> List[DocumentType]:
    """List all document types."""
    filter_query = "PartitionKey eq 'DOCTYPE'"
    if active_only:
        filter_query += " and is_active eq true"
    
    entities = self._document_types_table.query_entities(filter_query)
    return [self._deserialize_document_type(e) for e in entities]
```

### Step 2.3: Implement SchemaVersion operations (CRUD)

Implement create, read, list operations for DocumentTypeVersion entities with complex JSON field handling.

Files:
* src/entity_extraction/repositories/table_schema_repository.py - Add SchemaVersion methods

Success criteria:
* create_schema_version stores entity with document_type_id as partition key
* get_schema_version retrieves by document_type_id and version
* list_schema_versions returns all versions for a document type
* Large JSON schemas (input_schema, output_schema, extraction_config) serialized properly
* Version ordering preserved in queries

Context references:
* src/entity_extraction/repositories/schema_repository.py (Lines 96-162) - Cosmos DB SchemaVersion operations
* src/entity_extraction/models/schema.py (Lines 52-100) - DocumentTypeVersion model

Dependencies:
* Step 2.1 completion

Implementation:
```python
# Add to TableStorageSchemaRepository class

def _serialize_schema_version(self, version: DocumentTypeVersion) -> dict:
    """Convert DocumentTypeVersion to Table Storage entity."""
    # JSON fields need to be serialized as strings for Table Storage
    entity = {
        "PartitionKey": str(version.document_type_id),
        "RowKey": version.version,
        "id": str(version.id),
        "document_type_id": str(version.document_type_id),
        "document_name": version.document_name or "",
        "version": version.version,
        "input_schema": json.dumps(version.input_schema),  # Serialize to JSON string
        "output_schema": json.dumps(version.output_schema),
        "extraction_config": json.dumps(version.extraction_config),
        "citation_level": version.citation_level.value,
        "confidence_threshold": version.confidence_threshold,
        "created_at": version.created_at.isoformat(),
        "created_by": version.created_by,
        "is_active": version.is_active,
    }
    return entity

def _deserialize_schema_version(self, entity: dict) -> DocumentTypeVersion:
    """Convert Table Storage entity to DocumentTypeVersion."""
    from ..models.enums import CitationLevel
    
    return DocumentTypeVersion(
        id=UUID(entity["id"]),
        document_type_id=UUID(entity["document_type_id"]),
        document_name=entity.get("document_name") or None,
        version=entity["version"],
        input_schema=json.loads(entity["input_schema"]),  # Deserialize JSON string
        output_schema=json.loads(entity["output_schema"]),
        extraction_config=json.loads(entity["extraction_config"]),
        citation_level=CitationLevel(entity["citation_level"]),
        confidence_threshold=float(entity["confidence_threshold"]),
        created_at=datetime.fromisoformat(entity["created_at"]),
        created_by=entity["created_by"],
        is_active=entity["is_active"],
    )

async def create_schema_version(self, version: DocumentTypeVersion) -> DocumentTypeVersion:
    """Create a new schema version."""
    entity = self._serialize_schema_version(version)
    self._schema_versions_table.create_entity(entity)
    return version

async def get_schema_version(
    self, 
    document_type_id: UUID,
    version: str
) -> Optional[DocumentTypeVersion]:
    """Get schema version by document type and version string."""
    try:
        entity = self._schema_versions_table.get_entity(
            partition_key=str(document_type_id),
            row_key=version
        )
        if entity["is_active"]:
            return self._deserialize_schema_version(entity)
        return None
    except ResourceNotFoundError:
        return None

async def list_schema_versions(
    self,
    document_type_id: UUID,
    active_only: bool = True
) -> List[DocumentTypeVersion]:
    """List all versions for a document type."""
    filter_query = f"PartitionKey eq '{str(document_type_id)}'"
    if active_only:
        filter_query += " and is_active eq true"
    
    entities = self._schema_versions_table.query_entities(filter_query)
    versions = [self._deserialize_schema_version(e) for e in entities]
    
    # Sort by created_at descending (Table Storage doesn't guarantee order)
    versions.sort(key=lambda v: v.created_at, reverse=True)
    
    return versions
```

### Step 2.4: Implement query operations (by name, by version, list all)

Complete remaining query operations to match Cosmos DB repository interface.

Files:
* src/entity_extraction/repositories/table_schema_repository.py - Add remaining query methods

Success criteria:
* All query patterns from Cosmos DB repository supported
* Performance acceptable for expected data volumes (<50 types, <5 versions each)
* Proper error handling for not found cases

Dependencies:
* Step 2.2 completion
* Step 2.3 completion

Implementation:
```python
# Add to TableStorageSchemaRepository class

async def update_document_type(self, document_type: DocumentType) -> DocumentType:
    """Update an existing document type."""
    entity = self._serialize_document_type(document_type)
    self._document_types_table.update_entity(entity, mode="replace")
    return document_type

async def deactivate_document_type(self, type_id: UUID) -> bool:
    """Soft delete a document type."""
    doc_type = await self.get_document_type(type_id)
    if doc_type:
        doc_type.is_active = False
        await self.update_document_type(doc_type)
        return True
    return False

async def deactivate_schema_version(
    self, 
    document_type_id: UUID,
    version: str
) -> bool:
    """Soft delete a schema version."""
    schema_version = await self.get_schema_version(document_type_id, version)
    if schema_version:
        schema_version.is_active = False
        entity = self._serialize_schema_version(schema_version)
        self._schema_versions_table.update_entity(entity, mode="replace")
        return True
    return False
```

### Step 2.5: Validate phase changes

Run unit tests for schema repository. Test JSON serialization/deserialization.

Validation commands:
* pytest tests/unit/test_table_schema_repository.py -v
* python -m src.entity_extraction.repositories.table_schema_repository (test serialization)

## Implementation Phase 3: Infrastructure and Provisioning

<!-- parallelizable: true -->

### Step 3.1: Create Table Storage provisioning script

Create script to provision Table Storage tables with proper configuration.

Files:
* scripts/setup_table_storage.py - New provisioning script

Success criteria:
* Creates tables with proper naming convention
* Supports both access key and managed identity authentication
* Idempotent (safe to run multiple times)
* Validates configuration before attempting creation
* Provides clear success/failure messages

Context references:
* scripts/setup_extraction_cosmos.py (Lines 1-162) - Existing Cosmos DB provisioning pattern
* Python instructions for script structure

Dependencies:
* Step 1.1 completion (configuration)
* Step 1.2 completion (azure-data-tables package)

Implementation:
```python
"""
Setup script for Azure Table Storage for entity extraction schema storage.

Creates the required tables with appropriate configuration.

Usage:
    python scripts/setup_table_storage.py
    
Environment variables:
    EXTRACTION_TABLE_STORAGE_ENDPOINT - Table Storage endpoint URL
    EXTRACTION_TABLE_STORAGE_CONNECTION_STRING - Connection string (optional, for dev)
"""

import asyncio
import sys
from typing import Optional

from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential


def create_tables(
    endpoint: Optional[str] = None,
    connection_string: Optional[str] = None,
    table_names: list[str] = None
) -> None:
    """
    Create Table Storage tables.
    
    Args:
        endpoint: Table Storage endpoint URL
        connection_string: Connection string (for dev only)
        table_names: List of table names to create
    """
    if table_names is None:
        table_names = ["DocumentTypes", "SchemaVersions"]
    
    # Initialize Table Service Client
    if connection_string:
        print("Using connection string authentication...")
        service_client = TableServiceClient.from_connection_string(connection_string)
    elif endpoint:
        print("Using managed identity authentication...")
        credential = DefaultAzureCredential()
        service_client = TableServiceClient(endpoint=endpoint, credential=credential)
    else:
        raise ValueError("Must provide either endpoint or connection_string")
    
    try:
        # Create tables
        for table_name in table_names:
            print(f"\nCreating table '{table_name}'...")
            try:
                service_client.create_table(table_name)
                print(f"✓ Table '{table_name}' created successfully")
            except ResourceExistsError:
                print(f"✓ Table '{table_name}' already exists")
        
        print("\n" + "="*60)
        print("✓ Table Storage setup complete")
        print("="*60)
        
    finally:
        service_client.close()


def main():
    """Main entry point."""
    import os
    
    # Get configuration from environment
    endpoint = os.getenv("EXTRACTION_TABLE_STORAGE_ENDPOINT")
    connection_string = os.getenv("EXTRACTION_TABLE_STORAGE_CONNECTION_STRING")
    
    if not endpoint and not connection_string:
        print("ERROR: Must set EXTRACTION_TABLE_STORAGE_ENDPOINT or EXTRACTION_TABLE_STORAGE_CONNECTION_STRING")
        print("\nUsage:")
        print("  export EXTRACTION_TABLE_STORAGE_ENDPOINT='https://your-account.table.core.windows.net/'")
        print("  export EXTRACTION_TABLE_STORAGE_CONNECTION_STRING='...'  # Optional for dev")
        print("  python scripts/setup_table_storage.py")
        sys.exit(1)
    
    print("="*60)
    print("Table Storage Setup for Entity Extraction")
    print("="*60)
    if endpoint:
        print(f"\nEndpoint: {endpoint}")
    print(f"Authentication: {'Connection String' if connection_string else 'Managed Identity'}")
    
    create_tables(endpoint=endpoint, connection_string=connection_string)


if __name__ == "__main__":
    main()
```

### Step 3.2: Update Bicep infrastructure templates

Update infrastructure-as-code to include Table Storage tables in storage account.

Files:
* infrastructure/bicep/main.bicep - Add table storage configuration

Success criteria:
* Storage account configured with Table Storage enabled
* Managed identity has proper role assignments
* Tables created automatically via deployment
* Follows existing Bicep patterns in the file

Context references:
* infrastructure/bicep/main.bicep (Lines 198-235) - Existing storage account configuration
* Azure Bicep Table Storage resource documentation

Dependencies:
* Step 3.1 completion (provisioning script as reference)

Implementation:
```bicep
// Add after blob storage configuration in main.bicep

// Table Service (for schema storage)
resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

// Document Types Table
resource documentTypesTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'DocumentTypes'
}

// Schema Versions Table
resource schemaVersionsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'SchemaVersions'
}
```

### Step 3.3: Add managed identity permissions for Table Storage

Configure RBAC roles for App Service managed identity to access Table Storage.

Files:
* infrastructure/bicep/main.bicep - Add role assignments

Success criteria:
* App Service managed identity has Storage Table Data Contributor role
* Role assignment scoped to storage account
* Follows principle of least privilege

Context references:
* infrastructure/bicep/main.bicep - Existing managed identity patterns
* Azure RBAC role definitions for Table Storage

Dependencies:
* Step 3.2 completion

Implementation:
```bicep
// Add role assignment for Table Storage access
resource tableDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appServicePlan.id, 'StorageTableDataContributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3') // Storage Table Data Contributor
    principalId: appServicePlan.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

### Step 3.4: Validate phase changes

Test provisioning script in development environment. Verify Bicep template syntax.

Validation commands:
* python scripts/setup_table_storage.py (with dev environment variables)
* az bicep build --file infrastructure/bicep/main.bicep

## Implementation Phase 4: API Integration

<!-- parallelizable: false -->

### Step 4.1: Update dependency injection in FastAPI routes

Replace Cosmos DB repository injection with Table Storage repository.

Files:
* src/api/routes/extraction.py - Update dependency functions
* src/api/routes/onboarding.py - Update dependency functions

Success criteria:
* Dependency injection uses new TableStorageSchemaRepository
* No changes to API endpoint signatures or responses
* Backward compatibility maintained during transition

Context references:
* src/api/routes/extraction.py (Lines 28-62) - Current Cosmos DB dependency injection
* src/api/routes/onboarding.py (Lines 34-70) - Similar dependency pattern

Dependencies:
* Step 2.5 completion (Table Storage repository complete)

Implementation:
```python
# Update in src/api/routes/extraction.py

# Remove old Cosmos DB dependencies
# def get_cosmos_database():
#     """Get Cosmos DB database client."""
#     cosmos_client = get_cosmos_client()
#     config = get_config()
#     return cosmos_client.get_database_client(config.cosmos_database)

# Add new Table Storage dependency
def get_schema_repository():
    """Get schema repository (Table Storage)."""
    from src.entity_extraction.repositories.table_schema_repository import TableStorageSchemaRepository
    return TableStorageSchemaRepository()

# Remove old dependency parameter
# def get_schema_repository(database=Depends(get_cosmos_database)):
#     """Get schema repository."""
#     return SchemaRepository(database)

# Update all usages to remove database dependency
def get_schema_service(schema_repo=Depends(get_schema_repository)):
    """Get schema service."""
    return SchemaService(schema_repo)

# Similar updates for extraction_model_repository and extraction_repository
# (these may stay on Cosmos DB or migrate separately)
```

Repeat similar changes in src/api/routes/onboarding.py.

### Step 4.2: Update SchemaService to use new repository

Ensure SchemaService works with both repository implementations.

Files:
* src/entity_extraction/services/schema_service.py - Verify compatibility

Success criteria:
* SchemaService methods work with Table Storage repository
* No changes needed if repository interface unchanged
* Type hints updated if necessary

Context references:
* src/entity_extraction/services/schema_service.py (Lines 1-80) - Existing service implementation

Dependencies:
* Step 4.1 completion

Implementation:
Verify schema_service.py uses repository through interface only (no Cosmos DB-specific code). If interface maintained correctly, no changes needed. Add type hint if using abstract base:

```python
# If creating abstract base class for repository interface:
from abc import ABC, abstractmethod

class SchemaRepository(ABC):
    """Abstract base for schema repository implementations."""
    
    @abstractmethod
    async def create_document_type(self, document_type: DocumentType) -> DocumentType:
        ...
    
    # ... other abstract methods
```

### Step 4.3: Update orchestration interface integration

Update orchestration workflow integration to use Table Storage repository.

Files:
* src/entity_extraction/services/orchestration_interface.py - Update initialization

Success criteria:
* Workflow integration uses new repository
* No breaking changes to orchestration API
* Configuration loaded properly

Context references:
* src/entity_extraction/services/orchestration_interface.py (Lines 73-95) - Current initialization pattern

Dependencies:
* Step 4.1 completion

Implementation:
```python
# Update in src/entity_extraction/services/orchestration_interface.py

async def extract_document_for_workflow(
    document_id: str,
    document_content: bytes,
    document_type: str,
    schema_version: str = "1.0.0"
) -> Dict[str, Any]:
    logger.info("ORCHESTRATION INTERFACE: extract_document_for_workflow")
    logger.info("=" * 60)
    
    # Replace Cosmos DB initialization with Table Storage
    # OLD:
    # cosmos_client = get_cosmos_client()
    # database = cosmos_client.get_database_client(config.cosmos_database)
    # schema_repo = SchemaRepository(database)
    
    # NEW:
    from ..repositories.table_schema_repository import TableStorageSchemaRepository
    schema_repo = TableStorageSchemaRepository()
    
    # Rest of function remains the same
    ...
```

### Step 4.4: Validate phase changes

Run API integration tests. Test end-to-end extraction workflow.

Validation commands:
* pytest tests/integration/test_extraction_api.py -v
* pytest tests/e2e/test_extraction_workflow.py -v

## Implementation Phase 5: Data Migration

<!-- parallelizable: false -->

### Step 5.1: Create migration script to export from Cosmos DB

Create script to export all schema data from Cosmos DB to JSON files for backup and migration.

Files:
* scripts/migrate_cosmos_to_table_storage.py - New migration script (export part)

Success criteria:
* Exports all document types from extraction_schemas container
* Exports all schema versions from extraction_schemas container
* Preserves all fields including JSON schemas
* Creates timestamped backup directory
* Validates exported data integrity

Context references:
* src/entity_extraction/repositories/schema_repository.py (Lines 1-162) - Cosmos DB query patterns
* scripts/setup_extraction_cosmos.py - Connection pattern

Dependencies:
* None (reads from existing Cosmos DB)

Implementation:
```python
"""
Migration script to migrate schemas from Cosmos DB to Azure Table Storage.

Usage:
    python scripts/migrate_cosmos_to_table_storage.py export
    python scripts/migrate_cosmos_to_table_storage.py import
    python scripts/migrate_cosmos_to_table_storage.py validate
    
Environment variables:
    # Source (Cosmos DB)
    EXTRACTION_COSMOS_ENDPOINT
    EXTRACTION_COSMOS_KEY
    EXTRACTION_COSMOS_DATABASE
    
    # Target (Table Storage)
    EXTRACTION_TABLE_STORAGE_ENDPOINT
    EXTRACTION_TABLE_STORAGE_CONNECTION_STRING
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from azure.cosmos import CosmosClient
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential


class SchemaDataMigrator:
    """Handles migration of schema data from Cosmos DB to Table Storage."""
    
    def __init__(self):
        """Initialize migrator with source and target clients."""
        # Source: Cosmos DB
        cosmos_endpoint = os.getenv("EXTRACTION_COSMOS_ENDPOINT")
        cosmos_key = os.getenv("EXTRACTION_COSMOS_KEY")
        cosmos_database = os.getenv("EXTRACTION_COSMOS_DATABASE", "extraction_db")
        
        if not cosmos_endpoint:
            raise ValueError("EXTRACTION_COSMOS_ENDPOINT required for export")
        
        if cosmos_key:
            self.cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
        else:
            self.cosmos_client = CosmosClient(cosmos_endpoint, credential=DefaultAzureCredential())
        
        self.cosmos_database = self.cosmos_client.get_database_client(cosmos_database)
        self.cosmos_container = self.cosmos_database.get_container_client("extraction_schemas")
        
        # Target: Table Storage
        table_endpoint = os.getenv("EXTRACTION_TABLE_STORAGE_ENDPOINT")
        table_connection_string = os.getenv("EXTRACTION_TABLE_STORAGE_CONNECTION_STRING")
        
        if table_connection_string:
            self.table_service = TableServiceClient.from_connection_string(table_connection_string)
        elif table_endpoint:
            self.table_service = TableServiceClient(endpoint=table_endpoint, credential=DefaultAzureCredential())
        else:
            self.table_service = None  # For export-only mode
        
        # Backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = Path(f"./migration_backup_{timestamp}")
        self.backup_dir.mkdir(exist_ok=True)
    
    def export_from_cosmos(self) -> tuple[List[Dict], List[Dict]]:
        """
        Export all schema data from Cosmos DB.
        
        Returns:
            Tuple of (document_types, schema_versions)
        """
        print("="*60)
        print("EXPORTING FROM COSMOS DB")
        print("="*60)
        
        # Query all document types
        doc_types_query = "SELECT * FROM c WHERE c.type = 'document_type'"
        doc_types = list(self.cosmos_container.query_items(
            query=doc_types_query,
            enable_cross_partition_query=True
        ))
        
        print(f"\n✓ Exported {len(doc_types)} document types")
        
        # Query all schema versions
        versions_query = "SELECT * FROM c WHERE c.type = 'schema_version'"
        schema_versions = list(self.cosmos_container.query_items(
            query=versions_query,
            enable_cross_partition_query=True
        ))
        
        print(f"✓ Exported {len(schema_versions)} schema versions")
        
        # Save to backup files
        doc_types_file = self.backup_dir / "document_types.json"
        with open(doc_types_file, 'w') as f:
            json.dump(doc_types, f, indent=2, default=str)
        print(f"✓ Saved to {doc_types_file}")
        
        versions_file = self.backup_dir / "schema_versions.json"
        with open(versions_file, 'w') as f:
            json.dump(schema_versions, f, indent=2, default=str)
        print(f"✓ Saved to {versions_file}")
        
        return doc_types, schema_versions
```

### Step 5.2: Create migration script to import to Table Storage

Add import functionality to migration script to write data to Table Storage.

Files:
* scripts/migrate_cosmos_to_table_storage.py - Add import methods

Success criteria:
* Imports all document types to DocumentTypes table
* Imports all schema versions to SchemaVersions table
* Maintains proper partition and row keys
* Handles JSON serialization for complex fields
* Reports success/failure for each entity

Dependencies:
* Step 5.1 completion
* Step 3.1 completion (Table Storage tables exist)

Implementation:
```python
# Add to SchemaDataMigrator class

    def import_to_table_storage(
        self, 
        doc_types: List[Dict],
        schema_versions: List[Dict]
    ) -> tuple[int, int]:
        """
        Import schema data to Table Storage.
        
        Args:
            doc_types: List of document type documents from Cosmos DB
            schema_versions: List of schema version documents from Cosmos DB
        
        Returns:
            Tuple of (doc_types_imported, versions_imported)
        """
        if not self.table_service:
            raise ValueError("Table Storage client not configured. Set EXTRACTION_TABLE_STORAGE_ENDPOINT or CONNECTION_STRING")
        
        print("\n" + "="*60)
        print("IMPORTING TO TABLE STORAGE")
        print("="*60)
        
        # Get table clients
        doc_types_table = self.table_service.get_table_client("DocumentTypes")
        versions_table = self.table_service.get_table_client("SchemaVersions")
        
        # Import document types
        print(f"\nImporting {len(doc_types)} document types...")
        doc_types_imported = 0
        for doc_type in doc_types:
            try:
                entity = {
                    "PartitionKey": "DOCTYPE",
                    "RowKey": doc_type["id"],
                    "id": doc_type["id"],
                    "name": doc_type["name"],
                    "description": doc_type.get("description", ""),
                    "created_at": doc_type["created_at"],
                    "created_by": doc_type["created_by"],
                    "is_active": doc_type["is_active"],
                }
                doc_types_table.create_entity(entity)
                doc_types_imported += 1
                print(f"  ✓ {doc_type['name']} ({doc_type['id']})")
            except Exception as e:
                print(f"  ✗ Failed to import {doc_type['name']}: {e}")
        
        print(f"\n✓ Imported {doc_types_imported}/{len(doc_types)} document types")
        
        # Import schema versions
        print(f"\nImporting {len(schema_versions)} schema versions...")
        versions_imported = 0
        for version in schema_versions:
            try:
                entity = {
                    "PartitionKey": version["document_type_id"],
                    "RowKey": version["version"],
                    "id": version["id"],
                    "document_type_id": version["document_type_id"],
                    "document_name": version.get("document_name", ""),
                    "version": version["version"],
                    "input_schema": json.dumps(version["input_schema"]),
                    "output_schema": json.dumps(version["output_schema"]),
                    "extraction_config": json.dumps(version["extraction_config"]),
                    "citation_level": version["citation_level"],
                    "confidence_threshold": version["confidence_threshold"],
                    "created_at": version["created_at"],
                    "created_by": version["created_by"],
                    "is_active": version["is_active"],
                }
                versions_table.create_entity(entity)
                versions_imported += 1
                print(f"  ✓ {version.get('document_name', version['document_type_id'])} v{version['version']}")
            except Exception as e:
                print(f"  ✗ Failed to import version {version['version']}: {e}")
        
        print(f"\n✓ Imported {versions_imported}/{len(schema_versions)} schema versions")
        
        return doc_types_imported, versions_imported
```

### Step 5.3: Add validation and rollback capabilities

Add validation to compare source and target data, and rollback capability.

Files:
* scripts/migrate_cosmos_to_table_storage.py - Add validate and rollback methods

Success criteria:
* Validation compares counts and key fields
* Reports discrepancies clearly
* Rollback clears Table Storage data if needed
* Safe to re-run validation multiple times

Dependencies:
* Step 5.2 completion

Implementation:
```python
# Add to SchemaDataMigrator class

    def validate_migration(self) -> bool:
        """
        Validate migration by comparing Cosmos DB and Table Storage.
        
        Returns:
            True if validation passes, False otherwise
        """
        print("\n" + "="*60)
        print("VALIDATING MIGRATION")
        print("="*60)
        
        # Export from Cosmos DB
        cosmos_doc_types, cosmos_versions = self.export_from_cosmos()
        
        # Query Table Storage
        doc_types_table = self.table_service.get_table_client("DocumentTypes")
        versions_table = self.table_service.get_table_client("SchemaVersions")
        
        table_doc_types = list(doc_types_table.list_entities())
        table_versions = list(versions_table.list_entities())
        
        print(f"\nCounts:")
        print(f"  Document Types: Cosmos={len(cosmos_doc_types)}, Table={len(table_doc_types)}")
        print(f"  Schema Versions: Cosmos={len(cosmos_versions)}, Table={len(table_versions)}")
        
        # Validate counts
        valid = True
        if len(cosmos_doc_types) != len(table_doc_types):
            print("  ✗ Document type count mismatch!")
            valid = False
        if len(cosmos_versions) != len(table_versions):
            print("  ✗ Schema version count mismatch!")
            valid = False
        
        if valid:
            print("\n✓ Validation PASSED")
        else:
            print("\n✗ Validation FAILED")
        
        return valid

    def rollback_table_storage(self) -> None:
        """
        Rollback by deleting all entities from Table Storage.
        
        WARNING: This will delete all schema data from Table Storage!
        """
        response = input("\n⚠️  WARNING: This will DELETE all data from Table Storage tables. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Rollback cancelled.")
            return
        
        print("\n" + "="*60)
        print("ROLLING BACK TABLE STORAGE")
        print("="*60)
        
        doc_types_table = self.table_service.get_table_client("DocumentTypes")
        versions_table = self.table_service.get_table_client("SchemaVersions")
        
        # Delete document types
        entities = list(doc_types_table.list_entities())
        for entity in entities:
            doc_types_table.delete_entity(entity["PartitionKey"], entity["RowKey"])
        print(f"✓ Deleted {len(entities)} document types")
        
        # Delete schema versions
        entities = list(versions_table.list_entities())
        for entity in entities:
            versions_table.delete_entity(entity["PartitionKey"], entity["RowKey"])
        print(f"✓ Deleted {len(entities)} schema versions")
        
        print("\n✓ Rollback complete")


# Add main function to handle commands
def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python migrate_cosmos_to_table_storage.py [export|import|validate|rollback|migrate]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    migrator = SchemaDataMigrator()
    
    if command == "export":
        migrator.export_from_cosmos()
    elif command == "import":
        # Load from most recent backup
        backup_dirs = sorted(Path(".").glob("migration_backup_*"), reverse=True)
        if not backup_dirs:
            print("No backup found. Run 'export' first.")
            sys.exit(1)
        backup_dir = backup_dirs[0]
        with open(backup_dir / "document_types.json") as f:
            doc_types = json.load(f)
        with open(backup_dir / "schema_versions.json") as f:
            versions = json.load(f)
        migrator.import_to_table_storage(doc_types, versions)
    elif command == "validate":
        migrator.validate_migration()
    elif command == "rollback":
        migrator.rollback_table_storage()
    elif command == "migrate":
        # Full migration: export -> import -> validate
        doc_types, versions = migrator.export_from_cosmos()
        migrator.import_to_table_storage(doc_types, versions)
        migrator.validate_migration()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 5.4: Validate phase changes

Test migration with sample data. Verify data integrity after migration.

Validation commands:
* python scripts/migrate_cosmos_to_table_storage.py export
* python scripts/migrate_cosmos_to_table_storage.py import
* python scripts/migrate_cosmos_to_table_storage.py validate

## Implementation Phase 6: Testing and Documentation

<!-- parallelizable: false -->

### Step 6.1: Update unit tests for Table Storage repository

Create/update unit tests for the new Table Storage repository.

Files:
* tests/unit/test_table_schema_repository.py - New test file

Success criteria:
* Tests cover all CRUD operations
* Tests verify JSON serialization/deserialization
* Tests use mocks or test storage account
* Tests check error handling

Dependencies:
* Step 2.5 completion (repository implementation)

Implementation:
```python
"""Unit tests for Table Storage schema repository."""

import json
import pytest
from uuid import uuid4
from datetime import datetime

from src.entity_extraction.repositories.table_schema_repository import TableStorageSchemaRepository
from src.entity_extraction.models import DocumentType, DocumentTypeVersion, CitationLevel


@pytest.fixture
def mock_table_service(monkeypatch):
    """Mock Table Storage service client."""
    # Mock implementation or use Azure Storage Emulator
    pass


@pytest.mark.asyncio
async def test_create_document_type(mock_table_service):
    """Test creating a document type."""
    repo = TableStorageSchemaRepository()
    
    doc_type = DocumentType(
        name="Test Document",
        description="Test description",
        created_by="test@example.com"
    )
    
    result = await repo.create_document_type(doc_type)
    
    assert result.id == doc_type.id
    assert result.name == "Test Document"


@pytest.mark.asyncio
async def test_get_document_type_by_name(mock_table_service):
    """Test retrieving document type by name."""
    repo = TableStorageSchemaRepository()
    
    # Setup: create a document type
    doc_type = DocumentType(
        name="Bank Statement",
        created_by="test@example.com"
    )
    await repo.create_document_type(doc_type)
    
    # Test: retrieve by name (case-insensitive)
    result = await repo.get_document_type_by_name("bank statement")
    
    assert result is not None
    assert result.name == "Bank Statement"


@pytest.mark.asyncio
async def test_schema_version_json_serialization(mock_table_service):
    """Test JSON field serialization for schema versions."""
    repo = TableStorageSchemaRepository()
    
    doc_type_id = uuid4()
    input_schema = {"type": "object", "properties": {"field1": {"type": "string"}}}
    
    version = DocumentTypeVersion(
        document_type_id=doc_type_id,
        version="1.0.0",
        input_schema=input_schema,
        output_schema={},
        extraction_config={},
        created_by="test@example.com"
    )
    
    # Create and retrieve
    await repo.create_schema_version(version)
    result = await repo.get_schema_version(doc_type_id, "1.0.0")
    
    # Verify JSON fields preserved
    assert result.input_schema == input_schema
    assert isinstance(result.input_schema, dict)


# Additional tests for list operations, error handling, etc.
```

### Step 6.2: Update integration tests

Update integration tests to work with Table Storage repository.

Files:
* tests/integration/test_extraction_api.py - Update existing tests
* tests/integration/test_schema_migration.py - New migration test

Success criteria:
* Integration tests pass with Table Storage
* Tests verify end-to-end API functionality
* Migration test validates full export/import cycle

Dependencies:
* Step 6.1 completion

Implementation:
Add to tests/integration/test_schema_migration.py:
```python
"""Integration test for schema migration from Cosmos DB to Table Storage."""

import pytest
from uuid import uuid4

from src.entity_extraction.repositories.schema_repository import SchemaRepository  # Cosmos
from src.entity_extraction.repositories.table_schema_repository import TableStorageSchemaRepository
from src.entity_extraction.models import DocumentType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_schema_migration_roundtrip():
    """Test complete migration cycle: Cosmos -> export -> Table Storage."""
    # Create test data in Cosmos DB
    cosmos_repo = SchemaRepository(...)  # Initialize with test database
    
    doc_type = DocumentType(
        name=f"Test Migration {uuid4().hex[:8]}",
        created_by="test@example.com"
    )
    await cosmos_repo.create_document_type(doc_type)
    
    # Export and import via migration script
    # ... (call migration functions)
    
    # Verify in Table Storage
    table_repo = TableStorageSchemaRepository()
    result = await table_repo.get_document_type_by_name(doc_type.name)
    
    assert result is not None
    assert result.name == doc_type.name
    assert result.id == doc_type.id
```

### Step 6.3: Create migration runbook documentation

Create detailed runbook for production migration.

Files:
* docs/guides/cosmos-to-table-storage-migration.md - New migration runbook

Success criteria:
* Clear step-by-step production migration procedure
* Pre-migration checklist included
* Rollback procedure documented
* Timeline estimates provided

Dependencies:
* Step 5.3 completion (migration tooling complete)

Implementation:
Create docs/guides/cosmos-to-table-storage-migration.md with content including:
* Pre-migration checklist (backup, verify environment, test in staging)
* Migration steps with commands
* Validation procedures
* Rollback instructions
* Post-migration cleanup (decommission Cosmos containers)
* Troubleshooting section

### Step 6.4: Update architecture documentation

Update architecture diagrams and documentation to reflect Table Storage usage.

Files:
* docs/architecture/azure-architecture.md - Update service list and diagrams
* docs/architecture/component_overview.md - Update storage section
* specs/005-document-extraction-schema/plan.md - Update storage references

Success criteria:
* All architecture docs reference Table Storage instead of Cosmos DB for schemas
* Diagrams updated to show Table Storage
* Cost estimates updated

Context references:
* docs/architecture/azure-architecture.md (Lines 100-150) - Service descriptions and diagrams
* specs/005-document-extraction-schema/plan.md (Lines 16-20) - Storage technology references

Dependencies:
* All previous steps completed

Implementation:
Update service descriptions:
```markdown
| Service | Purpose |
|---------|----------|
| **Azure Table Storage** | Store document type schemas and versions |
| **Azure Cosmos DB** | Store cases, documents, entities, extraction results |
```

### Step 6.5: Validate phase changes

Run full test suite. Review documentation completeness.

Validation commands:
* pytest tests/ -v --cov=src.entity_extraction
* markdownlint docs/guides/cosmos-to-table-storage-migration.md

## Implementation Phase 7: Validation

<!-- parallelizable: false -->

### Step 7.1: Run full project validation

Execute all validation commands for the project.

Validation commands:
* ruff check src/entity_extraction/ src/api/routes/
* mypy src/entity_extraction/ src/api/routes/
* pytest tests/ -v --cov=src.entity_extraction --cov-report=term-missing

### Step 7.2: Fix minor validation issues

Iterate on lint errors and type hints. Apply fixes directly when corrections are straightforward and isolated.

### Step 7.3: Report blocking issues

When validation failures require changes beyond minor fixes:
* Document the issues and affected files.
* Provide the user with next steps.
* Recommend additional research and planning rather than inline fixes.
* Avoid large-scale refactoring within this phase.

## Dependencies

* Python 3.11+
* azure-data-tables >= 12.5.0
* Existing entity extraction module with Cosmos DB repository
* Azure Storage Account with Table Storage enabled
* Access to existing Cosmos DB data for migration

## Success Criteria

* All CRUD operations work through Table Storage repository
* API responses unchanged (backward compatible)
* Migration script successfully transfers data with validation
* Unit and integration test coverage maintained
* Documentation updated and accurate
* Production migration runbook reviewed and approved
* Cost reduction verified post-migration
