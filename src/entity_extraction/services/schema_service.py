"""Service for managing document schemas and versions."""

import json
from typing import Dict, List, Optional
from uuid import UUID

import jsonschema
from jsonschema import ValidationError

from ..models import DocumentType, DocumentTypeVersion
from ..repositories import SchemaRepository


class SchemaService:
    """Service for schema management operations."""
    
    def __init__(self, schema_repo: SchemaRepository):
        """
        Initialize schema service.
        
        Args:
            schema_repo: Repository for schema persistence
        """
        self.schema_repo = schema_repo
    
    async def get_schema(
        self,
        document_type_id: UUID,
        version: str
    ) -> Optional[DocumentTypeVersion]:
        """
        Get a specific schema version.
        
        Args:
            document_type_id: ID of the document type
            version: Version string (e.g., "2.0.0" or "2023")
        
        Returns:
            Schema version if found, None otherwise
        """
        return await self.schema_repo.get_schema_version(document_type_id, version)
    
    def validate_schema(self, schema: Dict, data: Dict) -> bool:
        """
        Validate data against a JSON schema.
        
        Args:
            schema: JSON Schema definition
            data: Data to validate
        
        Returns:
            True if validation succeeds
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValidationError(f"Schema validation failed: {e.message}")
    
    async def list_versions(
        self,
        document_type_id: UUID,
        active_only: bool = True
    ) -> List[DocumentTypeVersion]:
        """
        List all versions for a document type.
        
        Args:
            document_type_id: ID of the document type
            active_only: Whether to return only active versions
        
        Returns:
            List of schema versions
        """
        return await self.schema_repo.list_schema_versions(
            document_type_id,
            active_only
        )
    
    async def create_document_type(
        self,
        name: str,
        description: Optional[str],
        created_by: str
    ) -> DocumentType:
        """
        Create a new document type.
        
        Args:
            name: Human-readable name
            description: Optional description
            created_by: User creating the type
        
        Returns:
            Created document type
        """
        document_type = DocumentType(
            name=name,
            description=description,
            created_by=created_by
        )
        return await self.schema_repo.create_document_type(document_type)
    
    async def create_schema_version(
        self,
        document_type_id: UUID,
        version: str,
        input_schema: Dict,
        output_schema: Dict,
        extraction_config: Dict,
        citation_level: str,
        confidence_threshold: float,
        created_by: str
    ) -> DocumentTypeVersion:
        """
        Create a new schema version for a document type.
        
        Args:
            document_type_id: Parent document type ID
            version: Version string
            input_schema: JSON Schema for input fields
            output_schema: JSON Schema for output structure
            model_config: Model configuration
            citation_level: Citation detail level
            confidence_threshold: Confidence threshold for fallback
            created_by: User creating the version
        
        Returns:
            Created schema version
        
        Raises:
            ValidationError: If schemas are invalid
        """
        # Validate input and output schemas are valid JSON Schema
        try:
            jsonschema.Draft7Validator.check_schema(input_schema)
            jsonschema.Draft7Validator.check_schema(output_schema)
        except jsonschema.SchemaError as e:
            raise ValidationError(f"Invalid JSON Schema: {e.message}")
        
        # Get document type to populate document_name
        document_type = await self.schema_repo.get_document_type(document_type_id)
        
        from ..models import CitationLevel
        schema_version = DocumentTypeVersion(
            document_type_id=document_type_id,
            document_name=document_type.name if document_type else None,
            version=version,
            input_schema=input_schema,
            output_schema=output_schema,
            extraction_config=extraction_config,
            citation_level=CitationLevel(citation_level),
            confidence_threshold=confidence_threshold,
            created_by=created_by
        )
        
        return await self.schema_repo.create_schema_version(schema_version)
    
    async def list_document_types(self, active_only: bool = True) -> List[DocumentType]:
        """
        List all document types.
        
        Args:
            active_only: Whether to return only active types
        
        Returns:
            List of document types
        """
        return await self.schema_repo.list_document_types(active_only)
    
    async def validate_model_config(self, model_config: Dict, model_repo) -> List[str]:
        """
        Validate that all model IDs in configuration exist.
        
        Args:
            model_config: Model configuration dictionary
            model_repo: Extraction model repository
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        models = model_config.get("models", [])
        for model_conf in models:
            model_id = model_conf.get("model_id")
            if not model_id:
                errors.append("Model configuration missing 'model_id'")
                continue
            
            try:
                model_uuid = UUID(model_id)
                model = await model_repo.get_model(model_uuid)
                if not model:
                    errors.append(f"Model ID {model_id} not found")
                elif not model.is_active:
                    errors.append(f"Model {model_id} is not active")
            except ValueError:
                errors.append(f"Invalid model ID format: {model_id}")
        
        return errors
