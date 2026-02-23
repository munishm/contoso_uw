"""
Case workflow orchestration: classification → file upload & DB update → extraction
Config-driven, production-ready implementation.

This module provides:
1. WorkflowConfig - YAML/dict-based config for defining workflow steps
2. Processor wrappers for classifier, file upload, extraction
3. CaseWorkflowManager - orchestrates case processing workflows
"""

import asyncio
import logging
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum

from src.orchestration.pipeline import PipelineBuilder
from src.orchestration.workflow import orchestrator, WorkflowStep, WorkflowStatus
from src.orchestration.registry import registry
from src.interfaces.classifier import DocumentClassifier
from src.interfaces.processor import IDocumentProcessor
from src.shared.models.classification import ClassificationResponse, Documents

logger = logging.getLogger(__name__)


# =============================================================================
# Workflow Configuration
# =============================================================================

class StepType(str, Enum):
    """Supported workflow step types."""
    CLASSIFICATION = "classification"
    FILE_UPLOAD = "file_upload"
    DB_UPDATE = "db_update"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    CUSTOM = "custom"


@dataclass
class StepConfig:
    """Configuration for a single workflow step."""
    name: str
    type: StepType
    component: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    enabled: bool = True
    skip_on_error: bool = False
    retry_count: int = 0
    timeout_seconds: Optional[int] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """Configuration for a complete workflow."""
    name: str
    version: str
    description: str
    steps: List[StepConfig]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """Create WorkflowConfig from dictionary."""
        steps = [
            StepConfig(
                name=step["name"],
                type=StepType(step["type"]),
                component=step["component"],
                inputs=step.get("inputs", {}),
                outputs=step.get("outputs", []),
                enabled=step.get("enabled", True),
                skip_on_error=step.get("skip_on_error", False),
                retry_count=step.get("retry_count", 0),
                timeout_seconds=step.get("timeout_seconds"),
                config=step.get("config", {})
            )
            for step in data.get("steps", [])
        ]
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            steps=steps,
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "WorkflowConfig":
        """Load WorkflowConfig from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "steps": [
                {
                    "name": step.name,
                    "type": step.type.value,
                    "component": step.component,
                    "inputs": step.inputs,
                    "outputs": step.outputs,
                    "enabled": step.enabled,
                    "skip_on_error": step.skip_on_error,
                    "retry_count": step.retry_count,
                    "timeout_seconds": step.timeout_seconds,
                    "config": step.config
                }
                for step in self.steps
            ],
            "metadata": self.metadata
        }


# =============================================================================
# Processor Implementations
# =============================================================================

class ClassifierProcessor(IDocumentProcessor):
    """
    Classifier processor that wraps DocumentClassifier for workflow integration.
    
    Implements IDocumentProcessor interface to work with the orchestration system.
    Returns ClassificationResponse with documents array (file paths, types, metadata).
    """
    
    def __init__(self):
        self._classifier = DocumentClassifier()
        self._name = "classifier"
        self._version = "1.0.0"
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document through classification.
        
        Args:
            inputs: Dict containing 'document' key with document info (path/file_path)
            
        Returns:
            Dict with 'classification_response' containing ClassificationResponse
        """
        logger.info("#" * 60)
        logger.info("STEP 1: CLASSIFICATION - INPUT RECEIVED")
        logger.info("#" * 60)
        logger.info(f"Input keys: {list(inputs.keys())}")
        logger.info(f"  - document: {inputs.get('document')}")
        logger.info(f"  - case_id: {inputs.get('case_id')}")
        logger.info(f"  - blob_path: {inputs.get('blob_path')}")
        logger.info("-" * 60)
        
        # Extract document from inputs - workflow passes {"document": {...}}
        document = inputs.get("document", inputs)
        
        # If document is a string (path), convert to dict
        if isinstance(document, str):
            document = {"path": document}
        
        file_path = document.get('path') or document.get('file_path')
        logger.info(f"ClassifierProcessor: Document path = {file_path}")
        
        # Validate input
        if not self.validate_input(document):
            raise ValueError("Invalid input: document must contain 'path' or 'file_path'")
        
        # Perform classification
        classification_response = self._classifier.classify(document)
        
        # Detailed logging of classification results
        logger.info("=" * 50)
        logger.info("CLASSIFIER PROCESSOR - RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total pages in document: {classification_response.total_pages}")
        logger.info(f"Total segments identified: {classification_response.total_segments}")
        logger.info(f"Number of subdocuments: {len(classification_response.documents or [])}")
        
        # Log each subdocument with its file path
        if classification_response.documents:
            logger.info("Subdocuments (split files):")
            for idx, doc in enumerate(classification_response.documents):
                logger.info(f"  [{idx + 1}] Type: {doc.document_type}")
                logger.info(f"      File Path: {doc.file_path}")
        
        # Log page-level classification
        if classification_response.pages:
            logger.info(f"Page-level classifications ({len(classification_response.pages)} pages):")
            for page in classification_response.pages[:10]:  # Log first 10 pages
                logger.info(f"  Page {page.page_number}: {page.document_type} (confidence: {page.confidence})")
            if len(classification_response.pages) > 10:
                logger.info(f"  ... and {len(classification_response.pages) - 10} more pages")
        
        logger.info("=" * 50)
        
        return {
            "classification_response": classification_response,
            "documents": classification_response.documents,
            "pages": classification_response.pages,
            "total_pages": classification_response.total_pages,
            "total_segments": classification_response.total_segments
        }
    
    def validate_input(self, document: Dict[str, Any]) -> bool:
        """Validate document has required path."""
        # Handle both direct document dict and inputs wrapper
        if isinstance(document, str):
            return True
        doc = document.get("document", document) if isinstance(document, dict) else document
        if isinstance(doc, str):
            return True
        return bool(doc.get('path') or doc.get('file_path'))
    
    def get_supported_types(self) -> List[str]:
        """Get supported MIME types."""
        return ["application/pdf", "image/png", "image/jpeg", "image/tiff"]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version


