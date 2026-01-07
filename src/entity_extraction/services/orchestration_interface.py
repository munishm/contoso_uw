"""Interface for orchestration workflow integration."""

import logging
from typing import Any, Dict, Optional, List
from uuid import UUID

from ..config import get_config, get_cosmos_client
from ..repositories import ExtractionRepository, SchemaRepository, ExtractionModelRepository
from ..services.schema_extraction_service import SchemaExtractionService
from ..models import ExtractionResult

logger = logging.getLogger(__name__)


async def extract_document_for_workflow(
    document_id: str,
    document_content: bytes,
    document_type: str,
    schema_version: str = "1.0.0"
) -> Dict[str, Any]:
    """
    Extract structured data from a document for orchestration workflows.
    
    This is the main entry point for orchestration integration.
    Accepts document type as either a NAME (e.g., "Lab Report") or UUID string.
    
    Args:
        document_id: Unique document identifier
        document_content: Raw document bytes (PDF, image, etc.)
        document_type: Document type NAME (e.g., "Lab Report") or UUID string
        schema_version: Schema version to use (default: "1.0.0")
    
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
        # Using document type name (from classification)
        result = await extract_document_for_workflow(
            document_id="doc-123",
            document_content=pdf_bytes,
            document_type="Lab Report",
            schema_version="1.0.0"
        )
        
        # Using document type UUID
        result = await extract_document_for_workflow(
            document_id="doc-123",
            document_content=pdf_bytes,
            document_type="550e8400-e29b-41d4-a716-446655440000",
            schema_version="1.0.0"
        )
        
        if result["needs_review"]:
            # Route to human review
            pass
        else:
            # Continue with automated processing
            pass
        ```
    """
    import threading
    current_thread = threading.current_thread().name
    
    logger.info("=" * 60)
    logger.info("ORCHESTRATION INTERFACE: extract_document_for_workflow")
    logger.info("=" * 60)
    logger.info(f"  thread: {current_thread}")
    logger.info(f"  document_id: {document_id}")
    logger.info(f"  document_type: {document_type}")
    logger.info(f"  schema_version: {schema_version}")
    logger.info(f"  content_size: {len(document_content)} bytes")
    
    # Initialize services
    logger.info(f"  Getting config...")
    config = get_config()
    logger.info(f"  Getting cosmos_client...")
    cosmos_client = get_cosmos_client()
    logger.info(f"  Getting database client for: {config.cosmos_database}")
    database = cosmos_client.get_database_client(config.cosmos_database)
    
    logger.info(f"  cosmos_database: {config.cosmos_database}")
    
    logger.info(f"  Creating SchemaRepository...")
    schema_repo = SchemaRepository(database)
    logger.info(f"  Creating ExtractionRepository...")
    extraction_repo = ExtractionRepository(database)
    logger.info(f"  Creating ExtractionModelRepository...")
    model_repo = ExtractionModelRepository(database)
    
    # Resolve document type - could be UUID or name
    logger.info(f"  Resolving document type '{document_type}'...")
    try:
        document_type_id = await _resolve_document_type(schema_repo, document_type)
    except Exception as e:
        logger.error(f"  ✗ FAILED to resolve document type: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"  Traceback: {traceback.format_exc()}")
        raise
    
    if not document_type_id:
        # Document type not found - return placeholder
        logger.warning(f"  ✗ Document type '{document_type}' NOT FOUND in schemas container")
        logger.warning(f"    Extraction SKIPPED - document type not registered")
        return {
            "extraction_id": None,
            "document_id": document_id,
            "document_type": document_type,
            "status": "skipped",
            "message": f"Document type '{document_type}' not registered for extraction",
            "fields": [],
            "needs_review": False,
            "models_used": [],
            "processing_time_ms": 0,
            "error_message": None
        }
    
    logger.info(f"  ✓ Resolved document_type_id: {document_type_id}")
    
    # Initialize extraction service with model repository
    # Note: The adapter will be created dynamically by the extraction service
    # using the model configuration from the database (models container)
    extraction_service = SchemaExtractionService(
        schema_repo=schema_repo,
        extraction_repo=extraction_repo,
        model_repo=model_repo
    )
    
    try:
        # Perform extraction
        logger.info(f"  Calling extraction_service.extract_document()...")
        logger.info(f"    document_id: {document_id}")
        logger.info(f"    document_type_id: {document_type_id}")
        logger.info(f"    version: {schema_version}")
        
        extraction_result = await extraction_service.extract_document(
            document_id=document_id,
            document_content=document_content,
            document_type_id=document_type_id,
            version=schema_version
        )
        
        logger.info(f"  ✓ Extraction completed")
        logger.info(f"    status: {extraction_result.status}")
        logger.info(f"    fields: {len(extraction_result.fields)}")
        logger.info(f"    models_used: {extraction_result.models_used}")
        logger.info(f"    processing_time_ms: {extraction_result.processing_duration_ms}")
        
        if extraction_result.error_message:
            logger.error(f"    error_message: {extraction_result.error_message}")
        
        # Convert to workflow-friendly format
        result = _format_for_workflow(extraction_result)
        logger.info(f"  Returning {len(result.get('fields', []))} fields to workflow")
        logger.info("=" * 60)
        return result
        
    except ValueError as e:
        # Schema not found or configuration error
        logger.error(f"  ✗ Extraction ValueError: {e}")
        return {
            "extraction_id": None,
            "document_id": document_id,
            "document_type": document_type,
            "status": "error",
            "message": str(e),
            "fields": [],
            "needs_review": False,
            "models_used": [],
            "processing_time_ms": 0,
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"  ✗ Extraction Exception: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"    Traceback: {traceback.format_exc()}")
        return {
            "extraction_id": None,
            "document_id": document_id,
            "document_type": document_type,
            "status": "error",
            "message": str(e),
            "fields": [],
            "needs_review": False,
            "models_used": [],
            "processing_time_ms": 0,
            "error_message": str(e)
        }


async def _resolve_document_type(schema_repo: SchemaRepository, document_type: str) -> Optional[UUID]:
    """
    Resolve document type to UUID.
    
    Args:
        schema_repo: Schema repository instance
        document_type: Document type NAME or UUID string
    
    Returns:
        UUID if found, None otherwise
    """
    # Try to parse as UUID first
    try:
        uuid_val = UUID(document_type)
        logger.info(f"    document_type is already a UUID: {uuid_val}")
        return uuid_val
    except ValueError:
        pass
    
    # Look up by name
    logger.info(f"    Looking up document type by name: '{document_type}'")
    doc_type = await schema_repo.get_document_type_by_name(document_type)
    if doc_type:
        logger.info(f"    ✓ Found document type: id={doc_type.id}, name={doc_type.name}")
    else:
        logger.warning(f"    ✗ Document type '{document_type}' not found in database")
    return doc_type.id if doc_type else None


def _format_for_workflow(extraction: ExtractionResult) -> Dict[str, Any]:
    """Format extraction result for workflow consumption."""
    needs_review = any(field.needs_review for field in extraction.fields)
    
    fields_data = [
        {
            "field_name": field.field_name,
            "value": field.value,
            "confidence": field.confidence,
            "needs_review": field.needs_review,
            "review_reason": field.review_reason,
            "citations": [
                {
                    "type": citation.type,
                    "page": citation.page,
                    "bbox": citation.bbox.model_dump() if citation.bbox else None,
                    "text_snippet": citation.text_snippet
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
