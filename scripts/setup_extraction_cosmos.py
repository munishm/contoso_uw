# """
# Setup script for Cosmos DB containers for entity extraction.

# Creates the required database and containers with appropriate partition keys.

# Usage:
#     python scripts/setup_extraction_cosmos.py
    
# Environment variables:
#     EXTRACTION_COSMOS_ENDPOINT - Cosmos DB endpoint URL
#     EXTRACTION_COSMOS_KEY - Cosmos DB access key (optional if using managed identity)
# """


import asyncio
import sys
from typing import Optional

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from azure.identity.aio import DefaultAzureCredential


async def create_database_and_containers(
    endpoint: str,
    key: Optional[str] = None,
    database_name: str = "extraction_db"
) -> None:
    """
    Create Cosmos DB database and containers.
    
    Args:
        endpoint: Cosmos DB endpoint URL
        key: Cosmos DB access key (None for managed identity)
        database_name: Name of the database to create
    """
    # Initialize Cosmos client
    if key:
        print("Using access key authentication...")
        client = CosmosClient(endpoint, credential=key)
    else:
        print("Using managed identity authentication...")
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential=credential)
    
    try:
        # Get existing database (skipping creation - requires only data plane permissions)
        print(f"\nConnecting to database '{database_name}'...")
        database = client.get_database_client(database_name)
        print(f"✓ Connected to database '{database_name}'")
        
        # Create extraction_schemas container
        print("\nCreating 'extraction_schemas' container...")
        try:
            await database.create_container(
                id="extraction_schemas",
                partition_key=PartitionKey(path="/document_type_id"),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [
                        {"path": "/*"}
                    ],
                    "excludedPaths": [
                        {"path": "/input_schema/*"},
                        {"path": "/output_schema/*"}
                    ]
                }
            )
            print("✓ Container 'extraction_schemas' created successfully")
            print("  - Partition key: /document_type_id")
            print("  - Indexes: All paths except schemas")
        except exceptions.CosmosResourceExistsError:
            print("✓ Container 'extraction_schemas' already exists")
        
        # Create extraction_models container
        print("\nCreating 'extraction_models' container...")
        try:
            await database.create_container(
                id="extraction_models",
                partition_key=PartitionKey(path="/type"),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [
                        {"path": "/*"}
                    ]
                }
            )
            print("✓ Container 'extraction_models' created successfully")
            print("  - Partition key: /type")
        except exceptions.CosmosResourceExistsError:
            print("✓ Container 'extraction_models' already exists")
        
        # Create extraction_results container
        print("\nCreating 'extraction_results' container...")
        try:
            await database.create_container(
                id="extraction_results",
                partition_key=PartitionKey(path="/document_id"),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [
                        {"path": "/*"}
                    ],
                    "excludedPaths": [
                        {"path": "/fields/*"}
                    ]
                }
            )
            print("✓ Container 'extraction_results' created successfully")
            print("  - Partition key: /document_id")
            print("  - Indexes: All paths except fields array")
        except exceptions.CosmosResourceExistsError:
            print("✓ Container 'extraction_results' already exists")
        
        print("\n" + "="*60)
        print("✓ Setup completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Register extraction models using POST /api/v1/extraction/models")
        print("2. Create document types using POST /api/v1/extraction/document-types")
        print("3. Create schema versions using POST /api/v1/extraction/document-types/{id}/versions")
        print("4. Test extraction with POST /api/v1/extraction/extract")
        
    finally:
        await client.close()
        if not key:
            await credential.close()


async def main():
    """Main entry point."""
    import os
    
    # Get configuration from environment
    endpoint = os.getenv("EXTRACTION_COSMOS_ENDPOINT")
    key = os.getenv("EXTRACTION_COSMOS_KEY")
    database_name = os.getenv("EXTRACTION_COSMOS_DATABASE", "extraction_db")
    
    if not endpoint:
        print("ERROR: EXTRACTION_COSMOS_ENDPOINT environment variable is required")
        print("\nUsage:")
        print("  export EXTRACTION_COSMOS_ENDPOINT='https://your-account.documents.azure.com:443/'")
        print("  export EXTRACTION_COSMOS_KEY='your-key'  # Optional for managed identity")
        print("  python scripts/setup_extraction_cosmos.py")
        sys.exit(1)
    
    print("="*60)
    print("Cosmos DB Setup for Entity Extraction")
    print("="*60)
    print(f"\nEndpoint: {endpoint}")
    print(f"Database: {database_name}")
    print(f"Authentication: {'Access Key' if key else 'Managed Identity'}")
    
    await create_database_and_containers(endpoint, key, database_name)


if __name__ == "__main__":
    asyncio.run(main())