class FileUploadProcessor(IDocumentProcessor):
    """
    File upload processor - prepares files for blob storage upload.
    
    NOTE: Actual Azure Blob Storage operations are handled by case_service.py
    which has access to the StorageService with proper Azure AD authentication.
    This processor prepares the upload manifest and target blob paths.
    
    This separation ensures:
    1. Clean async/await handling (StorageService is async)
    2. Proper Azure AD credential management via FastAPI DI
    3. Consistent blob path generation across the application
    """
    
    def __init__(self):
        self._name = "file_upload"
        self._version = "2.0.0"  # Version bump for refactored approach
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare files for blob storage upload.
        
        This processor no longer performs actual blob uploads. Instead, it:
        1. Builds the target blob path for each document
        2. Prepares an upload manifest for case_service.py to execute
        
        Args:
            inputs: Dict with 'classification_response' or 'documents' array, and 'case_id'
            
        Returns:
            Dict with prepared upload information (paths and file references)
        """
        logger.info("#" * 60)
        logger.info("STEP 2: FILE UPLOAD (PREPARE) - INPUT RECEIVED")
        logger.info("#" * 60)
        logger.info(f"Input keys: {list(inputs.keys())}")
        logger.info(f"  - case_id: {inputs.get('case_id')}")
        
        # Log classification_response details
        cr = inputs.get('classification_response')
        if cr:
            logger.info(f"  - classification_response: ClassificationResponse(")
            logger.info(f"      analyzer_id={cr.analyzer_id},")
            logger.info(f"      total_pages={cr.total_pages},")
            logger.info(f"      total_segments={cr.total_segments},")
            logger.info(f"      documents_count={len(cr.documents) if cr.documents else 0},")
            logger.info(f"      pages_count={len(cr.pages) if cr.pages else 0})")
        else:
            logger.info(f"  - classification_response: None")
        
        # Log documents array
        docs = inputs.get('documents')
        if docs:
            logger.info(f"  - documents: [{len(docs)} items]")
            for idx, d in enumerate(docs[:5]):  # Show first 5
                doc_type = d.document_type if hasattr(d, 'document_type') else d.get('document_type')
                file_path = d.file_path if hasattr(d, 'file_path') else d.get('file_path')
                logger.info(f"      [{idx+1}] type={doc_type}, path={file_path}")
            if len(docs) > 5:
                logger.info(f"      ... and {len(docs) - 5} more")
        else:
            logger.info(f"  - documents: None")
        logger.info("-" * 60)
        
        # Get case_id for blob path
        case_id = inputs.get("case_id")
        
        # Get documents from classification response
        classification_response = inputs.get("classification_response")
        documents = inputs.get("documents") or (
            classification_response.documents if classification_response else []
        )
        
        logger.info(f"Processing Case ID: {case_id}")
        logger.info(f"Preparing {len(documents) if documents else 0} subdocuments for upload")
        
        if not documents:
            logger.warning("FileUploadProcessor: No documents to prepare for upload")
            return {
                "uploaded_files": [],
                "upload_status": "skipped",
                "classification_response": classification_response
            }
        
        uploaded_files = []
        for idx, doc in enumerate(documents):
            file_path = doc.file_path if isinstance(doc, Documents) else doc.get("file_path")
            doc_type = doc.document_type if isinstance(doc, Documents) else doc.get("document_type")
            
            logger.info(f"Preparing subdocument [{idx + 1}/{len(documents)}]:")
            logger.info(f"  Source: {file_path}")
            logger.info(f"  Type: {doc_type}")
            
            # Generate target blob path (actual upload handled by case_service.py)
            blob_path = self._generate_blob_path(file_path, doc_type, case_id)
            
            uploaded_files.append({
                "document_type": doc_type,
                "original_path": file_path,  # Local file path for reading content
                "blob_path": blob_path,      # Target blob path for upload
                "upload_status": "pending",  # Will be updated by case_service.py
            })
            
            logger.info(f"  Target Blob Path: {blob_path}")
            logger.info(f"  Status: PREPARED (pending upload)")
        
        logger.info("-" * 50)
        logger.info(f"UPLOAD PREPARE COMPLETE: {len(uploaded_files)} files ready for upload")
        logger.info("NOTE: Actual blob upload handled by case_service.py via StorageService")
        logger.info("=" * 50)
        
        return {
            "uploaded_files": uploaded_files,
            "upload_status": "prepared",
            "classification_response": classification_response,
            "documents": documents
        }
    
    def _generate_blob_path(self, file_path: str, document_type: str, case_id: Optional[str] = None) -> str:
        """
        Generate the target blob path for a document.
        
        Args:
            file_path: Local file path (used to extract filename)
            document_type: Classification type of the document
            case_id: Case ID for organizing files in blob
            
        Returns:
            Blob path in format: {case_id}/documents/sub-documents/{doc_type}/{filename}
        """
        file_name = Path(file_path).name
        # Clean document type for path (replace spaces with underscores)
        clean_doc_type = document_type.replace(" ", "_").lower()
        
        if case_id:
            # Format: {case_id}/documents/sub-documents/{doc_type}/{filename}
            return f"{case_id}/documents/sub-documents/{clean_doc_type}/{file_name}"
        else:
            # Fallback if no case_id
            return f"documents/sub-documents/{clean_doc_type}/{file_name}"
    
    def validate_input(self, document: Dict[str, Any]) -> bool:
        return bool(
            document.get("classification_response") or 
            document.get("documents")
        )
    
    def get_supported_types(self) -> List[str]:
        return ["ClassificationResponse"]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version


class DatabaseUpdateProcessor(IDocumentProcessor):
    """
    Database update processor - prepares document data for DB insertion.
    
    NOTE: Actual Cosmos DB operations are handled by case_service.py which has
    proper async context. This processor prepares the document records and
    passes them through the workflow for the service layer to persist.
    
    This separation ensures:
    1. Clean async/await handling (no sync-to-async bridging issues)
    2. Repository access in proper FastAPI dependency injection context
    3. Transaction consistency with case status updates
    """
    
    def __init__(self):
        self._name = "db_update"
        self._version = "2.0.0"  # Version bump for refactored approach
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare document records for database insertion.
        
        This processor no longer performs actual DB operations. Instead, it:
        1. Builds document record structures from workflow data
        2. Passes prepared records through for case_service.py to persist
        
        Args:
            inputs: Dict with processing results from previous steps
            
        Returns:
            Dict with prepared document records and metadata
        """
        from datetime import datetime, timezone
        from pathlib import Path
        import uuid
        
        logger.info("#" * 60)
        logger.info("STEP 3: DB UPDATE (PREPARE) - INPUT RECEIVED")
        logger.info("#" * 60)
        logger.info(f"Input keys: {list(inputs.keys())}")
        logger.info(f"  - case_id: {inputs.get('case_id')}")
        
        # Log classification_response
        cr = inputs.get('classification_response')
        if cr:
            logger.info(f"  - classification_response: ClassificationResponse(total_pages={cr.total_pages}, total_segments={cr.total_segments})")
        else:
            logger.info(f"  - classification_response: None")
        
        # Log uploaded_files
        uf = inputs.get('uploaded_files', [])
        logger.info(f"  - uploaded_files: [{len(uf)} items]")
        for idx, f in enumerate(uf[:5]):
            logger.info(f"      [{idx+1}] type={f.get('document_type')}, blob_path={f.get('blob_path')}")
        if len(uf) > 5:
            logger.info(f"      ... and {len(uf) - 5} more")
        
        # Log pages
        pg = inputs.get('pages', [])
        logger.info(f"  - pages: [{len(pg)} items]")
        if pg:
            # Show page distribution by type
            page_types = {}
            for p in pg:
                dt = p.document_type if hasattr(p, 'document_type') else p.get('document_type')
                page_types[dt] = page_types.get(dt, 0) + 1
            for dt, count in page_types.items():
                logger.info(f"      {dt}: {count} pages")
        logger.info("-" * 60)
        
        case_id = inputs.get("case_id")
        classification_response = inputs.get("classification_response")
        uploaded_files = inputs.get("uploaded_files", [])
        pages = inputs.get("pages", [])
        
        logger.info(f"Processing Case ID: {case_id}")
        logger.info(f"Preparing {len(uploaded_files)} document records")
        
        if not case_id:
            logger.warning("No case_id provided - skipping document record preparation")
            return {
                "prepared_documents": [],
                "db_update_status": "skipped",
                "classification_response": classification_response,
                "uploaded_files": uploaded_files
            }
        
        # Build page mapping for each document type
        page_mapping = {}
        if pages:
            for page in pages:
                doc_type = page.document_type if hasattr(page, 'document_type') else page.get('document_type')
                page_num = page.page_number if hasattr(page, 'page_number') else page.get('page_number')
                confidence = page.confidence if hasattr(page, 'confidence') else page.get('confidence')
                
                if doc_type not in page_mapping:
                    page_mapping[doc_type] = {"pages": [], "confidences": []}
                page_mapping[doc_type]["pages"].append(page_num)
                if confidence:
                    page_mapping[doc_type]["confidences"].append(confidence)
        
        prepared_documents = []
        
        for idx, uploaded_file in enumerate(uploaded_files):
            doc_type = uploaded_file["document_type"]
            blob_path = uploaded_file["blob_path"]
            original_path = uploaded_file["original_path"]
            
            # Get page info for this document type
            doc_pages = page_mapping.get(doc_type, {})
            page_numbers = doc_pages.get("pages", [])
            confidences = doc_pages.get("confidences", [])
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            # Prepare document record (will be persisted by case_service.py)
            document_record = {
                "document_type": doc_type,
                "blob_path": blob_path,
                "original_path": original_path,
                "filename": Path(original_path).name,
                "page_numbers": page_numbers,
                "page_count": len(page_numbers),
                "classification_confidence": avg_confidence,
                "classifier_id": classification_response.analyzer_id if classification_response else None,
            }
            
            prepared_documents.append(document_record)
            
            logger.info(f"Prepared document record [{idx + 1}/{len(uploaded_files)}]:")
            logger.info(f"  Document Type: {doc_type}")
            logger.info(f"  Blob Path: {blob_path}")
            logger.info(f"  Pages: {page_numbers}")
            logger.info(f"  Confidence: {avg_confidence}")
        
        logger.info("-" * 50)
        logger.info(f"DB UPDATE (PREPARE) COMPLETE: {len(prepared_documents)} document records prepared")
        logger.info("NOTE: Actual DB insertion handled by case_service.py")
        logger.info("=" * 50)
        
        # Get documents from classification_response for extraction step
        documents = classification_response.documents if classification_response else []
        
        return {
            "prepared_documents": prepared_documents,
            "db_update_status": "prepared",
            "classification_response": classification_response,
            "uploaded_files": uploaded_files,
            "documents": documents  # Pass through for extraction step
        }
    
    def validate_input(self, document: Dict[str, Any]) -> bool:
        return bool(document.get("uploaded_files"))
    
    def get_supported_types(self) -> List[str]:
        return ["UploadResult"]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version


