"""Document Type Onboarding API routes."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from azure.identity import DefaultAzureCredential
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.document_classification.document_classifier import DirectDocumentClassifier
from src.entity_extraction.config import get_config, get_cosmos_client
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
from src.evaluation.entity_extraction.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


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
    model_repo=Depends(get_extraction_model_repository),
):
    """Get extraction service."""
    return SchemaExtractionService(schema_repo, extraction_repo, model_repo)


# Request/Response models


class ClassifyDocumentRequest(BaseModel):
    """Request model for document classification."""

    document_name: str = Field(..., description="Name of the document")


class ClassifyDocumentResponse(BaseModel):
    """Response model for document classification."""

    document_type: str = Field(..., description="Classified document type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    suggested_name: str = Field(..., description="Suggested document type name")


class OnboardingTestRequest(BaseModel):
    """Request model for testing extraction during onboarding."""

    document_type_id: Optional[UUID] = Field(None, description="Existing document type ID (for editing)")
    document_type_name: str = Field(..., description="Name of the document type")
    description: Optional[str] = Field(None, description="Description of document type")
    version: str = Field(..., description="Version string")
    input_schema: Dict[str, Any] = Field(..., description="Input schema (fields to extract)")
    output_schema: Dict[str, Any] = Field(..., description="Output schema")
    extraction_config: Dict[str, Any] = Field(..., description="Extraction model configuration")
    custom_prompt: Optional[str] = Field(None, description="Custom extraction prompt")
    citation_level: str = Field(default="bounding_box", description="Citation level")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    created_by: str = Field(..., description="User email")


class OnboardingTestResponse(BaseModel):
    """Response model for test extraction."""

    extraction_result: ExtractionResult = Field(..., description="Extraction result")
    evaluation: Optional[Dict[str, Any]] = Field(None, description="Evaluation metrics")
    recommendation: str = Field(
        ..., description="Recommendation (finalize, adjust, or retry)"
    )


class FinalizeOnboardingRequest(BaseModel):
    """Request model to finalize document type onboarding."""

    document_type_id: Optional[UUID] = Field(None, description="Existing document type ID (for updates)")
    document_type_name: str = Field(..., description="Name of the document type")
    description: Optional[str] = Field(None, description="Description")
    version: str = Field(..., description="Version string")
    input_schema: Dict[str, Any] = Field(..., description="Input schema")
    output_schema: Dict[str, Any] = Field(..., description="Output schema")
    extraction_config: Dict[str, Any] = Field(..., description="Extraction configuration")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt")
    citation_level: str = Field(default="bounding_box")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    created_by: str = Field(..., description="User email")


class CompareModelsRequest(BaseModel):
    """Request model for A/B model comparison."""

    model_configs: List[Dict[str, Any]] = Field(
        ..., min_items=2, max_items=5, description="List of model configurations to compare"
    )
    input_schema: Dict[str, Any] = Field(..., description="Input schema")
    output_schema: Dict[str, Any] = Field(..., description="Output schema")


# Endpoints


@router.post("/classify-document", response_model=ClassifyDocumentResponse)
async def classify_document(file: UploadFile = File(...)):
    """
    Classify an uploaded document to determine its type.

    This endpoint helps identify what type of document has been uploaded
    during the onboarding process.
    """
    try:
        # Read document content
        document_content = await file.read()

        # Initialize classifier
        classifier = DirectDocumentClassifier()

        # Classify document
        classification_result = classifier.classify_document(
            document_content=document_content, document_name=file.filename or "document"
        )

        # Get the top classification
        if classification_result.pages and len(classification_result.pages) > 0:
            top_classification = classification_result.pages[0]
            document_type = top_classification.document_type
            confidence = top_classification.confidence

            # Generate a suggested name
            suggested_name = document_type.replace("_", " ").title()

            return ClassifyDocumentResponse(
                document_type=document_type,
                confidence=confidence,
                suggested_name=suggested_name,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to classify document",
            )

    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.post("/test-extraction", response_model=OnboardingTestResponse)
async def test_extraction(
    document_id: str = Form(...),
    config_json: str = Form(...),
    file: UploadFile = File(...),
    ground_truth_file: Optional[UploadFile] = File(None),
    extraction_service: SchemaExtractionService = Depends(get_extraction_service),
    schema_repo: SchemaRepository = Depends(get_schema_repository),
    model_repo: ExtractionModelRepository = Depends(get_extraction_model_repository),
):
    """
    Test extraction with a specific configuration during onboarding.

    This endpoint allows users to test their extraction configuration
    before finalizing the onboarding.
    """
    try:
        import json

        # Parse configuration
        config = json.loads(config_json)
        request = OnboardingTestRequest(**config)

        # Read document content
        document_content = await file.read()

        # Read ground truth if provided
        ground_truth = None
        if ground_truth_file:
            ground_truth_content = await ground_truth_file.read()
            ground_truth = json.loads(ground_truth_content.decode("utf-8"))

        # Create temporary document type and version if not exists
        if request.document_type_id:
            doc_type = await schema_repo.get_document_type(request.document_type_id)
            if not doc_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document type {request.document_type_id} not found",
                )
        else:
            # Create temporary document type for testing
            schema_service = SchemaService(schema_repo)
            doc_type = await schema_service.create_document_type(
                name=f"TEMP_{request.document_type_name}",
                description=f"Temporary for onboarding test: {request.description}",
                created_by=request.created_by,
            )

        # Add custom prompt to extraction config if provided
        extraction_config = request.extraction_config.copy()
        if request.custom_prompt:
            extraction_config["custom_prompt"] = request.custom_prompt
        
        # Log the input schema fields only (not full content)
        logger.info(f"Creating schema version with {len(request.input_schema)} input schema fields: {list(request.input_schema.keys())}")
        logger.info(f"Input schema type: {type(request.input_schema)}")
        logger.info(f"Input schema structure check - has 'properties'?: {'properties' in request.input_schema if isinstance(request.input_schema, dict) else 'N/A'}")
        if isinstance(request.input_schema, dict) and "properties" in request.input_schema:
            logger.info(f"Input schema.properties fields: {list(request.input_schema['properties'].keys())}")

        # Create temporary schema version
        schema_service = SchemaService(schema_repo)
        version = await schema_service.create_schema_version(
            document_type_id=doc_type.id,
            version=request.version,  # Use version as-is, no prefix
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            extraction_config=extraction_config,
            citation_level=request.citation_level,
            confidence_threshold=request.confidence_threshold,
            created_by=request.created_by,
        )

        # Perform extraction
        extraction_result = await extraction_service.extract_document(
            document_id=document_id,
            document_content=document_content,
            document_type_id=doc_type.id,
            version=request.version,  # Use version as-is
        )

        # Perform evaluation
        evaluation_result = None
        recommendation = "adjust"

        if ground_truth:
            # Evaluate with ground truth
            evaluation_result = await _evaluate_with_ground_truth(
                extraction_result, ground_truth
            )
        else:
            # Evaluate without ground truth using completeness/correctness
            evaluation_result = await _evaluate_extraction(extraction_result, document_content)

        # Determine recommendation based on evaluation
        if evaluation_result:
            avg_confidence = evaluation_result.get("average_confidence", 0)
            completeness_score = evaluation_result.get("completeness_score", 0)
            correctness_score = evaluation_result.get("correctness_score", 0)

            if avg_confidence >= 0.8 and completeness_score >= 0.8 and correctness_score >= 0.8:
                recommendation = "finalize"
            elif avg_confidence >= 0.6 and completeness_score >= 0.6:
                recommendation = "adjust"
            else:
                recommendation = "retry"

        return OnboardingTestResponse(
            extraction_result=extraction_result,
            evaluation=evaluation_result,
            recommendation=recommendation,
        )

    except Exception as e:
        logger.error(f"Test extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test extraction failed: {str(e)}",
        )


@router.post("/compare-models", response_model=List[OnboardingTestResponse])
async def compare_models(
    document_id: str = Form(...),
    config_json: str = Form(...),
    file: UploadFile = File(...),
    extraction_service: SchemaExtractionService = Depends(get_extraction_service),
    schema_repo: SchemaRepository = Depends(get_schema_repository),
):
    """
    Compare multiple model configurations side-by-side.

    This enables A/B testing during onboarding.
    """
    try:
        import json

        # Parse configuration
        config = json.loads(config_json)
        request = CompareModelsRequest(**config)

        # Read document content
        document_content = await file.read()

        results = []

        # Test each model configuration
        for idx, model_config in enumerate(request.model_configs):
            # Create temporary document type
            schema_service = SchemaService(schema_repo)
            doc_type = await schema_service.create_document_type(
                name=f"TEMP_COMPARE_{idx}",
                description=f"Temporary for comparison test",
                created_by="system",
            )

            # Create temporary version
            version = await schema_service.create_schema_version(
                document_type_id=doc_type.id,
                version="1.0.0",  # Use a valid version format
                input_schema=request.input_schema,
                output_schema=request.output_schema,
                extraction_config=model_config,
                citation_level="bounding_box",
                confidence_threshold=0.7,
                created_by="system",
            )

            # Perform extraction
            extraction_result = await extraction_service.extract_document(
                document_id=f"{document_id}_compare_{idx}",
                document_content=document_content,
                document_type_id=doc_type.id,
                version="1.0.0",  # Use same valid version
            )

            # Evaluate
            evaluation_result = await _evaluate_extraction(extraction_result, document_content)

            # Determine recommendation
            recommendation = "adjust"
            if evaluation_result:
                avg_confidence = evaluation_result.get("average_confidence", 0)
                if avg_confidence >= 0.8:
                    recommendation = "finalize"
                elif avg_confidence < 0.6:
                    recommendation = "retry"

            results.append(
                OnboardingTestResponse(
                    extraction_result=extraction_result,
                    evaluation=evaluation_result,
                    recommendation=recommendation,
                )
            )

        return results

    except Exception as e:
        logger.error(f"Model comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model comparison failed: {str(e)}",
        )


@router.post(
    "/finalize", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED
)
async def finalize_onboarding(
    request: FinalizeOnboardingRequest,
    schema_service: SchemaService = Depends(get_schema_service),
    schema_repo: SchemaRepository = Depends(get_schema_repository),
    model_repo: ExtractionModelRepository = Depends(get_extraction_model_repository),
):
    """
    Finalize document type onboarding.

    This creates or updates the document type and schema version permanently.
    """
    try:
        # Create or update document type
        if request.document_type_id:
            # Update existing
            doc_type = await schema_repo.get_document_type(request.document_type_id)
            if not doc_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document type {request.document_type_id} not found",
                )
            # Update fields if needed (you may want to add an update method)
            doc_type_id = request.document_type_id
        else:
            # Create new
            doc_type = await schema_service.create_document_type(
                name=request.document_type_name,
                description=request.description,
                created_by=request.created_by,
            )
            doc_type_id = doc_type.id

        # Add custom prompt to extraction config if provided
        extraction_config = request.extraction_config.copy()
        if request.custom_prompt:
            extraction_config["custom_prompt"] = request.custom_prompt

        # Validate model configuration
        errors = await schema_service.validate_model_config(extraction_config, model_repo)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model configuration: {', '.join(errors)}",
            )

        # Create schema version
        version = await schema_service.create_schema_version(
            document_type_id=doc_type_id,
            version=request.version,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            extraction_config=extraction_config,
            citation_level=request.citation_level,
            confidence_threshold=request.confidence_threshold,
            created_by=request.created_by,
        )

        return {
            "success": True,
            "document_type_id": str(doc_type_id),
            "version_id": str(version.id),
            "message": "Document type onboarding completed successfully",
        }

    except Exception as e:
        logger.error(f"Finalize onboarding failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize onboarding: {str(e)}",
        )


# Helper functions


async def _evaluate_with_ground_truth(
    extraction_result: ExtractionResult, ground_truth: Dict[str, Any]
) -> Dict[str, Any]:
    """Evaluate extraction results against ground truth."""
    total_fields = len(extraction_result.fields)
    correct_fields = 0
    total_confidence = 0.0

    field_evaluations = {}

    for field in extraction_result.fields:
        field_name = field.field_name
        extracted_value = field.value
        expected_value = ground_truth.get(field_name)

        is_correct = str(extracted_value) == str(expected_value) if expected_value else False
        if is_correct:
            correct_fields += 1

        total_confidence += field.confidence

        field_evaluations[field_name] = {
            "extracted": extracted_value,
            "expected": expected_value,
            "is_correct": is_correct,
            "confidence": field.confidence,
        }

    accuracy = correct_fields / total_fields if total_fields > 0 else 0
    avg_confidence = total_confidence / total_fields if total_fields > 0 else 0

    return {
        "evaluation_type": "ground_truth",
        "accuracy": accuracy,
        "average_confidence": avg_confidence,
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "field_evaluations": field_evaluations,
        "completeness_score": accuracy,  # For ground truth, accuracy = completeness
        "correctness_score": accuracy,
    }


async def _evaluate_extraction(
    extraction_result: ExtractionResult, document_content: bytes
) -> Dict[str, Any]:
    """Evaluate extraction using completeness and correctness evaluators."""
    try:
        # Get Azure credentials and config
        import os
        credential = DefaultAzureCredential()

        # Get Azure OpenAI config from environment
        azure_endpoint = os.getenv("EXTRACTION_OPENAI_ENDPOINT")
        deployment_name = os.getenv("EXTRACTION_OPENAI_DEPLOYMENT_GPT4_VISION")
        api_version = os.getenv("EXTRACTION_OPENAI_API_VERSION", "2024-12-01-preview")

        if not azure_endpoint or not deployment_name:
            raise ValueError("Missing EXTRACTION_OPENAI_ENDPOINT or EXTRACTION_OPENAI_DEPLOYMENT_GPT4_VISION in environment")

        # Initialize evaluation service
        eval_service = EvaluationService(
            azure_endpoint=azure_endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
            credential=credential,
        )

        # Convert document content to text (simplified)
        source_text = document_content.decode("utf-8", errors="ignore")

        # Prepare fields for evaluation - convert to list format expected by evaluate_batch
        fields = [
            {"field_name": field.field_name, "value": str(field.value)}
            for field in extraction_result.fields
        ]

        # Run batch evaluation
        evaluation_result = eval_service.evaluate_batch(
            fields=fields,
            source_text=source_text,
            evaluators=["correctness", "completeness"],
        )

        # Calculate summary metrics
        total_fields = len(extraction_result.fields)
        total_confidence = sum(field.confidence for field in extraction_result.fields)
        avg_confidence = total_confidence / total_fields if total_fields > 0 else 0

        # Extract scores from aggregate_summary
        aggregate = evaluation_result.get("aggregate_summary", {})
        avg_completeness = aggregate.get("average_completeness_score", 0)
        avg_correctness = aggregate.get("average_correctness_score", 0)

        return {
            "evaluation_type": "ai_evaluator",
            "average_confidence": avg_confidence,
            "completeness_score": avg_completeness,
            "correctness_score": avg_correctness,
            "total_fields": total_fields,
            "field_evaluations": evaluation_result.get("results", {}),
            "summary": evaluation_result.get("summary", {}),
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        # Return basic metrics if evaluation fails
        total_fields = len(extraction_result.fields)
        total_confidence = sum(field.confidence for field in extraction_result.fields)
        avg_confidence = total_confidence / total_fields if total_fields > 0 else 0

        return {
            "evaluation_type": "basic",
            "average_confidence": avg_confidence,
            "completeness_score": 0,
            "correctness_score": 0,
            "total_fields": total_fields,
            "error": str(e),
        }
    
