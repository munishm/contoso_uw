"""Repository for extraction models in Cosmos DB."""

from typing import List, Optional
from uuid import UUID

from azure.cosmos import ContainerProxy, DatabaseProxy, exceptions

from ..models import ExtractionModel, ModelType


class ExtractionModelRepository:
    """Repository for managing extraction models."""
    
    def __init__(self, database: DatabaseProxy):
        """
        Initialize extraction model repository.
        
        Args:
            database: Cosmos DB database client
        """
        self.database = database
        self._models_container: Optional[ContainerProxy] = None
    
    @property
    def models_container(self) -> ContainerProxy:
        """Get or create models container."""
        if self._models_container is None:
            from ..config import get_config
            config = get_config()
            self._models_container = self.database.get_container_client(
                config.cosmos_container_models
            )
        return self._models_container
    
    async def create_model(self, model: ExtractionModel) -> ExtractionModel:
        """Create a new extraction model."""
        item = model.model_dump(mode='json')
        item['id'] = str(model.id)
        item['partition_key'] = model.type.value
        
        created = self.models_container.create_item(item)
        return ExtractionModel.model_validate(created)
    
    async def get_model(self, model_id: UUID) -> Optional[ExtractionModel]:
        """Get extraction model by ID."""
        # Query since we don't know the partition key
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": str(model_id)}]
        
        items = list(self.models_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return ExtractionModel.model_validate(items[0]) if items else None
    
    async def list_models(
        self,
        model_type: Optional[ModelType] = None,
        active_only: bool = True
    ) -> List[ExtractionModel]:
        """List extraction models."""
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []
        
        if model_type:
            query += " AND c.type = @type"
            parameters.append({"name": "@type", "value": model_type.value})
        
        if active_only:
            query += " AND c.is_active = true"
        
        items = list(self.models_container.query_items(
            query=query,
            parameters=parameters if parameters else None,
            enable_cross_partition_query=True
        ))
        return [ExtractionModel.model_validate(item) for item in items]
    
    async def get_models_by_ids(self, model_ids: List[UUID]) -> List[ExtractionModel]:
        """Get multiple models by their IDs."""
        if not model_ids:
            return []
        
        # Convert UUIDs to strings for query
        id_strings = [str(mid) for mid in model_ids]
        placeholders = ", ".join([f"@id{i}" for i in range(len(id_strings))])
        
        query = f"SELECT * FROM c WHERE c.id IN ({placeholders})"
        parameters = [
            {"name": f"@id{i}", "value": id_str}
            for i, id_str in enumerate(id_strings)
        ]
        
        items = list(self.models_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return [ExtractionModel.model_validate(item) for item in items]