class ExtractionProcessor(IDocumentProcessor):
    """
    Entity extraction processor.
    
    Extracts entities from classified documents using the SchemaExtractionService.
    Receives classification output (documents array with file paths and metadata).
    """
    
    # Default schema version (can be overridden via config)
    DEFAULT_SCHEMA_VERSION = "1.0.0"
    
    # Document types to extract (only these will be processed)
    EXTRACTABLE_DOCUMENT_TYPES = ["Application", "Application Form"]
    
    def __init__(self):
        self._name = "extractor"
        self._version = "2.0.0"  # Version bump for actual extraction implementation
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from documents.
        
        Args:
            inputs: Dict with classification_response and documents
            
        Returns:
            Dict with extracted entities
        """
        import asyncio
        
        logger.info("#" * 60)
        logger.info("STEP 4: EXTRACTION - INPUT RECEIVED")
        logger.info("#" * 60)
        logger.info(f"Input keys: {list(inputs.keys())}")
        
        # Log classification_response
        cr = inputs.get('classification_response')
        if cr:
            logger.info(f"  - classification_response: ClassificationResponse(total_pages={cr.total_pages}, total_segments={cr.total_segments})")
        else:
            logger.info(f"  - classification_response: None")
        
        # Log documents
        docs = inputs.get('documents')
        if docs:
            logger.info(f"  - documents: [{len(docs)} items]")
            for idx, d in enumerate(docs[:5]):
                doc_type = d.document_type if hasattr(d, 'document_type') else d.get('document_type')
                file_path = d.file_path if hasattr(d, 'file_path') else d.get('file_path')
                logger.info(f"      [{idx+1}] type={doc_type}, path={file_path}")
            if len(docs) > 5:
                logger.info(f"      ... and {len(docs) - 5} more")
        else:
            logger.info(f"  - documents: None")
        logger.info("-" * 60)
        
        classification_response = inputs.get("classification_response")
        documents = inputs.get("documents") or (
            classification_response.documents if classification_response else []
        )
        
        extracted_results = []
        for doc in documents:
            file_path = doc.file_path if isinstance(doc, Documents) else doc.get("file_path")
            doc_type = doc.document_type if isinstance(doc, Documents) else doc.get("document_type")
            
            # Check if this document type should be extracted
            if doc_type not in self.EXTRACTABLE_DOCUMENT_TYPES:
                logger.info(f"ExtractionProcessor: Skipping {doc_type} (not in extractable types: {self.EXTRACTABLE_DOCUMENT_TYPES})")
                extracted_results.append({
                    "document_type": doc_type,
                    "file_path": file_path,
                    "extraction_result": None,
                    "status": "skipped",
                    "reason": f"Document type '{doc_type}' not configured for extraction"
                })
                continue
            
            logger.info(f"ExtractionProcessor: Processing {doc_type} from {file_path}")
            
            # Call extraction service
            try:
                extraction_result = self._extract_document(
                    file_path=file_path,
                    document_type=doc_type,
                    schema_version=self.DEFAULT_SCHEMA_VERSION
                )
                extracted_results.append({
                    "document_type": doc_type,
                    "file_path": file_path,
                    "extraction_result": extraction_result,
                    "status": "success"
                })
                logger.info(f"  ✓ Extraction completed for {doc_type}")
            except Exception as e:
                logger.error(f"  ✗ Extraction failed for {doc_type}: {e}")
                extracted_results.append({
                    "document_type": doc_type,
                    "file_path": file_path,
                    "extraction_result": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        successful = sum(1 for r in extracted_results if r["status"] == "success")
        skipped = sum(1 for r in extracted_results if r["status"] == "skipped")
        logger.info("-" * 50)
        logger.info(f"EXTRACTION COMPLETE: {successful} extracted, {skipped} skipped, {len(extracted_results) - successful - skipped} failed")
        logger.info("=" * 50)
        
        return {
            "extracted_entities": extracted_results,
            "classification_response": classification_response,
            "extraction_status": "success" if successful == len(extracted_results) else "partial"
        }
    
    def _extract_document(
        self, 
        file_path: str, 
        document_type: str,
        schema_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Extract entities from a document using SchemaExtractionService.
        
        Args:
            file_path: Path to the document file
            document_type: Classification type of the document (e.g., "Lab Report")
            schema_version: Schema version to use for extraction
            
        Returns:
            Dictionary with extraction results
        """
        import asyncio
        
        try:
            # Import extraction service
            from src.entity_extraction.services.orchestration_interface import (
                extract_document_for_workflow
            )
            
            # Read document content from file
            with open(file_path, "rb") as f:
                document_content = f.read()
            
            # Generate a document ID based on file path
            document_id = Path(file_path).stem
            
            logger.info(f"  Calling extraction service:")
            logger.info(f"    - document_id: {document_id}")
            logger.info(f"    - document_type: {document_type}")
            logger.info(f"    - schema_version: {schema_version}")
            logger.info(f"    - content_size: {len(document_content)} bytes")
            
            # Run async extraction in sync context
            # Use asyncio.run() which creates a new event loop for this thread
            # This works correctly even when called from a ThreadPoolExecutor
            result = asyncio.run(
                self._extract_async(
                    document_id=document_id,
                    document_content=document_content,
                    document_type=document_type,
                    schema_version=schema_version
                )
            )
            
            return result
            
        except Exception as e:
            logger.error(f"  Extraction service error: {e}")
            import traceback
            logger.error(f"  Traceback: {traceback.format_exc()}")
            # Return placeholder on error
            return {
                "status": "error",
                "error": str(e),
                "entities": []
            }
    
    async def _extract_async(
        self,
        document_id: str,
        document_content: bytes,
        document_type: str,
        schema_version: str
    ) -> Dict[str, Any]:
        """
        Async extraction helper.
        
        Args:
            document_id: Document identifier
            document_content: Document bytes
            document_type: Document type name (e.g., "Lab Report")
            schema_version: Schema version
            
        Returns:
            Extraction result dictionary
        """
        try:
            from src.entity_extraction.services.orchestration_interface import (
                extract_document_for_workflow
            )
            
            # Use the unified extraction function (accepts name or UUID)
            result = await extract_document_for_workflow(
                document_id=document_id,
                document_content=document_content,
                document_type=document_type,
                schema_version=schema_version
            )
            return result
            
        except ImportError:
            # Fallback if the function doesn't exist yet
            logger.warning("extract_document_for_workflow not available, using placeholder")
            return {
                "status": "placeholder",
                "document_type": document_type,
                "entities": [
                    {"type": "placeholder", "value": f"Entity from {document_type}", "confidence": 0.95}
                ]
            }
        except Exception as e:
            logger.error(f"Async extraction error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "entities": []
            }
    
    def validate_input(self, document: Dict[str, Any]) -> bool:
        return bool(
            document.get("classification_response") or 
            document.get("documents")
        )
    
    def get_supported_types(self) -> List[str]:
        return ["ClassificationResponse"]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version


