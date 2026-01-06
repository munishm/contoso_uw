"""Repository for extraction results in Cosmos DB."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from azure.cosmos import ContainerProxy, DatabaseProxy, exceptions

from ..models import ExtractionResult, ExtractionStatus


class ExtractionRepository:
    """Repository for managing extraction results."""
    
    def __init__(self, database: DatabaseProxy):
        """
        Initialize extraction repository.
        
        Args:
            database: Cosmos DB database client
        """
        self.database = database
        self._results_container: Optional[ContainerProxy] = None
    
    @property
    def results_container(self) -> ContainerProxy:
        """Get or create results container."""
        if self._results_container is None:
            from ..config import get_config
            config = get_config()
            self._results_container = self.database.get_container_client(
                config.cosmos_container_results
            )
        return self._results_container
    
    async def create_extraction(self, extraction: ExtractionResult) -> ExtractionResult:
        """Create a new extraction result."""
        item = extraction.model_dump(mode='json')
        item['id'] = str(extraction.id)
        item['partition_key'] = extraction.document_id
        
        created = self.results_container.create_item(item)
        return ExtractionResult.model_validate(created)
    
    async def get_extraction(self, extraction_id: UUID) -> Optional[ExtractionResult]:
        """Get extraction result by ID."""
        # Query since we don't know the document_id (partition key)
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": str(extraction_id)}]
        
        items = list(self.results_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return ExtractionResult.model_validate(items[0]) if items else None
    
    async def update_extraction(self, extraction: ExtractionResult) -> ExtractionResult:
        """Update an existing extraction result."""
        item = extraction.model_dump(mode='json')
        item['id'] = str(extraction.id)
        item['partition_key'] = extraction.document_id
        
        updated = self.results_container.replace_item(
            item=str(extraction.id),
            body=item
        )
        return ExtractionResult.model_validate(updated)
    
    async def list_extractions_for_document(
        self,
        document_id: str,
        status: Optional[ExtractionStatus] = None,
        limit: int = 100
    ) -> List[ExtractionResult]:
        """List extraction results for a specific document."""
        query = "SELECT * FROM c WHERE c.document_id = @doc_id"
        parameters = [{"name": "@doc_id", "value": document_id}]
        
        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        query += " ORDER BY c.created_at DESC"
        
        items = list(self.results_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=document_id,
            max_item_count=limit
        ))
        return [ExtractionResult.model_validate(item) for item in items]
    
    async def list_pending_extractions(self, limit: int = 100) -> List[ExtractionResult]:
        """List all pending extraction results."""
        query = """
            SELECT * FROM c 
            WHERE c.status IN (@pending, @in_progress)
            ORDER BY c.created_at ASC
        """
        parameters = [
            {"name": "@pending", "value": ExtractionStatus.PENDING.value},
            {"name": "@in_progress", "value": ExtractionStatus.IN_PROGRESS.value}
        ]
        
        items = list(self.results_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
            max_item_count=limit
        ))
        return [ExtractionResult.model_validate(item) for item in items]
