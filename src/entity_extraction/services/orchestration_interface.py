"""Interface for orchestration workflow integration."""

from typing import Any, Dict, Optional
from uuid import UUID

from ..config import get_config, get_cosmos_client
from ..repositories import ExtractionRepository, SchemaRepository
from ..adapters.azure_openai_vision import AzureOpenAIVisionAdapter
from ..services.schema_extraction_service import SchemaExtractionService
from ..models import ExtractionResult


async def extract_document_for_workflow(
    document_id: str,
    document_content: bytes,
    document_type_id: str,
    schema_version: str = "latest"
) -> Dict[str, Any]:
    """
    Extract structured data from a document for orchestration workflows.
    
    This is the main entry point for orchestration integration.
    
    Args:
        document_id: Unique document identifier
        document_content: Raw document bytes (PDF, image, etc.)
        document_type_id: Document type UUID as string
        schema_version: Schema version to use (default: "latest")
    
    Returns:
        Dictionary with extraction results:
        {
            "extraction_id": str,
            "status": str,
            "fields": List[Dict],
            "needs_review": bool,
            "processing_time_ms": int
        }
    
    Example:
        ```python
        result = await extract_document_for_workflow(
            document_id="doc-123",
            document_content=pdf_bytes,
            document_type_id="550e8400-e29b-41d4-a716-446655440000",
            schema_version="2.0.0"
        )
        
        if result["needs_review"]:
            # Route to human review
            pass
        else:
            # Continue with automated processing
            pass
        ```
    """
    # Initialize services
    config = get_config()
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(config.cosmos_database)
    
    schema_repo = SchemaRepository(database)
    extraction_repo = ExtractionRepository(database)
    
    # Initialize extraction service with GPT-4 Vision adapter
    extraction_service = SchemaExtractionService(
        schema_repo=schema_repo,
        extraction_repo=extraction_repo
    )
    
    # Register GPT-4 Vision adapter
    vision_adapter = AzureOpenAIVisionAdapter(
        endpoint=config.openai_endpoint,
        api_key=config.openai_key,
        deployment=config.openai_deployment_gpt4_vision
    )
    extraction_service.register_adapter("azure_gpt4_vision", vision_adapter)
    
    # Perform extraction
    extraction_result = await extraction_service.extract_document(
        document_id=document_id,
        document_content=document_content,
        document_type_id=UUID(document_type_id),
        version=schema_version
    )
    
    # Convert to workflow-friendly format
    return _format_for_workflow(extraction_result)


def _format_for_workflow(extraction: ExtractionResult) -> Dict[str, Any]:
    """Format extraction result for workflow consumption."""
    needs_review = any(field.needs_review for field in extraction.fields)
    
    fields_data = [
        {
            "name": field.field_name,
            "value": field.value,
            "confidence": field.confidence,
            "needs_review": field.needs_review,
            "review_reason": field.review_reason,
            "citations": [
                {
                    "type": citation.type,
                    "page": citation.page,
                    "bbox": citation.bbox.model_dump() if citation.bbox else None,
                    "text": citation.text_snippet
                }
                for citation in field.citations
            ]
        }
        for field in extraction.fields
    ]
    
    return {
        "extraction_id": str(extraction.id),
        "document_id": extraction.document_id,
        "status": extraction.status.value,
        "fields": fields_data,
        "needs_review": needs_review,
        "models_used": extraction.models_used,
        "processing_time_ms": extraction.processing_duration_ms,
        "error_message": extraction.error_message
    }


async def get_extraction_status(extraction_id: str) -> Dict[str, Any]:
    """
    Get status of an extraction operation.
    
    Args:
        extraction_id: Extraction UUID as string
    
    Returns:
        Status dictionary
    """
    config = get_config()
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(config.cosmos_database)
    
    extraction_repo = ExtractionRepository(database)
    extraction = await extraction_repo.get_extraction(UUID(extraction_id))
    
    if not extraction:
        return {
            "found": False,
            "error": f"Extraction {extraction_id} not found"
        }
    
    return {
        "found": True,
        "status": extraction.status.value,
        "completed": extraction.completed_at is not None,
        "result": _format_for_workflow(extraction) if extraction.status.value == "completed" else None
    }