class SummarizationProcessor(IDocumentProcessor):
    """
    Summarization processor for generating natural language summaries from entities.
    
    This processor:
    1. Takes extracted entities from the extraction step
    2. Loads entity data from label.json files (evaluations/notebooks/data/label.json format)
    3. Uses SummarizationService to generate natural language summaries
    4. Saves summary results for downstream use
    
    Input: extraction results with entity data
    Output: generated summaries with metadata
    """
    
    def __init__(self):
        self._name = "summarizer"
        self._version = "1.0.0"
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summaries from extracted entities.
        
        Args:
            inputs: Dict containing 'extracted_entities' from extraction step
            
        Returns:
            Dict with 'summaries' containing generated summaries
        """
        import os
        from dotenv import load_dotenv
        from azure.identity import DefaultAzureCredential
        
        logger.info("#" * 60)
        logger.info("STEP 5: SUMMARIZATION - INPUT RECEIVED")
        logger.info("#" * 60)
        logger.info(f"Input keys: {list(inputs.keys())}")
        
        # Log extracted_entities
        extracted_entities = inputs.get('extracted_entities', [])
        logger.info(f"  - extracted_entities: [{len(extracted_entities)} items]")
        for idx, ee in enumerate(extracted_entities[:3]):
            logger.info(f"      [{idx+1}] status={ee.get('status')}, doc_type={ee.get('document_type')}")
        if len(extracted_entities) > 3:
            logger.info(f"      ... and {len(extracted_entities) - 3} more")
        logger.info("-" * 60)
        
        # Process each extraction result
        summaries = []
        
        for idx, extraction_data in enumerate(extracted_entities):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing extraction result [{idx+1}/{len(extracted_entities)}]")
            logger.info(f"{'='*60}")
            
            # Log extraction data details
            document_type = extraction_data.get("document_type")
            file_path = extraction_data.get("file_path")
            status = extraction_data.get("status")
            
            logger.info(f"  Document Type: {document_type}")
            logger.info(f"  File Path: {file_path}")
            logger.info(f"  Extraction Status: {status}")
            
            # Skip if extraction was not successful
            if status != "success":
                logger.warning(f"  ⚠ Skipping summarization - extraction status: {status}")
                if extraction_data.get("reason"):
                    logger.info(f"  Reason: {extraction_data.get('reason')}")
                if extraction_data.get("error"):
                    logger.error(f"  Error: {extraction_data.get('error')}")
                
                summaries.append({
                    "document_type": document_type,
                    "file_path": file_path,
                    "summary": None,
                    "status": "skipped",
                    "reason": f"Extraction status was {status}"
                })
                continue
            
            extraction_result = extraction_data.get("extraction_result", {})
            
            # Log extraction result structure
            logger.info(f"  Extraction Result Keys: {list(extraction_result.keys())}")
            logger.info(f"  Extraction Result Type: {type(extraction_result)}")
            
            # Check for entities
            if "entities" in extraction_result:
                entities = extraction_result.get("entities", [])
                logger.info(f"  Found 'entities' key with {len(entities)} items")
                if entities:
                    logger.info(f"  First entity sample: {entities[0]}")
            else:
                logger.info(f"  No 'entities' key found in extraction_result")
                # Log a sample of the extraction result structure
                logger.info(f"  Extraction result sample: {str(extraction_result)[:200]}...")
            
            logger.info(f"\n  Starting summarization for {document_type}...")
            
            try:
                # Generate summary from extraction result
                summary_result = self._generate_summary(
                    extraction_result=extraction_result,
                    document_type=document_type,
                    file_path=file_path
                )
                
                # Log summary result details
                success = summary_result.get("success")
                error_msg = summary_result.get("error_message")
                summary_text = summary_result.get("summary", "")
                entities_used = summary_result.get("entities_used", {})
                
                logger.info(f"  Summary Result:")
                logger.info(f"    Success: {success}")
                logger.info(f"    Summary Length: {len(summary_text)} chars")
                if error_msg:
                    logger.error(f"    Error Message: {error_msg}")
                if summary_text:
                    logger.info(f"    Summary Preview: {summary_text[:100]}...")
                
                # Run summarization evaluation if summary was generated successfully
                evaluation_result = None
                if success and summary_text and entities_used:
                    logger.info(f"\n  Running summarization evaluation for {document_type}...")
                    logger.info(f"    Entities used for evaluation ({len(entities_used)}):")
                    for entity_name, entity_value in entities_used.items():
                        logger.info(f"      - {entity_name}: {entity_value}")
                    
                    evaluation_result = self._evaluate_summary(
                        summary=summary_text,
                        entities=entities_used,
                        document_type=document_type
                    )
                    
                    if evaluation_result and evaluation_result.get("success"):
                        logger.info(f"  ✓ Summarization evaluation completed:")
                        logger.info(f"    Overall Score: {evaluation_result.get('overall_score', 0):.3f}")
                        logger.info(f"    Final Composite Score: {evaluation_result.get('final_composite_score', 0):.3f}")
                        for eval_name, eval_data in evaluation_result.get("evaluations", {}).items():
                            logger.info(f"    {eval_name}: {eval_data.get('score', 0):.3f}")
                    else:
                        logger.warning(f"  ⚠ Summarization evaluation failed or skipped")
                
                summaries.append({
                    "document_type": document_type,
                    "file_path": file_path,
                    "summary": summary_text,
                    "metadata": summary_result.get("metadata"),
                    "status": "success" if success else "failed",
                    "error_message": error_msg,
                    "evaluation": evaluation_result  # Add evaluation results
                })
                
                if success:
                    logger.info(f"  ✓ Summary generated successfully for {document_type}")
                else:
                    logger.error(f"  ✗ Summary generation failed for {document_type}")
                
            except Exception as e:
                logger.error(f"  ✗ Exception during summarization for {document_type}: {e}")
                import traceback
                logger.error(f"  Traceback: {traceback.format_exc()}")
                
                summaries.append({
                    "document_type": document_type,
                    "file_path": file_path,
                    "summary": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        successful = sum(1 for s in summaries if s["status"] == "success")
        logger.info("-" * 50)
        logger.info(f"SUMMARIZATION COMPLETE: {successful} summaries generated, {len(summaries) - successful} failed/skipped")
        logger.info("=" * 50)
        
        return {
            "summaries": summaries,
            "summarization_status": "success" if successful > 0 else "failed",
            "extracted_entities": extracted_entities,  # Pass through
            "classification_response": inputs.get("classification_response")  # Pass through
        }
    
    def _generate_summary(
        self,
        extraction_result: Dict[str, Any],
        document_type: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Generate a summary from extraction results using SummarizationService.
        
        Args:
            extraction_result: The extraction result containing entities
            document_type: Type of document being summarized
            file_path: Path to the original file
            
        Returns:
            Dictionary with summary, success status, and metadata
        """
        import os
        from dotenv import load_dotenv
        from azure.identity import DefaultAzureCredential
        
        try:
            # Import summarization service
            from src.document_summarization.summarization_service import SummarizationService
            from src.document_summarization.utils.entity_loader import EntityLoader
            
            logger.info(f"    [_generate_summary] Starting for document_type: {document_type}")
            
            # Load environment variables
            load_dotenv()
            
            # Get Azure OpenAI configuration (simplified - similar to EXTRACTION_DOC_INTELLIGENCE_ENDPOINT)
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-198589")  # Default: actual deployment
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")  # Default: latest API version
            
            logger.info(f"    [_generate_summary] Azure OpenAI Config:")
            logger.info(f"      Endpoint: {azure_endpoint[:50]}..." if azure_endpoint else "      Endpoint: None")
            logger.info(f"      Deployment: {deployment_name}")
            logger.info(f"      API Version: {api_version}")
            
            if not azure_endpoint:
                logger.error("    [_generate_summary] ✗ Azure OpenAI endpoint missing!")
                logger.error(f"      Required: AZURE_OPENAI_ENDPOINT environment variable")
                logger.error(f"      Example: AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com")
                return {
                    "summary": "",
                    "success": False,
                    "error_message": "Azure OpenAI endpoint not configured. Set AZURE_OPENAI_ENDPOINT environment variable.",
                    "metadata": {}
                }
            
            # Initialize SummarizationService
            logger.info(f"    [_generate_summary] Initializing SummarizationService...")
            service = SummarizationService(
                azure_endpoint=azure_endpoint,
                deployment_name=deployment_name,
                api_version=api_version,
                credential=DefaultAzureCredential(),
                temperature=0.0,
                max_tokens=5000
            )
            logger.info(f"    [_generate_summary] ✓ SummarizationService initialized")
            
            # Extract entities from the extraction result
            # The extraction result may have different formats, handle both
            entities = {}
            
            logger.info(f"    [_generate_summary] Extracting entities from extraction_result")
            logger.info(f"      extraction_result type: {type(extraction_result)}")
            
            # Check if extraction_result has an 'entities' key with list format
            if "entities" in extraction_result and isinstance(extraction_result["entities"], list):
                logger.info(f"      Found 'entities' key (list format) with {len(extraction_result['entities'])} items")
                # Convert list of entity objects to dict
                for idx, entity in enumerate(extraction_result["entities"]):
                    if isinstance(entity, dict):
                        entity_type = entity.get("type") or entity.get("entity_type") or entity.get("name")
                        entity_value = entity.get("value") or entity.get("entity_value")
                        logger.debug(f"        Entity [{idx}]: type={entity_type}, value={entity_value}")
                        if entity_type and entity_value:
                            entities[entity_type] = entity_value
                logger.info(f"      Converted {len(entities)} entities from list to dict")
            
            # Check if extraction_result itself is a dict of entities
            elif isinstance(extraction_result, dict):
                logger.info(f"      extraction_result is dict, checking for entity mappings")
                logger.info(f"      Keys in extraction_result: {list(extraction_result.keys())}")
                # Try to find entity mappings in the result
                excluded_keys = ["status", "metadata", "document_type", "confidence", "analyzer_id", 
                                 "fields", "needs_review", "models_used", "processing_time_ms", 
                                 "error_message", "extraction_id", "extraction_completed_at"]
                
                for key, value in extraction_result.items():
                    if key not in excluded_keys:
                        if isinstance(value, (str, int, float, bool)):
                            entities[key] = str(value)
                            logger.debug(f"        Added entity: {key} = {value}")
                
                # Also check if there's a 'fields' key (common in extraction results)
                if "fields" in extraction_result and isinstance(extraction_result["fields"], list):
                    logger.info(f"      Found 'fields' key with {len(extraction_result['fields'])} items")
                    for field in extraction_result["fields"]:
                        if isinstance(field, dict):
                            field_name = field.get("name") or field.get("field_name")
                            field_value = field.get("value") or field.get("field_value")
                            if field_name and field_value:
                                entities[field_name] = field_value
                                logger.debug(f"        Added field: {field_name} = {field_value}")
                    logger.info(f"      Extracted {len(entities)} entities from 'fields'")
            
            logger.info(f"    [_generate_summary] Entity extraction complete:")
            logger.info(f"      Total entities extracted: {len(entities)}")
            if entities:
                logger.info(f"      Entity keys: {list(entities.keys())}")
                # Log first few entities
                for key, value in list(entities.items())[:5]:
                    logger.info(f"        {key}: {str(value)[:50]}...")
            else:
                logger.warning(f"      ⚠ NO ENTITIES EXTRACTED!")
            
            if not entities:
                logger.error("    [_generate_summary] ✗ No entities found in extraction result")
                return {
                    "summary": "",
                    "success": False,
                    "error_message": "No entities found in extraction result",
                    "metadata": {"entity_count": 0}
                }
            
            # Generate summary
            logger.info(f"    [_generate_summary] Calling service.generate_summary()...")
            result = service.generate_summary(
                entities=entities,
                context=f"{document_type}"
            )
            
            logger.info(f"    [_generate_summary] Summary generation result:")
            logger.info(f"      Success: {result.get('success')}")
            logger.info(f"      Summary length: {len(result.get('summary', ''))} chars")
            if result.get('error_message'):
                logger.error(f"      Error: {result.get('error_message')}")
            
            # Add entities used to result for evaluation
            result["entities_used"] = entities
            
            return result
            
        except ImportError as e:
            logger.error(f"    [_generate_summary] ✗ Import error: {e}")
            import traceback
            logger.error(f"      Traceback: {traceback.format_exc()}")
            return {
                "summary": "",
                "success": False,
                "error_message": f"Import error: {str(e)}",
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"    [_generate_summary] ✗ Unexpected error: {e}")
            import traceback
            logger.error(f"      Traceback: {traceback.format_exc()}")
            return {
                "summary": "",
                "success": False,
                "error_message": str(e),
                "metadata": {}
            }
    
    def _evaluate_summary(
        self,
        summary: str,
        entities: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of a generated summary using the SummaryEvaluationService.
        
        Args:
            summary: The generated summary text
            entities: Dictionary of entities used to generate the summary
            document_type: Type of document for context
            
        Returns:
            Dictionary with evaluation results including scores and feedback
        """
        try:
            logger.info(f"    [_evaluate_summary] Starting evaluation for {document_type}")
            logger.info(f"      Summary length: {len(summary)} chars")
            logger.info(f"      Summary text: {summary}")
            logger.info(f"      Entities count: {len(entities)}")
            logger.info(f"      Entities details:")
            for entity_name, entity_value in entities.items():
                logger.info(f"        - {entity_name}: {entity_value}")
            
            # Import evaluation components
            from src.evaluation.document_summarization import SummaryEvaluationService
            from src.evaluation.document_summarization.evaluators import (
                EntityCoverageEvaluator,
                GroundednessEvaluator,
                SemanticFidelityEvaluator
            )
            
            # Initialize evaluation service
            service = SummaryEvaluationService()
            
            # Create and register evaluators
            ecs_evaluator = EntityCoverageEvaluator()
            gs_evaluator = GroundednessEvaluator()
            sef_evaluator = SemanticFidelityEvaluator()
            
            service.register_evaluator(ecs_evaluator)
            service.register_evaluator(gs_evaluator)
            service.register_evaluator(sef_evaluator)
            
            logger.info(f"      Registered evaluators: {service.get_registered_evaluators()}")
            
            # Convert entities to string values if needed
            entities_str = {}
            for key, value in entities.items():
                entities_str[key] = str(value) if value is not None else ""
            
            logger.info(f"      Running evaluators...")
            
            # Run evaluation
            result = service.evaluate(
                summary=summary,
                entities=entities_str,
                context=document_type,
                evaluators=["all"]
            )
            
            if result.get("success"):
                # Calculate weighted composite score
                evaluations = result.get("evaluations", {})
                ecs_score = evaluations.get("entity_coverage", {}).get("score", 0)
                gs_score = evaluations.get("groundedness", {}).get("score", 0)
                sef_score = evaluations.get("semantic_fidelity", {}).get("score", 0)
                
                # Get feedback from each evaluator
                ecs_feedback = evaluations.get("entity_coverage", {}).get("feedback", "")
                gs_feedback = evaluations.get("groundedness", {}).get("feedback", "")
                sef_feedback = evaluations.get("semantic_fidelity", {}).get("feedback", "")
                
                # Get metadata from evaluators for detailed logging
                ecs_metadata = evaluations.get("entity_coverage", {}).get("metadata", {})
                gs_metadata = evaluations.get("groundedness", {}).get("metadata", {})
                sef_metadata = evaluations.get("semantic_fidelity", {}).get("metadata", {})
                
                # Weighted combination: ECS 40%, GS 30%, SEF 30%
                final_score = (
                    0.40 * ecs_score +
                    0.30 * gs_score +
                    0.30 * sef_score
                )
                
                result["final_composite_score"] = final_score
                result["weights"] = {
                    "entity_coverage": 0.40,
                    "groundedness": 0.30,
                    "semantic_fidelity": 0.30
                }
                
                logger.info(f"    [_evaluate_summary] ✓ Evaluation completed:")
                logger.info(f"      ┌─────────────────────────────────────────────────────")
                logger.info(f"      │ Entity Coverage: {ecs_score:.3f} (weight: 40%)")
                logger.info(f"      │   Feedback: {ecs_feedback}")
                if ecs_metadata.get("covered_entities"):
                    logger.info(f"      │   Covered: {ecs_metadata.get('covered_entities')}")
                if ecs_metadata.get("missing_entities"):
                    logger.info(f"      │   Missing: {ecs_metadata.get('missing_entities')}")
                logger.info(f"      ├─────────────────────────────────────────────────────")
                logger.info(f"      │ Groundedness: {gs_score:.3f} (weight: 30%)")
                logger.info(f"      │   Feedback: {gs_feedback}")
                if gs_metadata.get("entity_scores"):
                    for entity, score in gs_metadata.get("entity_scores", {}).items():
                        logger.info(f"      │     {entity}: {score:.3f}")
                logger.info(f"      ├─────────────────────────────────────────────────────")
                logger.info(f"      │ Semantic Fidelity: {sef_score:.3f} (weight: 30%)")
                logger.info(f"      │   Feedback: {sef_feedback}")
                if sef_metadata.get("entity_similarity_scores"):
                    for entity, score in sef_metadata.get("entity_similarity_scores", {}).items():
                        logger.info(f"      │     {entity}: {score:.3f}")
                logger.info(f"      └─────────────────────────────────────────────────────")
                logger.info(f"      Final Composite Score: {final_score:.3f}")
            else:
                logger.warning(f"    [_evaluate_summary] ⚠ Evaluation failed: {result.get('error_message')}")
            
            return result
            
        except ImportError as e:
            logger.error(f"    [_evaluate_summary] ✗ Import error: {e}")
            return {
                "success": False,
                "error_message": f"Import error: {str(e)}",
                "overall_score": 0.0,
                "evaluations": {}
            }
        except Exception as e:
            logger.error(f"    [_evaluate_summary] ✗ Unexpected error: {e}")
            import traceback
            logger.error(f"      Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error_message": str(e),
                "overall_score": 0.0,
                "evaluations": {}
            }
    
    def validate_input(self, document: Dict[str, Any]) -> bool:
        """Validate that input has extracted entities."""
        return bool(document.get("extracted_entities"))
    
    def get_supported_types(self) -> List[str]:
        """Get supported input types."""
        return ["ExtractionResult"]
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version


# =============================================================================
# Workflow Manager
# =============================================================================

class CaseWorkflowManager:
    """
    Manages case processing workflows.
    
    Provides:
    - Config-driven workflow definition
    - Processor registration
    - Workflow execution with error handling (sync and async)
    - Support for adding/removing steps dynamically
    
    Design Note:
    - Workflow processors are synchronous for simplicity
    - Database operations are handled by the calling service (case_service.py)
      which has proper async context and dependency injection
    """
    
    def __init__(self):
        self._workflows: Dict[str, WorkflowConfig] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize and register all processors."""
        if self._initialized:
            return
        
        # Register processors
        self._register_default_processors()
        self._initialized = True
        logger.info("CaseWorkflowManager: Initialized with default processors")
    
    def _register_default_processors(self):
        """Register default processors in the registry."""
        processors = {
            "classifier": ClassifierProcessor(),
            "file_upload": FileUploadProcessor(),
            "db_update": DatabaseUpdateProcessor(),
            "extractor": ExtractionProcessor(),
            "summarizer": SummarizationProcessor(),
        }
        
        for name, processor in processors.items():
            if not registry.has_component(name):
                registry.register(name, processor)
                logger.info(f"CaseWorkflowManager: Registered processor '{name}'")
    
    def register_processor(self, name: str, processor: IDocumentProcessor):
        """Register a custom processor."""
        if registry.has_component(name):
            registry.unregister(name)
        registry.register(name, processor)
        logger.info(f"CaseWorkflowManager: Registered custom processor '{name}'")
    
    def load_workflow_config(self, config: WorkflowConfig):
        """Load a workflow configuration."""
        self._workflows[config.name] = config
        self._build_workflow(config)
        logger.info(f"CaseWorkflowManager: Loaded workflow '{config.name}' v{config.version}")
    
    def load_workflow_from_yaml(self, yaml_path: str):
        """Load workflow configuration from YAML file."""
        config = WorkflowConfig.from_yaml(yaml_path)
        self.load_workflow_config(config)
    
    def load_workflow_from_dict(self, data: Dict[str, Any]):
        """Load workflow configuration from dictionary."""
        config = WorkflowConfig.from_dict(data)
        self.load_workflow_config(config)
    
    def _build_workflow(self, config: WorkflowConfig):
        """Build workflow from configuration."""
        builder = PipelineBuilder(config.name)
        
        enabled_steps = []
        for step in config.steps:
            if not step.enabled:
                logger.info(f"CaseWorkflowManager: Skipping disabled step '{step.name}'")
                continue
            
            enabled_steps.append(step.name)
            builder.add_step(
                step_name=step.name,
                component=step.component,
                inputs=step.inputs,
                outputs=step.outputs,
                skip_on_error=step.skip_on_error
            )
        
        builder.build(orchestrator)
        logger.info(f"CaseWorkflowManager: Built workflow '{config.name}' with {len(enabled_steps)} steps: {enabled_steps}")
    
    def execute_workflow(
        self, 
        workflow_name: str, 
        inputs: Dict[str, Any],
        human_review_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow synchronously.
        
        Args:
            workflow_name: Name of the workflow to execute
            inputs: Initial input data (e.g., document path, case_id)
            human_review_callback: Optional callback for human-in-the-loop
            
        Returns:
            Workflow execution results including prepared_documents for DB insertion
        """
        self.initialize()
        
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")
        
        logger.info(f"CaseWorkflowManager: Executing workflow '{workflow_name}'")
        
        try:
            results = orchestrator.execute(
                workflow_name, 
                inputs, 
                human_review_callback=human_review_callback
            )
            
            status = orchestrator.get_status()
            logger.info(f"CaseWorkflowManager: Workflow '{workflow_name}' completed with status: {status}")
            
            return {
                "status": status.value,
                "results": results
            }
        except Exception as e:
            logger.error(f"CaseWorkflowManager: Workflow '{workflow_name}' failed: {e}")
            raise
    
    async def execute_workflow_async(
        self, 
        workflow_name: str, 
        inputs: Dict[str, Any],
        human_review_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow asynchronously.
        
        Runs the synchronous workflow in a thread pool to avoid blocking
        the async event loop. Use this when calling from async context
        (e.g., FastAPI endpoints).
        
        Args:
            workflow_name: Name of the workflow to execute
            inputs: Initial input data (e.g., document path, case_id)
            human_review_callback: Optional callback for human-in-the-loop
            
        Returns:
            Workflow execution results including prepared_documents for DB insertion
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Use default executor (ThreadPoolExecutor)
            lambda: self.execute_workflow(workflow_name, inputs, human_review_callback)
        )
    
    def get_workflow_status(self) -> WorkflowStatus:
        """Get current workflow status."""
        return orchestrator.get_status()
    
    def list_workflows(self) -> List[str]:
        """List available workflows."""
        return list(self._workflows.keys())


# =============================================================================
# Default Workflow Configuration
# =============================================================================

DEFAULT_CASE_WORKFLOW_CONFIG = {
    "name": "case_processing",
    "version": "2.1.0",  # Version bump for summarization step addition
    "description": "Default case processing workflow: classification → file upload → DB prepare → extraction → summarization. DB insertion handled by case_service.py.",
    "steps": [
        {
            "name": "classification",
            "type": "classification",
            "component": "classifier",
            "inputs": {"document": None},
            "outputs": ["classification_response", "documents", "pages"],
            "enabled": True,
            "skip_on_error": False
        },
        {
            "name": "file_upload",
            "type": "file_upload",
            "component": "file_upload",
            "inputs": {"classification_response": None, "documents": None, "case_id": None},
            "outputs": ["uploaded_files"],
            "enabled": True,
            "skip_on_error": False
        },
        {
            "name": "db_update",
            "type": "db_update",
            "component": "db_update",
            "inputs": {"uploaded_files": None, "classification_response": None, "case_id": None, "pages": None},
            "outputs": ["prepared_documents", "db_update_status", "documents"],
            "enabled": True,
            "skip_on_error": False
        },
        {
            "name": "extraction",
            "type": "extraction",
            "component": "extractor",
            "inputs": {"classification_response": None, "documents": None},
            "outputs": ["extracted_entities"],
            "enabled": True,
            "skip_on_error": False
        },
        {
            "name": "summarization",
            "type": "summarization",
            "component": "summarizer",
            "inputs": {"extracted_entities": None, "classification_response": None},
            "outputs": ["summaries", "summarization_status"],
            "enabled": True,
            "skip_on_error": True  # Continue workflow even if summarization fails
        }
    ],
    "metadata": {
        "created_by": "contoso_case_workflow",
        "purpose": "insurance_underwriting",
        "notes": "DB operations handled by case_service.py for proper async context. Summarization generates natural language summaries from extracted entities."
    }
}


# =============================================================================
# Convenience Functions
# =============================================================================

# Global workflow manager instance
workflow_manager = CaseWorkflowManager()


def initialize_case_workflow():
    """Initialize the case workflow with default configuration."""
    workflow_manager.initialize()
    workflow_manager.load_workflow_from_dict(DEFAULT_CASE_WORKFLOW_CONFIG)
    logger.info("Case workflow initialized with default configuration")


def on_new_case_created(
    document_path: str, 
    case_id: Optional[str] = None,
    blob_path: Optional[str] = None,
    human_review_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Trigger workflow when a new case is created (synchronous version).
    
    Args:
        document_path: Path to the local document file (for classification)
        case_id: Optional case identifier
        blob_path: Optional blob storage path (for reference in subsequent steps)
        human_review_callback: Optional callback for human review
        
    Returns:
        Workflow execution results with classification, uploads, prepared_documents, and extraction
        NOTE: prepared_documents should be persisted by the calling service (case_service.py)
    """
    # Ensure workflow is initialized
    if "case_processing" not in workflow_manager.list_workflows():
        initialize_case_workflow()
    
    # Prepare inputs - use local path for classification
    inputs = {
        "document": {"path": document_path},
        "case_id": case_id,
        "blob_path": blob_path,  # Store blob path for reference
    }
    
    # Execute workflow
    results = workflow_manager.execute_workflow(
        "case_processing", 
        inputs,
        human_review_callback=human_review_callback
    )
    
    logger.info(f"Case workflow completed for case_id={case_id}, document={document_path}")
    return results


async def on_new_case_created_async(
    document_path: str, 
    case_id: Optional[str] = None,
    blob_path: Optional[str] = None,
    human_review_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Trigger workflow when a new case is created (async version).
    
    Use this when calling from async context (e.g., FastAPI endpoints).
    
    Args:
        document_path: Path to the local document file (for classification)
        case_id: Optional case identifier
        blob_path: Optional blob storage path (for reference in subsequent steps)
        human_review_callback: Optional callback for human review
        
    Returns:
        Workflow execution results with classification, uploads, prepared_documents, and extraction
        NOTE: prepared_documents should be persisted by the calling service (case_service.py)
    """
    # Ensure workflow is initialized
    if "case_processing" not in workflow_manager.list_workflows():
        initialize_case_workflow()
    
    # Prepare inputs - use local path for classification
    inputs = {
        "document": {"path": document_path},
        "case_id": case_id,
        "blob_path": blob_path,  # Store blob path for reference
    }
    
    # Execute workflow asynchronously
    results = await workflow_manager.execute_workflow_async(
        "case_processing", 
        inputs,
        human_review_callback=human_review_callback
    )
    
    logger.info(f"Case workflow (async) completed for case_id={case_id}, document={document_path}")
    return results


def create_custom_workflow(config: Dict[str, Any]) -> str:
    """
    Create a custom workflow from configuration.
    
    Args:
        config: Workflow configuration dictionary
        
    Returns:
        Workflow name
    """
    workflow_manager.initialize()
    workflow_manager.load_workflow_from_dict(config)
    return config["name"]
