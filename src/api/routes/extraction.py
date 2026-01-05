"""Extraction API routes for schema management and document extraction."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.entity_extraction.config import get_cosmos_client
from src.entity_extraction.models import (
    DocumentType,
    DocumentTypeVersion,
    ExtractionModel,
    ExtractionResult,
    ModelType,
)
from src.entity_extraction.repositories import (
    ExtractionModelRepository,
    ExtractionRepository,
    SchemaRepository,
)
from src.entity_extraction.services import SchemaExtractionService, SchemaService
from src.entity_extraction.adapters import AzureOpenAIVisionAdapter
from src.entity_extraction.config import get_config

router = APIRouter(prefix="/extraction", tags=["extraction"])


# Dependency injection
def get_cosmos_database():
    """Get Cosmos DB database client."""
    cosmos_client = get_cosmos_client()
    config = get_config()
    return cosmos_client.get_database_client(config.cosmos_database)


def get_schema_repository(database=Depends(get_cosmos_database)):
    """Get schema repository."""
    return SchemaRepository(database)


def get_extraction_model_repository(database=Depends(get_cosmos_database)):
    """Get extraction model repository."""
    return ExtractionModelRepository(database)


def get_extraction_repository(database=Depends(get_cosmos_database)):
    """Get extraction repository."""
    return ExtractionRepository(database)


def get_schema_service(schema_repo=Depends(get_schema_repository)):
    """Get schema service."""
    return SchemaService(schema_repo)


def get_extraction_service(
    schema_repo=Depends(get_schema_repository),
    extraction_repo=Depends(get_extraction_repository),
    model_repo=Depends(get_extraction_model_repository)
):
    """Get extraction service with model repository for dynamic adapter creation."""
    service = SchemaExtractionService(schema_repo, extraction_repo, model_repo)
    return service


# Request/Response models
class DocumentTypeCreate(BaseModel):
    """Request model for creating a document type."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    created_by: str


class DocumentTypeResponse(BaseModel):
    """Response model for document type."""
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    versions_count: int = 0


class SchemaVersionCreate(BaseModel):
    """Request model for creating a schema version."""
    version: str
    input_schema: dict
    output_schema: dict
    extraction_config: dict
    citation_level: str
    confidence_threshold: float = 0.7
    created_by: str


class ExtractionModelCreate(BaseModel):
    """Request model for registering an extraction model."""
    name: str
    type: ModelType
    endpoint: Optional[str] = None
    version: str
    api_version: Optional[str] = None
    capabilities: List[str] = []


class ExtractionRequest(BaseModel):
    """Request model for triggering extraction."""
    document_id: str
    document_type_id: UUID
    version: str


# Document Type Endpoints

