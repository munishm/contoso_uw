#!/usr/bin/env python3
"""
Infrastructure Provisioning Script for HSBC IWPB Underwriting POC.

This script creates all required Cosmos DB databases, containers, and Blob Storage containers
for the application. It uses Azure AD authentication (DefaultAzureCredential).

Usage:
    python scripts/provision_infrastructure.py [--dry-run] [--cosmos-only] [--blob-only]

Options:
    --dry-run       Show what would be created without actually creating
    --cosmos-only   Only provision Cosmos DB resources
    --blob-only     Only provision Blob Storage resources

Environment Variables Required:
    COSMOS_ENDPOINT           - Cosmos DB account endpoint
    COSMOS_DATABASE_NAME      - Database name (default: underwriting)
    BLOB_ACCOUNT_URL          - Blob Storage account URL
    BLOB_CONTAINER_NAME       - Main blob container name (default: documents)
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv


# Cosmos DB Configuration
COSMOS_DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME", "underwriting")

# Container definitions with partition keys
COSMOS_CONTAINERS = {
    # API Module Containers
    "cases": {
        "partition_key": "/case_id",
        "description": "Stores case records with underwriting case data"
    },
    "documents": {
        "partition_key": "/case_id",
        "description": "Stores document records with classification and extraction results"
    },
    "entities": {
        "partition_key": "/document_id",
        "description": "Stores extracted entities from documents"
    },
    "summaries": {
        "partition_key": "/document_id",
        "description": "Stores document summaries"
    },
    "counters": {
        "partition_key": "/counter_id",
        "description": "Stores atomic counters for ID generation"
    },
    # Extraction Module Containers
    "extraction_schemas": {
        "partition_key": "/document_type_id",
        "description": "Stores extraction schema definitions per document type"
    },
    "extraction_models": {
        "partition_key": "/partition_key",
        "description": "Stores extraction model configurations"
    },
}

# Blob Storage Configuration
BLOB_CONTAINERS = {
    "documents": {
        "description": "Main document storage for uploaded and processed documents"
    },
}


async def provision_cosmos_db(
    endpoint: str,
    database_name: str,
    dry_run: bool = False
):
    """Provision Cosmos DB database and containers."""
    from azure.cosmos.aio import CosmosClient
    from azure.cosmos import PartitionKey
    from azure.cosmos.exceptions import CosmosResourceExistsError
    from azure.identity.aio import DefaultAzureCredential
    
    print("\n" + "=" * 70)
    print("COSMOS DB PROVISIONING")
    print("=" * 70)
    print(f"\nEndpoint: {endpoint}")
    print(f"Database: {database_name}")
    print(f"Containers to create: {len(COSMOS_CONTAINERS)}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No resources will be created\n")
        for name, config in COSMOS_CONTAINERS.items():
            print(f"  [DRY-RUN] Would create container: {name}")
            print(f"            Partition Key: {config['partition_key']}")
            print(f"            Description: {config['description']}")
            print()
        return
    
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    
    try:
        # Create or get database
        print(f"\n1. Creating/Getting database: {database_name}")
        try:
            database = await client.create_database(database_name)
            print(f"   ✓ Created database: {database_name}")
        except CosmosResourceExistsError:
            database = client.get_database_client(database_name)
            print(f"   ℹ Database already exists: {database_name}")
        
        # Create containers
        print(f"\n2. Creating containers...")
        for name, config in COSMOS_CONTAINERS.items():
            try:
                partition_key = PartitionKey(path=config["partition_key"])
                container = await database.create_container(
                    id=name,
                    partition_key=partition_key,
                    offer_throughput=400  # Minimum RU/s
                )
                print(f"   ✓ Created container: {name} (partition: {config['partition_key']})")
            except CosmosResourceExistsError:
                print(f"   ℹ Container already exists: {name}")
            except Exception as e:
                print(f"   ✗ Failed to create container {name}: {e}")
        
        # Initialize counters if needed
        print(f"\n3. Initializing counters...")
        try:
            counters_container = database.get_container_client("counters")
            
            # Initialize case counter
            try:
                await counters_container.create_item({
                    "id": "case_counter",
                    "counter_id": "case_counter",
                    "counter_type": "case",
                    "prefix": "CASE",
                    "current_value": 0,
                    "format": "CASE-{year}{month:02d}-{sequence:06d}"
                })
                print(f"   ✓ Initialized case counter")
            except CosmosResourceExistsError:
                print(f"   ℹ Case counter already exists")
        except Exception as e:
            print(f"   ✗ Failed to initialize counters: {e}")
        
        print("\n" + "=" * 70)
        print("Cosmos DB provisioning completed!")
        print("=" * 70)
        
    finally:
        await client.close()
        await credential.close()


async def provision_blob_storage(
    account_url: str,
    dry_run: bool = False
):
    """Provision Blob Storage containers."""
    from azure.storage.blob.aio import BlobServiceClient
    from azure.core.exceptions import ResourceExistsError
    from azure.identity.aio import DefaultAzureCredential
    
    print("\n" + "=" * 70)
    print("BLOB STORAGE PROVISIONING")
    print("=" * 70)
    print(f"\nAccount URL: {account_url}")
    print(f"Containers to create: {len(BLOB_CONTAINERS)}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No resources will be created\n")
        for name, config in BLOB_CONTAINERS.items():
            print(f"  [DRY-RUN] Would create blob container: {name}")
            print(f"            Description: {config['description']}")
            print()
        return
    
    credential = DefaultAzureCredential()
    client = BlobServiceClient(account_url, credential=credential)
    
    try:
        print(f"\n1. Creating blob containers...")
        for name, config in BLOB_CONTAINERS.items():
            try:
                container = await client.create_container(name)
                print(f"   ✓ Created blob container: {name}")
            except ResourceExistsError:
                print(f"   ℹ Blob container already exists: {name}")
            except Exception as e:
                print(f"   ✗ Failed to create blob container {name}: {e}")
        
        print("\n" + "=" * 70)
        print("Blob Storage provisioning completed!")
        print("=" * 70)
        
    finally:
        await client.close()
        await credential.close()


def print_terraform_output():
    """Print Terraform/Bicep configuration for reference."""
    print("\n" + "=" * 70)
    print("INFRASTRUCTURE AS CODE REFERENCE")
    print("=" * 70)
    
    print("\n# Cosmos DB Containers (for Terraform/Bicep)")
    print("# Database: underwriting")
    print("containers = [")
    for name, config in COSMOS_CONTAINERS.items():
        print(f'  {{ name = "{name}", partition_key = "{config["partition_key"]}" }},')
    print("]")
    
    print("\n# Blob Containers")
    print("blob_containers = [")
    for name in BLOB_CONTAINERS:
        print(f'  "{name}",')
    print("]")


async def main(
    dry_run: bool = False,
    cosmos_only: bool = False,
    blob_only: bool = False
):
    """Main provisioning function."""
    # Load environment variables
    load_dotenv()
    
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    blob_account_url = os.getenv("BLOB_ACCOUNT_URL")
    database_name = os.getenv("COSMOS_DATABASE_NAME", "underwriting")
    
    print("\n" + "=" * 70)
    print("HSBC IWPB Underwriting - Infrastructure Provisioning")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Cosmos Endpoint:  {cosmos_endpoint or 'NOT SET'}")
    print(f"  Database Name:    {database_name}")
    print(f"  Blob Account URL: {blob_account_url or 'NOT SET'}")
    print(f"  Dry Run:          {dry_run}")
    
    if not cosmos_only and not blob_only:
        cosmos_only = True
        blob_only = True
    
    # Provision Cosmos DB
    if cosmos_only and cosmos_endpoint:
        await provision_cosmos_db(
            endpoint=cosmos_endpoint,
            database_name=database_name,
            dry_run=dry_run
        )
    elif cosmos_only and not cosmos_endpoint:
        print("\n⚠️  Skipping Cosmos DB: COSMOS_ENDPOINT not set")
    
    # Provision Blob Storage
    if blob_only and blob_account_url:
        await provision_blob_storage(
            account_url=blob_account_url,
            dry_run=dry_run
        )
    elif blob_only and not blob_account_url:
        print("\n⚠️  Skipping Blob Storage: BLOB_ACCOUNT_URL not set")
    
    # Print IaC reference
    print_terraform_output()
    
    print("\n" + "=" * 70)
    print("Provisioning script completed!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Provision Azure infrastructure for HSBC IWPB Underwriting"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating"
    )
    parser.add_argument(
        "--cosmos-only",
        action="store_true",
        help="Only provision Cosmos DB resources"
    )
    parser.add_argument(
        "--blob-only",
        action="store_true",
        help="Only provision Blob Storage resources"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(
        dry_run=args.dry_run,
        cosmos_only=args.cosmos_only,
        blob_only=args.blob_only
    ))
