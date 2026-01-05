"""Service for schema-based document extraction."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import jsonschema

from ..models import (
    DocumentTypeVersion,
    ExtractedField,
    ExtractionResult,
    ExtractionStatus,
    ModelType,
)
from ..repositories import ExtractionRepository, SchemaRepository, ExtractionModelRepository
from ..adapters.base import ExtractionModelAdapter
from ..adapters import AzureOpenAIVisionAdapter


class SchemaExtractionService:
    """Main service for orchestrating schema-based extraction."""
    
    def __init__(
        self,
        schema_repo: SchemaRepository,
        extraction_repo: ExtractionRepository,
        model_repo: ExtractionModelRepository,
        adapters: Optional[Dict[str, ExtractionModelAdapter]] = None
    ):
        """
        Initialize extraction service.
        
        Args:
            schema_repo: Repository for schema access
            extraction_repo: Repository for result storage
            model_repo: Repository for model registry
            adapters: Dictionary of model adapters (name -> adapter instance)
        """
        self.schema_repo = schema_repo
        self.extraction_repo = extraction_repo
        self.model_repo = model_repo
        self.adapters = adapters or {}
    
    def register_adapter(self, name: str, adapter: ExtractionModelAdapter):
        """Register a model adapter."""
        self.adapters[name] = adapter
    
    async def extract_document(
        self,
        document_id: str,
        document_content: bytes,
        document_type_id: UUID,
        version: str
    ) -> ExtractionResult:
        """
        Extract structured data from a document using configured schema.
        
        Args:
            document_id: Unique document identifier
            document_content: Raw document bytes
            document_type_id: Document type ID
            version: Schema version to use
        
        Returns:
            Extraction result with all fields
        
        Raises:
            ValueError: If schema not found or invalid
        """
        start_time = time.time()
        
        # Create initial extraction record
        extraction = ExtractionResult(
            document_id=document_id,
            document_type_id=document_type_id,
            version_id=UUID(int=0),  # Will update after schema lookup
            status=ExtractionStatus.IN_PROGRESS
        )
        extraction = await self.extraction_repo.create_extraction(extraction)
        
        try:
            # 1. Look up schema version
            schema_version = await self.schema_repo.get_schema_version(
                document_type_id,
                version
            )
            if not schema_version:
                raise ValueError(
                    f"Schema not found for document type {document_type_id} version {version}"
                )
            
            extraction.version_id = schema_version.id
            
            # 2. Get document type for context
            document_type = await self.schema_repo.get_document_type(document_type_id)
            if not document_type:
                raise ValueError(f"Document type {document_type_id} not found")
            
            # 3. Determine which model(s) to use
            extraction_config = schema_version.extraction_config
            models = extraction_config.get("models", [])
            
            if not models:
                raise ValueError("No models configured for this schema version")
            
            # For MVP, use first primary model (Phase 4 will add multi-model support)
            primary_model = next(
                (m for m in models if m.get("strategy") == "primary"),
                models[0]
            )
            
            # Fetch model from database
            model_id = UUID(primary_model.get("model_id"))
            db_model = await self.model_repo.get_model(model_id)
            
            if not db_model:
                raise ValueError(f"Model {model_id} not found in registry")
            
            if not db_model.is_active:
                raise ValueError(f"Model {db_model.name} is not active")
            
            # Create adapter dynamically based on model type
            if db_model.type == ModelType.VISION:
                adapter = AzureOpenAIVisionAdapter(
                    endpoint=db_model.endpoint,
                    api_key=None,  # Use Azure AD
                    deployment=db_model.version,
                    api_version=db_model.api_version or "2024-02-15-preview"
                )
            else:
                raise ValueError(f"Unsupported model type: {db_model.type}")
            
            model_name = db_model.name
            
            # 4. Execute extraction
            field_names = primary_model.get("fields", ["*"])
            raw_results = await adapter.extract(
                document_content,
                document_type.name,
                schema_version,
                field_names
            )
            
            extraction.models_used = [model_name]
            
            # 5. Map extracted data to output schema fields
            extracted_fields = self._map_to_output_schema(
                raw_results,
                schema_version,
                model_name
            )
            
            # 6. Handle missing required fields
            extracted_fields = self._handle_missing_fields(
                extracted_fields,
                schema_version
            )
            
            # 7. Validate against output schema
            validation_errors = self._validate_output(extracted_fields, schema_version)
            if validation_errors:
                extraction.error_message = f"Validation errors: {validation_errors}"
                extraction.status = ExtractionStatus.REVIEW_REQUIRED
            else:
                extraction.status = ExtractionStatus.COMPLETED
            
            extraction.fields = extracted_fields
            extraction.completed_at = datetime.utcnow()
            extraction.processing_duration_ms = int((time.time() - start_time) * 1000)
            
            # 8. Save result
            extraction = await self.extraction_repo.update_extraction(extraction)
            
            # 9. Log extraction
            self._log_extraction(extraction, document_type.name, version)
            
            return extraction
            
        except Exception as e:
            # Handle errors
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = str(e)
            extraction.completed_at = datetime.utcnow()
            extraction.processing_duration_ms = int((time.time() - start_time) * 1000)
            
            await self.extraction_repo.update_extraction(extraction)
            
            self._log_extraction(extraction, "unknown", version, success=False)
            
            raise
    
    def _map_to_output_schema(
        self,
        raw_results: Dict[str, Any],
        schema_version: DocumentTypeVersion,
        model_source: str
    ) -> List[ExtractedField]:
        """
        Map raw extraction results to output schema format.
        
        Args:
            raw_results: Raw results from model adapter
            schema_version: Schema defining output structure
            model_source: Name of model that produced results
        
        Returns:
            List of extracted fields
        """
        fields = []
        output_schema = schema_version.output_schema
        properties = output_schema.get("properties", {})
        
        for field_name in properties.keys():
            field_result = raw_results.get(field_name, {})
            
            value = field_result.get("value")
            confidence = field_result.get("confidence", 0.0)
            citations = field_result.get("citations", [])
            
            # Determine if review is needed
            needs_review = False
            review_reason = None
            
            if value is None:
                needs_review = True
                review_reason = "Field not found in document"
            elif confidence < schema_version.confidence_threshold:
                needs_review = True
                review_reason = f"Confidence {confidence:.2f} below threshold {schema_version.confidence_threshold}"
            
            # Determine value type
            value_type = type(value).__name__ if value is not None else "null"
            
            field = ExtractedField(
                field_name=field_name,
                value=value,
                value_type=value_type,
                confidence=confidence,
                citations=citations,
                needs_review=needs_review,
                review_reason=review_reason,
                model_source=model_source
            )
            fields.append(field)
        
        return fields
    
    def _handle_missing_fields(
        self,
        fields: List[ExtractedField],
        schema_version: DocumentTypeVersion
    ) -> List[ExtractedField]:
        """
        Handle missing required fields by adding null indicators.
        
        Args:
            fields: Currently extracted fields
            schema_version: Schema defining required fields
        
        Returns:
            Fields list with null entries for missing required fields
        """
        input_schema = schema_version.input_schema
        required_fields = set(input_schema.get("required", []))
        extracted_field_names = {f.field_name for f in fields}
        
        missing_required = required_fields - extracted_field_names
        
        for field_name in missing_required:
            field = ExtractedField(
                field_name=field_name,
                value=None,
                value_type="null",
                confidence=0.0,
                citations=[],
                needs_review=True,
                review_reason="Required field missing from extraction",
                model_source="system"
            )
            fields.append(field)
        
        return fields
    
    def _validate_output(
        self,
        fields: List[ExtractedField],
        schema_version: DocumentTypeVersion
    ) -> List[str]:
        """
        Validate extracted data against output schema.
        
        Args:
            fields: Extracted fields
            schema_version: Schema with validation rules
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Build output data structure
        output_data = {}
        for field in fields:
            output_data[field.field_name] = {
                "value": field.value,
                "confidence": field.confidence,
                "citations": [c.model_dump() for c in field.citations],
                "needs_review": field.needs_review
            }
        
        # Validate against output schema
        try:
            jsonschema.validate(output_data, schema_version.output_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        
        return errors
    
    def _log_extraction(
        self,
        extraction: ExtractionResult,
        document_type: str,
        version: str,
        success: bool = True
    ):
        """
        Log extraction attempt for monitoring.
        
        Args:
            extraction: Extraction result
            document_type: Document type name
            version: Schema version
            success: Whether extraction succeeded
        """
        # TODO: Integrate with Azure Application Insights in Phase 7
        log_entry = {
            "extraction_id": str(extraction.id),
            "document_id": extraction.document_id,
            "document_type": document_type,
            "version": version,
            "models_used": extraction.models_used,
            "duration_ms": extraction.processing_duration_ms,
            "status": extraction.status.value,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # For now, just print (will be replaced with proper logging)
        print(f"EXTRACTION_LOG: {log_entry}")
    
    async def get_extraction_result(self, extraction_id: UUID) -> Optional[ExtractionResult]:
        """Get extraction result by ID."""
        return await self.extraction_repo.get_extraction(extraction_id)