@router.post("/document-types", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_document_type(
    request: DocumentTypeCreate,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Create a new document type."""
    try:
        doc_type = await schema_service.create_document_type(
            name=request.name,
            description=request.description,
            created_by=request.created_by
        )
        return DocumentTypeResponse(
            id=doc_type.id,
            name=doc_type.name,
            description=doc_type.description,
            is_active=doc_type.is_active,
            versions_count=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create document type: {str(e)}"
        )


@router.get("/document-types", response_model=List[DocumentTypeResponse])
async def list_document_types(
    active_only: bool = True,
    schema_service: SchemaService = Depends(get_schema_service),
    schema_repo: SchemaRepository = Depends(get_schema_repository)
):
    """List all document types."""
    doc_types = await schema_service.list_document_types(active_only)
    
    # Get version counts for each type
    responses = []
    for doc_type in doc_types:
        versions = await schema_repo.list_schema_versions(doc_type.id, active_only=True)
        responses.append(DocumentTypeResponse(
            id=doc_type.id,
            name=doc_type.name,
            description=doc_type.description,
            is_active=doc_type.is_active,
            versions_count=len(versions)
        ))
    
    return responses


@router.get("/document-types/{type_id}", response_model=DocumentType)
async def get_document_type(
    type_id: UUID,
    schema_repo: SchemaRepository = Depends(get_schema_repository)
):
    """Get a specific document type."""
    doc_type = await schema_repo.get_document_type(type_id)
    if not doc_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type {type_id} not found"
        )
    return doc_type


# Schema Version Endpoints

@router.post(
    "/document-types/{type_id}/versions",
    response_model=DocumentTypeVersion,
    status_code=status.HTTP_201_CREATED
)
async def create_schema_version(
    type_id: UUID,
    request: SchemaVersionCreate,
    schema_service: SchemaService = Depends(get_schema_service),
    model_repo: ExtractionModelRepository = Depends(get_extraction_model_repository)
):
    """Create a new schema version for a document type."""
    try:
        # Validate model configuration
        errors = await schema_service.validate_model_config(request.extraction_config, model_repo)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model configuration: {', '.join(errors)}"
            )
        
        version = await schema_service.create_schema_version(
            document_type_id=type_id,
            version=request.version,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            extraction_config=request.extraction_config,
            citation_level=request.citation_level,
            confidence_threshold=request.confidence_threshold,
            created_by=request.created_by
        )
        return version
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create schema version: {str(e)}"
        )


@router.get("/document-types/{type_id}/versions", response_model=List[DocumentTypeVersion])
async def list_schema_versions(
    type_id: UUID,
    active_only: bool = True,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """List all schema versions for a document type."""
    versions = await schema_service.list_versions(type_id, active_only)
    return versions


@router.get("/document-types/{type_id}/versions/{version}", response_model=DocumentTypeVersion)
async def get_schema_version(
    type_id: UUID,
    version: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Get a specific schema version."""
    schema_version = await schema_service.get_schema(type_id, version)
    if not schema_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema version {version} not found for document type {type_id}"
        )
    return schema_version


# Extraction Model Endpoints

@router.post("/models", response_model=ExtractionModel, status_code=status.HTTP_201_CREATED)
async def register_extraction_model(
    request: ExtractionModelCreate,
    model_repo: ExtractionModelRepository = Depends(get_extraction_model_repository)
):
    """Register a new extraction model."""
    try:
        model = ExtractionModel(
            name=request.name,
            type=request.type,
            endpoint=request.endpoint,
            version=request.version,
            api_version=request.api_version,
            capabilities=request.capabilities
        )
        created = await model_repo.create_model(model)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register model: {str(e)}"
        )


@router.get("/models", response_model=List[ExtractionModel])
async def list_extraction_models(
    model_type: Optional[ModelType] = None,
    active_only: bool = True,
    model_repo: ExtractionModelRepository = Depends(get_extraction_model_repository)
):
    """List all extraction models."""
    models = await model_repo.list_models(model_type, active_only)
    return models


# Extraction Endpoints

@router.post("/extract", response_model=ExtractionResult, status_code=status.HTTP_202_ACCEPTED)
async def trigger_extraction(
    document_id: str = Form(...),
    document_type_id: UUID = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    extraction_service: SchemaExtractionService = Depends(get_extraction_service)
):
    """Trigger document extraction."""
    try:
        # Read document content
        document_content = await file.read()
        
        # Trigger extraction
        result = await extraction_service.extract_document(
            document_id=document_id,
            document_content=document_content,
            document_type_id=document_type_id,
            version=version
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/results/{extraction_id}", response_model=ExtractionResult)
async def get_extraction_result(
    extraction_id: UUID,
    extraction_service: SchemaExtractionService = Depends(get_extraction_service)
):
    """Get extraction result by ID."""
    result = await extraction_service.get_extraction_result(extraction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction result {extraction_id} not found"
        )
    return result


@router.get("/documents/{document_id}/extractions", response_model=List[ExtractionResult])
async def list_document_extractions(
    document_id: str,
    limit: int = 100,
    extraction_repo: ExtractionRepository = Depends(get_extraction_repository)
):
    """List all extraction results for a document."""
    results = await extraction_repo.list_extractions_for_document(
        document_id=document_id,
        limit=limit
    )
    return results
