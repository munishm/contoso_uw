"""Repository for extraction results in Cosmos DB.

Extraction results are stored directly in the documents container,
embedded within each document record under the 'extraction' field.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from azure.cosmos import ContainerProxy, DatabaseProxy, exceptions

from ..models import ExtractionResult, ExtractionStatus

logger = logging.getLogger(__name__)


class ExtractionRepository:
    """Repository for managing extraction results embedded in documents."""
    
    def __init__(self, database: DatabaseProxy):
        """
        Initialize extraction repository.
        
        Args:
            database: Cosmos DB database client
        """
        self.database = database
        self._documents_container: Optional[ContainerProxy] = None
    
    @property
    def documents_container(self) -> ContainerProxy:
        """Get documents container (extraction results are embedded in documents)."""
        if self._documents_container is None:
            self._documents_container = self.database.get_container_client("documents")
        return self._documents_container
    
    async def create_extraction(self, extraction: ExtractionResult) -> ExtractionResult:
        """
        Create a new extraction result.
        
        Note: For the workflow, we create a temporary extraction record.
        The actual persistence happens when update_extraction is called,
        which updates the document record with the extraction results.
        """
        logger.info(f"ExtractionRepository: Created extraction record (in-memory): {extraction.id}")
        return extraction
    
    async def get_extraction(self, extraction_id: UUID) -> Optional[ExtractionResult]:
        """Get extraction result by ID from documents container."""
        # Query documents that have this extraction_id
        query = "SELECT * FROM c WHERE c.extraction.extraction_id = @extraction_id"
        parameters = [{"name": "@extraction_id", "value": str(extraction_id)}]
        
        items = list(self.documents_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            doc = items[0]
            extraction_data = doc.get("extraction", {})
            return self._extraction_from_document(extraction_data, doc.get("id"))
        
        return None
    
    async def update_extraction(
        self, 
        extraction: ExtractionResult,
        evaluation_results: dict = None
    ) -> ExtractionResult:
        """
        Update extraction result by updating the document record.
        
        This embeds the extraction results directly in the document.
        
        Args:
            extraction: Extraction result to save
            evaluation_results: Optional evaluation results from batch evaluation
        """
        print(f"\n>>> update_extraction CALLED: extraction_id={extraction.id}, document_id={extraction.document_id}")
        print(f">>> evaluation_results provided: {evaluation_results is not None}")
        if evaluation_results:
            print(f">>> evaluation_results keys: {evaluation_results.keys()}")
        
        logger.info(f"ExtractionRepository: Updating extraction {extraction.id} for document {extraction.document_id}")
        
        # Find the document by document_id
        # The document_id in extraction might be the filename stem, so we need to query
        query = """
            SELECT * FROM c 
            WHERE c.id = @doc_id 
            OR CONTAINS(c.filename, @doc_id)
            OR CONTAINS(c.blob_path, @doc_id)
        """
        parameters = [{"name": "@doc_id", "value": extraction.document_id}]
        
        print(f">>> Querying for document_id: {extraction.document_id}")
        
        items = list(self.documents_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        print(f">>> Query returned {len(items)} items")
        
        if not items:
            print(f">>> WARNING: No document found!")
            logger.warning(f"ExtractionRepository: Document not found for extraction {extraction.id}, document_id={extraction.document_id}")
            # Return the extraction as-is (workflow will handle it)
            return extraction
        
        doc = items[0]
        case_id = doc.get("case_id")
        print(f">>> Found document: id={doc.get('id')}, case_id={case_id}")
        
        # Build extraction data to embed in document
        extraction_data = {
            "extraction_id": str(extraction.id),
            "document_type_id": str(extraction.document_type_id),
            "version_id": str(extraction.version_id),
            "status": extraction.status.value,
            "models_used": extraction.models_used,
            "fields": [field.model_dump(mode='json') for field in extraction.fields],
            "processing_duration_ms": extraction.processing_duration_ms,
            "error_message": extraction.error_message,
            "needs_review": any(f.needs_review for f in extraction.fields),
            "extraction_started_at": extraction.created_at.isoformat() if extraction.created_at else None,
            "extraction_completed_at": extraction.completed_at.isoformat() if extraction.completed_at else None,
        }
        
        # Add evaluation results if provided
        if evaluation_results:
            extraction_data["evaluation"] = evaluation_results
            logger.info(f"Added evaluation results to extraction data: {len(evaluation_results.get('results', []))} field evaluations")
        else:
            logger.info("No evaluation results provided")
        
        # Update the document with extraction results
        doc["extraction"] = extraction_data
        doc["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"ExtractionRepository: About to update document {doc['id']}, case_id={case_id}")
        logger.info(f"ExtractionRepository: extraction_data has evaluation: {'evaluation' in extraction_data}")
        
        # Print the full extraction_data structure for debugging
        import json
        print("\n" + "="*60)
        print("EXTRACTION DATA TO BE SAVED:")
        print("="*60)
        print(json.dumps(extraction_data, indent=2, default=str))
        print("="*60 + "\n")
        
        try:
            updated = self.documents_container.replace_item(
                item=doc["id"],
                body=doc
            )
            logger.info(f"ExtractionRepository: Updated document {doc['id']} with extraction results (including evaluation: {'evaluation' in extraction_data})")
            
            # Verify what was saved by reading it back 
            saved_doc = self.documents_container.read_item(item=doc["id"], partition_key=case_id)
            saved_extraction = saved_doc.get("extraction", {})
            print("\n" + "="*60)
            print("VERIFICATION - SAVED EXTRACTION DATA:")
            print("="*60)
            print(f"Has evaluation: {'evaluation' in saved_extraction}")
            if 'evaluation' in saved_extraction:
                eval_data = saved_extraction['evaluation']
                print(f"Evaluation total_fields: {eval_data.get('total_fields')}")
                print(f"Evaluation results count: {len(eval_data.get('results', []))}")
            print("="*60 + "\n")
            
            # Set evaluation on the extraction object so it's available to workflow
            if evaluation_results:
                extraction.evaluation = evaluation_results
                logger.info(f"ExtractionRepository: Set evaluation on extraction object")
            
            return extraction
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"ExtractionRepository: Document {doc['id']} not found for update")
            return extraction
        except Exception as e:
            logger.error(f"ExtractionRepository: Failed to update document {doc['id']}: {e}", exc_info=True)
            return extraction
    
    async def list_extractions_for_document(
        self,
        document_id: str,
        status: Optional[ExtractionStatus] = None,
        limit: int = 100
    ) -> List[ExtractionResult]:
        """List extraction results for a specific document."""
        query = "SELECT * FROM c WHERE c.id = @doc_id AND IS_DEFINED(c.extraction)"
        parameters = [{"name": "@doc_id", "value": document_id}]
        
        if status:
            query += " AND c.extraction.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        items = list(self.documents_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
            max_item_count=limit
        ))
        
        results = []
        for doc in items:
            extraction_data = doc.get("extraction", {})
            if extraction_data:
                result = self._extraction_from_document(extraction_data, doc.get("id"))
                if result:
                    results.append(result)
        
        return results
    
    async def list_pending_extractions(self, limit: int = 100) -> List[ExtractionResult]:
        """List all documents with pending extraction results."""
        query = """
            SELECT * FROM c 
            WHERE IS_DEFINED(c.extraction) 
            AND c.extraction.status IN (@pending, @in_progress)
            ORDER BY c.created_at ASC
        """
        parameters = [
            {"name": "@pending", "value": ExtractionStatus.PENDING.value},
            {"name": "@in_progress", "value": ExtractionStatus.IN_PROGRESS.value}
        ]
        
        items = list(self.documents_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
            max_item_count=limit
        ))
        
        results = []
        for doc in items:
            extraction_data = doc.get("extraction", {})
            if extraction_data:
                result = self._extraction_from_document(extraction_data, doc.get("id"))
                if result:
                    results.append(result)
        
        return results
    
    def _extraction_from_document(self, extraction_data: dict, document_id: str) -> Optional[ExtractionResult]:
        """Convert embedded extraction data to ExtractionResult model."""
        if not extraction_data:
            return None
        
        try:
            return ExtractionResult(
                id=UUID(extraction_data.get("extraction_id")) if extraction_data.get("extraction_id") else None,
                document_id=document_id,
                document_type_id=UUID(extraction_data.get("document_type_id")) if extraction_data.get("document_type_id") else UUID(int=0),
                version_id=UUID(extraction_data.get("version_id")) if extraction_data.get("version_id") else UUID(int=0),
                status=ExtractionStatus(extraction_data.get("status", "pending")),
                models_used=extraction_data.get("models_used", []),
                fields=extraction_data.get("fields", []),
                processing_duration_ms=extraction_data.get("processing_duration_ms"),
                error_message=extraction_data.get("error_message"),
                created_at=datetime.fromisoformat(extraction_data["extraction_started_at"]) if extraction_data.get("extraction_started_at") else None,
                completed_at=datetime.fromisoformat(extraction_data["extraction_completed_at"]) if extraction_data.get("extraction_completed_at") else None,
            )
        except Exception as e:
            logger.error(f"ExtractionRepository: Failed to parse extraction data: {e}")
            return None
