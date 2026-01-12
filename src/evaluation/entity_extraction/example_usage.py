"""
Example: Using batch evaluation with entity extraction

This demonstrates how the batch evaluation automatically runs after extraction.
"""

import asyncio


async def example_extraction_with_evaluation():
    """Example showing automatic batch evaluation."""
    from src.entity_extraction.config import get_config, get_cosmos_client
    from src.entity_extraction.repositories import (
        SchemaRepository, ExtractionRepository, ExtractionModelRepository
    )
    from src.entity_extraction.services import SchemaExtractionService
    from uuid import UUID
    
    # Initialize services
    config = get_config()
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(config.cosmos_database)
    
    schema_repo = SchemaRepository(database)
    extraction_repo = ExtractionRepository(database)
    model_repo = ExtractionModelRepository(database)
    
    # Initialize extraction service with evaluation enabled (default)
    extraction_service = SchemaExtractionService(
        schema_repo=schema_repo,
        extraction_repo=extraction_repo,
        model_repo=model_repo,
        enable_evaluation=True  # Evaluation enabled by default
    )
    
    print("=" * 60)
    print("Entity Extraction with Automatic Batch Evaluation")
    print("=" * 60)
    
    # Example document
    document_id = "example-doc"
    document_type_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    version = "1.0.0"
    document_content = b"Account Number: 1234567890\nName: John Smith"
    
    print(f"\nExtracting document: {document_id}")
    
    try:
        # Perform extraction - evaluation runs automatically
        result = await extraction_service.extract_document(
            document_id=document_id,
            document_content=document_content,
            document_type_id=document_type_id,
            version=version
        )
        
        print(f"\n✓ Extraction completed!")
        print(f"  Status: {result.status.value}")
        print(f"  Fields extracted: {len(result.fields)}")
        
        # Query document to see evaluation results
        container = database.get_container_client("documents")
        query = "SELECT * FROM c WHERE CONTAINS(c.id, @doc_id) OR CONTAINS(c.filename, @doc_id)"
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@doc_id", "value": document_id}],
            enable_cross_partition_query=True
        ))
        
        if items and "extraction" in items[0]:
            extraction_data = items[0]["extraction"]
            if "evaluation" in extraction_data:
                print("\n✓ Evaluation results saved!")
                eval_summary = extraction_data["evaluation"]["aggregate_summary"]
                print(f"  Average correctness: {eval_summary.get('average_correctness_score', 'N/A')}")
                print(f"  Fields correct: {eval_summary.get('fields_correct', 0)}")
            else:
                print("\n⚠ No evaluation results found")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_extraction_without_evaluation():
    """Example showing extraction with evaluation disabled."""
    from src.entity_extraction.config import get_config, get_cosmos_client
    from src.entity_extraction.repositories import (
        SchemaRepository, ExtractionRepository, ExtractionModelRepository
    )
    from src.entity_extraction.services import SchemaExtractionService
    
    config = get_config()
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(config.cosmos_database)
    
    schema_repo = SchemaRepository(database)
    extraction_repo = ExtractionRepository(database)
    model_repo = ExtractionModelRepository(database)
    
    # Disable evaluation
    extraction_service = SchemaExtractionService(
        schema_repo=schema_repo,
        extraction_repo=extraction_repo,
        model_repo=model_repo,
        enable_evaluation=False  # Evaluation disabled
    )
    
    print("\n" + "=" * 60)
    print("Extraction WITHOUT Evaluation")
    print("=" * 60)
    print("\nEvaluation disabled - no evaluation will run after extraction.")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_extraction_with_evaluation())
    asyncio.run(example_extraction_without_evaluation())
