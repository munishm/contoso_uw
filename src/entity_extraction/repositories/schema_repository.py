"""Repository for document type schemas in Cosmos DB."""

from typing import List, Optional
from uuid import UUID

from azure.cosmos import ContainerProxy, DatabaseProxy, exceptions

from ..models import DocumentType, DocumentTypeVersion


class SchemaRepository:
    """Repository for managing document types and schema versions."""
    
    def __init__(self, database: DatabaseProxy):
        """
        Initialize schema repository.
        
        Args:
            database: Cosmos DB database client
        """
        self.database = database
        self._schema_container: Optional[ContainerProxy] = None
    
    @property
    def schema_container(self) -> ContainerProxy:
        """Get or create schemas container."""
        if self._schema_container is None:
            from ..config import get_config
            config = get_config()
            self._schema_container = self.database.get_container_client(
                config.cosmos_container_schemas
            )
        return self._schema_container
    
    # Document Type operations
    
    async def create_document_type(self, document_type: DocumentType) -> DocumentType:
        """Create a new document type."""
        item = document_type.model_dump(mode='json')
        item['id'] = str(document_type.id)
        item['partition_key'] = 'document_type'
        item['type'] = 'document_type'
        
        created = self.schema_container.create_item(item)
        return DocumentType.model_validate(created)
    
    async def get_document_type(self, type_id: UUID) -> Optional[DocumentType]:
        """Get document type by ID."""
        try:
            item = self.schema_container.read_item(
                item=str(type_id),
                partition_key='document_type'
            )
            return DocumentType.model_validate(item)
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def list_document_types(self, active_only: bool = True) -> List[DocumentType]:
        """List all document types."""
        query = "SELECT * FROM c WHERE c.type = 'document_type'"
        if active_only:
            query += " AND c.is_active = true"
        
        items = list(self.schema_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return [DocumentType.model_validate(item) for item in items]
    
    # Schema Version operations
    
    async def create_schema_version(self, version: DocumentTypeVersion) -> DocumentTypeVersion:
        """Create a new schema version."""
        item = version.model_dump(mode='json')
        item['id'] = str(version.id)
        item['partition_key'] = str(version.document_type_id)
        item['type'] = 'schema_version'
        
        created = self.schema_container.create_item(item)
        return DocumentTypeVersion.model_validate(created)
    
    async def get_schema_version(
        self, 
        document_type_id: UUID,
        version: str
    ) -> Optional[DocumentTypeVersion]:
        """Get schema version by document type and version string."""
        query = """
            SELECT * FROM c 
            WHERE c.type = 'schema_version' 
            AND c.document_type_id = @type_id 
            AND c.version = @version
            AND c.is_active = true
        """
        parameters = [
            {"name": "@type_id", "value": str(document_type_id)},
            {"name": "@version", "value": version}
        ]
        
        items = list(self.schema_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=str(document_type_id)
        ))
        
        return DocumentTypeVersion.model_validate(items[0]) if items else None
    
    async def list_schema_versions(
        self,
        document_type_id: UUID,
        active_only: bool = True
    ) -> List[DocumentTypeVersion]:
        """List all versions for a document type."""
        query = """
            SELECT * FROM c 
            WHERE c.type = 'schema_version' 
            AND c.document_type_id = @type_id
        """
        if active_only:
            query += " AND c.is_active = true"
        query += " ORDER BY c.created_at DESC"
        
        parameters = [
            {"name": "@type_id", "value": str(document_type_id)}
        ]
        
        items = list(self.schema_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=str(document_type_id)
        ))
        return [DocumentTypeVersion.model_validate(item) for item in items]
