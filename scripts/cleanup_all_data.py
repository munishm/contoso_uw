#!/usr/bin/env python3
"""
Cleanup script to delete all cases and associated documents from Cosmos DB and Blob Storage.

This script will:
1. List all cases from Cosmos DB
2. For each case, delete all associated documents from Cosmos DB
3. Delete the case from Cosmos DB
4. Delete all blobs under the case folder from Azure Blob Storage

Usage:
    python scripts/cleanup_all_data.py [--dry-run] [--case-id <case_id>]

Options:
    --dry-run       Show what would be deleted without actually deleting
    --case-id       Delete only a specific case (optional)
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient


async def get_cosmos_client():
    """Initialize Cosmos DB client with AAD auth."""
    endpoint = os.getenv("COSMOS_ENDPOINT")
    if not endpoint:
        raise ValueError("COSMOS_ENDPOINT environment variable not set")
    
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    return client, credential


async def get_blob_service_client():
    """Initialize Blob Service client with AAD auth."""
    account_url = os.getenv("BLOB_ACCOUNT_URL")
    if not account_url:
        raise ValueError("BLOB_ACCOUNT_URL environment variable not set")
    
    credential = DefaultAzureCredential()
    client = BlobServiceClient(account_url, credential=credential)
    return client, credential


async def list_all_cases(container) -> list:
    """List all cases from Cosmos DB."""
    cases = []
    query = "SELECT c.id, c.case_number, c.status, c.created_at FROM c"
    items = container.query_items(query=query)
    async for item in items:
        cases.append(item)
    return cases


async def list_documents_for_case(container, case_id: str) -> list:
    """List all documents for a specific case."""
    documents = []
    query = "SELECT c.id, c.document_id, c.filename, c.blob_path FROM c WHERE c.case_id = @case_id"
    params = [{"name": "@case_id", "value": case_id}]
    items = container.query_items(query=query, parameters=params)
    async for item in items:
        documents.append(item)
    return documents


async def delete_document(container, document_id: str, case_id: str, dry_run: bool = False):
    """Delete a document from Cosmos DB."""
    if dry_run:
        print(f"    [DRY-RUN] Would delete document: {document_id}")
        return True
    
    try:
        await container.delete_item(item=document_id, partition_key=case_id)
        print(f"    ✓ Deleted document: {document_id}")
        return True
    except Exception as e:
        print(f"    ✗ Failed to delete document {document_id}: {e}")
        return False


async def delete_case(container, case_id: str, dry_run: bool = False):
    """Delete a case from Cosmos DB."""
    if dry_run:
        print(f"  [DRY-RUN] Would delete case: {case_id}")
        return True
    
    try:
        await container.delete_item(item=case_id, partition_key=case_id)
        print(f"  ✓ Deleted case: {case_id}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to delete case {case_id}: {e}")
        return False


async def delete_blobs_for_case(blob_service_client, container_name: str, case_id: str, dry_run: bool = False):
    """Delete all blobs under a case folder."""
    container_client = blob_service_client.get_container_client(container_name)
    
    deleted_count = 0
    try:
        # List all blobs with the case_id prefix
        async for blob in container_client.list_blobs(name_starts_with=f"{case_id}/"):
            if dry_run:
                print(f"    [DRY-RUN] Would delete blob: {blob.name}")
            else:
                try:
                    await container_client.delete_blob(blob.name)
                    print(f"    ✓ Deleted blob: {blob.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    ✗ Failed to delete blob {blob.name}: {e}")
    except Exception as e:
        print(f"  ✗ Failed to list blobs for case {case_id}: {e}")
    
    return deleted_count


async def cleanup_case(
    cases_container,
    documents_container,
    blob_service_client,
    blob_container_name: str,
    case_id: str,
    dry_run: bool = False
):
    """Clean up a single case and all its associated data."""
    print(f"\n{'=' * 60}")
    print(f"Processing case: {case_id}")
    print(f"{'=' * 60}")
    
    # 1. Delete documents from Cosmos DB
    print("\n1. Deleting documents from Cosmos DB...")
    documents = await list_documents_for_case(documents_container, case_id)
    print(f"   Found {len(documents)} document(s)")
    
    for doc in documents:
        doc_id = doc.get("document_id") or doc.get("id")
        await delete_document(documents_container, doc_id, case_id, dry_run)
    
    # 2. Delete blobs from Azure Blob Storage
    print("\n2. Deleting blobs from Azure Blob Storage...")
    blob_count = await delete_blobs_for_case(blob_service_client, blob_container_name, case_id, dry_run)
    if not dry_run:
        print(f"   Deleted {blob_count} blob(s)")
    
    # 3. Delete case from Cosmos DB
    print("\n3. Deleting case from Cosmos DB...")
    await delete_case(cases_container, case_id, dry_run)
    
    print(f"\n{'=' * 60}")
    print(f"Completed cleanup for case: {case_id}")
    print(f"{'=' * 60}")


async def main(dry_run: bool = False, specific_case_id: Optional[str] = None):
    """Main cleanup function."""
    # Load environment variables
    load_dotenv()
    
    database_name = os.getenv("COSMOS_DATABASE_NAME", "underwriting")
    blob_container_name = os.getenv("BLOB_CONTAINER_NAME", "documents")
    
    print("\n" + "=" * 70)
    print("HSBC IWPB Underwriting - Data Cleanup Script")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Cosmos Database: {database_name}")
    print(f"  Blob Container:  {blob_container_name}")
    print(f"  Dry Run:         {dry_run}")
    if specific_case_id:
        print(f"  Target Case:     {specific_case_id}")
    print()
    
    if dry_run:
        print("⚠️  DRY RUN MODE - No data will be deleted\n")
    else:
        print("⚠️  WARNING: This will permanently delete data!\n")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("Aborted.")
            return
    
    # Initialize clients
    print("\nInitializing Azure clients...")
    
    cosmos_client, cosmos_credential = await get_cosmos_client()
    blob_service_client, blob_credential = await get_blob_service_client()
    
    try:
        # Get database and containers
        database = cosmos_client.get_database_client(database_name)
        cases_container = database.get_container_client("cases")
        documents_container = database.get_container_client("documents")
        
        if specific_case_id:
            # Delete only the specified case
            await cleanup_case(
                cases_container,
                documents_container,
                blob_service_client,
                blob_container_name,
                specific_case_id,
                dry_run
            )
        else:
            # List all cases
            print("\nListing all cases...")
            cases = await list_all_cases(cases_container)
            print(f"Found {len(cases)} case(s)")
            
            if not cases:
                print("No cases to delete.")
                return
            
            # Show cases
            print("\nCases to delete:")
            for case in cases:
                print(f"  - {case['id']} ({case.get('case_number', 'N/A')})")
            
            if not dry_run:
                confirm2 = input(f"\nDelete all {len(cases)} cases? Type 'YES' to confirm: ")
                if confirm2 != "YES":
                    print("Aborted.")
                    return
            
            # Delete each case
            for case in cases:
                await cleanup_case(
                    cases_container,
                    documents_container,
                    blob_service_client,
                    blob_container_name,
                    case["id"],
                    dry_run
                )
        
        print("\n" + "=" * 70)
        print("Cleanup completed!")
        print("=" * 70)
        
    finally:
        # Clean up
        await cosmos_client.close()
        await cosmos_credential.close()
        await blob_service_client.close()
        await blob_credential.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete all cases and documents from Cosmos DB and Blob Storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--case-id",
        type=str,
        help="Delete only a specific case ID"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(dry_run=args.dry_run, specific_case_id=args.case_id))
