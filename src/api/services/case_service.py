"""
Case business logic service.

Handles case operations including validation, state transitions, and CRUD operations.
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Any, Optional

from src.api.middleware.error_handler import BadRequestError, ConflictError, NotFoundError

# Import workflow orchestration
from src.orchestration.case_workflow import (
    workflow_manager,
    initialize_case_workflow,
    on_new_case_created as trigger_case_workflow,
    on_new_case_created_async as trigger_case_workflow_async,
)
from src.api.models.case import (
    CaseDetailResponse,
    CaseListResponse,
    CaseSummaryResponse,
    CaseUpdateRequest,
    DocumentSummaryInCase,
    StatusHistoryEntry,
    StatusHistoryResponse,
)
from src.api.models.enums import CaseStatus, validate_status_transition
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.counter_repository import CounterRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.services.storage_service import StorageService

# Import TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)


class CaseService:
    """Service for case management operations."""

    def __init__(
        self,
        case_repository: CaseRepository,
        document_repository: DocumentRepository,
        counter_repository: CounterRepository,
        storage_service: Optional[StorageService] = None,
        classification_service: Optional["ClassificationService"] = None,
    ) -> None:
        """
        Initialize case service with repositories.

        Args:
            case_repository: Repository for case data access
            document_repository: Repository for document data access
            counter_repository: Repository for ID generation
            storage_service: Service for blob storage operations
            classification_service: Service for document classification
        """
        self.case_repo = case_repository
        self.document_repo = document_repository
        self.counter_repo = counter_repository
        self.storage_service = storage_service
        self.classification_service = classification_service

    async def create_case(
        self,
        client_name: str,
        policy_type: str,
        metadata: dict[str, Any],
        user_id: str,
        main_document_content: Optional[bytes] = None,
        main_document_filename: Optional[str] = None,
        main_document_content_type: Optional[str] = None,
    ) -> CaseDetailResponse:
        """
        Create a new case with optional main document upload.

        Args:
            client_name: Name of the client
            policy_type: Type of insurance policy
            metadata: Additional case metadata
            user_id: ID of the user creating the case
            main_document_content: Optional file content of the main document
            main_document_filename: Optional filename of the main document
            main_document_content_type: Optional MIME type of the main document

        Returns:
            Created case details
        """
        # Generate unique case ID
        case_id = await self.counter_repo.get_next_case_id()
        logger.info(f"Creating new case with ID: {case_id}")

        # Upload main document to blob storage if provided
        main_document_blob_path: Optional[str] = None
        if main_document_content and main_document_filename and self.storage_service:
            blob_path = f"{case_id}/main/{main_document_filename}"
            await self.storage_service.upload_blob(
                blob_path=blob_path,
                content=main_document_content,
                content_type=main_document_content_type or "application/octet-stream",
            )
            main_document_blob_path = blob_path
            logger.info(f"Main document uploaded to {blob_path}")

        now = datetime.now(timezone.utc)
        case_data = {
            "id": case_id,
            "case_id": case_id,
            "client_name": client_name,
            "policy_type": policy_type,
            "submission_date": now.date().isoformat(),  # Auto-generated submission date
            "status": CaseStatus.DRAFT.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": user_id,
            "metadata": metadata,
            "main_document_blob_path": main_document_blob_path,
            # Processing tracking fields
            "processing_status": "not_started",
            "total_documents_expected": None,
            "documents_processed_count": 0,
            "processing_started_at": None,
            "processing_completed_at": None,
            "processing_error": None,
            "case_summary": None,
            "case_summary_updated_at": None,
            "is_deleted": False,
            "deleted_at": None,
            "deleted_by": None,
            "status_history": [
                {
                    "previous_status": None,
                    "new_status": CaseStatus.DRAFT.value,
                    "changed_by": user_id,
                    "changed_at": now.isoformat(),
                    "reason": "Case created",
                }
            ],
        }

        created = await self.case_repo.create_case(case_data)
        logger.info(f"Case {case_id} created successfully")

        # Trigger workflow orchestration if a main document was uploaded
        if main_document_blob_path and main_document_content:
            local_temp_path = None
            workflow_started_at = datetime.now(timezone.utc)
            
            # Update case with processing_started_at
            await self.case_repo.update_case(
                case_id,
                {"processing_started_at": workflow_started_at.isoformat(), "processing_status": "processing"},
                user_id=user_id,
            )
            
            try:
                logger.info(f"Starting workflow orchestration for case {case_id}")
                
                # Save document content to a local temp file for classification
                # This avoids modifying the document_classifier to handle blob storage
                ext = Path(main_document_filename).suffix if main_document_filename else ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(main_document_content)
                    local_temp_path = temp_file.name
                
                logger.info(f"Saved document to temp file: {local_temp_path} ({len(main_document_content)} bytes)")
                
                # Initialize workflow if not already done
                initialize_case_workflow()
                
                # Trigger the case processing workflow with LOCAL file path
                # This will run: classification → file upload → DB prepare → extraction
                # Note: Using async version to avoid blocking the event loop
                workflow_result = await trigger_case_workflow_async(
                    document_path=local_temp_path,  # Pass local file, not blob path
                    case_id=case_id,
                    blob_path=main_document_blob_path,  # Pass blob path separately for reference
                )
                
                logger.info(
                    f"Workflow completed for case {case_id} with status: {workflow_result.get('status')}"
                )
                
                # Update case with workflow results
                step_results = workflow_result.get('results', {})
                
                # ========== DETAILED LOGGING FOR CLASSIFICATION RESULTS ==========
                classification_result = step_results.get('classification', {})
                classification_response = classification_result.get('classification_response')
                documents = classification_result.get('documents', [])
                pages = classification_result.get('pages', [])
                
                logger.info("=" * 60)
                logger.info(f"CLASSIFICATION RESULTS FOR CASE {case_id}")
                logger.info("=" * 60)
                logger.info(f"Total subdocuments identified: {len(documents)}")
                logger.info(f"Total pages classified: {len(pages) if pages else 0}")
                
                # Log each subdocument from classifier
                for idx, doc in enumerate(documents or []):
                    doc_type = doc.document_type if hasattr(doc, 'document_type') else doc.get('document_type', 'unknown')
                    file_path = doc.file_path if hasattr(doc, 'file_path') else doc.get('file_path', 'unknown')
                    logger.info(f"  Subdocument [{idx + 1}]: type={doc_type}, path={file_path}")
                
                # ========== DETAILED LOGGING FOR FILE UPLOAD RESULTS ==========
                file_upload_result = step_results.get('file_upload', {})
                uploaded_files = file_upload_result.get('uploaded_files', [])
                upload_status = file_upload_result.get('upload_status', 'unknown')
                
                logger.info("-" * 60)
                logger.info(f"FILE UPLOAD PREPARED (from workflow)")
                logger.info("-" * 60)
                logger.info(f"Upload status: {upload_status}")
                logger.info(f"Total files prepared for upload: {len(uploaded_files)}")
                
                for idx, uploaded in enumerate(uploaded_files):
                    logger.info(f"  Prepared [{idx + 1}]:")
                    logger.info(f"    - Document Type: {uploaded.get('document_type')}")
                    logger.info(f"    - Original Path: {uploaded.get('original_path')}")
                    logger.info(f"    - Target Blob Path: {uploaded.get('blob_path')}")
                    logger.info(f"    - Status: {uploaded.get('upload_status')}")
                
                # ========== UPLOAD SUB-DOCUMENTS TO BLOB STORAGE ==========
                # The workflow prepares blob paths; we do actual upload here with StorageService
                if self.storage_service and uploaded_files:
                    logger.info("-" * 60)
                    logger.info("UPLOADING SUB-DOCUMENTS TO BLOB STORAGE")
                    logger.info("-" * 60)
                    
                    for idx, uploaded in enumerate(uploaded_files):
                        original_path = uploaded.get("original_path")
                        blob_path = uploaded.get("blob_path")
                        doc_type = uploaded.get("document_type")
                        
                        try:
                            # Read the local file content
                            with open(original_path, "rb") as f:
                                file_content = f.read()
                            
                            # Upload to blob storage
                            await self.storage_service.upload_blob(
                                blob_path=blob_path,
                                content=file_content,
                                content_type="application/pdf",
                            )
                            
                            # Update status in our tracking
                            uploaded["upload_status"] = "success"
                            uploaded["size_bytes"] = len(file_content)
                            logger.info(f"  ✓ Uploaded [{idx + 1}]: {doc_type} -> {blob_path} ({len(file_content)} bytes)")
                            
                        except FileNotFoundError:
                            uploaded["upload_status"] = "failed"
                            uploaded["error"] = f"File not found: {original_path}"
                            logger.error(f"  ✗ Failed [{idx + 1}]: File not found: {original_path}")
                        except Exception as upload_err:
                            uploaded["upload_status"] = "failed"
                            uploaded["error"] = str(upload_err)
                            logger.error(f"  ✗ Failed [{idx + 1}]: {upload_err}")
                    
                    successful_uploads = sum(1 for u in uploaded_files if u.get("upload_status") == "success")
                    logger.info(f"Blob upload complete: {successful_uploads}/{len(uploaded_files)} files uploaded")
                    logger.info("-" * 60)
                else:
                    if not self.storage_service:
                        logger.warning("StorageService not available - skipping blob upload")
                    if not uploaded_files:
                        logger.info("No files to upload to blob storage")
                
                # ========== DETAILED LOGGING FOR PREPARED DOCUMENTS ==========
                # (Note: Workflow now prepares document data; actual DB insert happens below)
                db_update_result = step_results.get('db_update', {})
                prepared_documents = db_update_result.get('prepared_documents', [])
                db_update_status = db_update_result.get('db_update_status', 'unknown')
                
                logger.info("-" * 60)
                logger.info(f"PREPARED DOCUMENT RECORDS (from workflow)")
                logger.info("-" * 60)
                logger.info(f"DB update status: {db_update_status}")
                logger.info(f"Total documents prepared: {len(prepared_documents)}")
                
                for idx, record in enumerate(prepared_documents):
                    logger.info(f"  Prepared Document [{idx + 1}]:")
                    logger.info(f"    - Document Type: {record.get('document_type')}")
                    logger.info(f"    - Blob Path: {record.get('blob_path')}")
                    logger.info(f"    - Filename: {record.get('filename')}")
                    logger.info(f"    - Page Count: {record.get('page_count')}")
                    logger.info(f"    - Confidence: {record.get('classification_confidence')}")
                
                # ========== EXTRACTION RESULTS ==========
                extraction_result = step_results.get('extraction', {})
                extracted_entities = extraction_result.get('extracted_entities', [])
                
                logger.info("-" * 60)
                logger.info(f"EXTRACTION RESULTS")
                logger.info("-" * 60)
                logger.info(f"Total entity sets extracted: {len(extracted_entities)}")
                
                # Build extraction lookup by document_type for later embedding
                extraction_by_doc_type: dict[str, dict] = {}
                for entity_set in extracted_entities:
                    doc_type = entity_set.get('document_type')
                    status = entity_set.get('status', 'unknown')
                    extraction_data = entity_set.get('extraction_result', {})
                    
                    logger.info(f"  Entity Set [{doc_type}]: status={status}")
                    if extraction_data:
                        fields = extraction_data.get('fields', [])
                        logger.info(f"    - fields: {len(fields)}")
                        logger.info(f"    - needs_review: {extraction_data.get('needs_review', False)}")
                        logger.info(f"    - models_used: {extraction_data.get('models_used', [])}")
                        logger.info(f"    - processing_time_ms: {extraction_data.get('processing_time_ms', 0)}")
                    else:
                        logger.info(f"    - No extraction data (skipped or error)")
                    
                    # Store for embedding in document record
                    extraction_by_doc_type[doc_type] = {
                        "status": status,
                        "data": extraction_data if status == "success" else None,
                        "error": entity_set.get('error'),
                        "reason": entity_set.get('reason')
                    }
                
                logger.info("=" * 60)
            
                documents_count = len(documents)
                
                # ========== CREATE DOCUMENT RECORDS IN COSMOS DB ==========
                # The workflow's db_update step prepares document data but doesn't insert.
                # We create documents here in the proper async context using the prepared data
                # or directly from uploaded_files/pages (which have same info).
                logger.info("-" * 60)
                logger.info("CREATING DOCUMENT RECORDS IN COSMOS DB")
                logger.info("-" * 60)
                
                created_document_ids = []
                now = datetime.now(timezone.utc)
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    doc_type = uploaded_file.get("document_type")
                    blob_path = uploaded_file.get("blob_path")
                    original_path = uploaded_file.get("original_path")
                    
                    # Find page info for this document type
                    page_numbers = []
                    confidences = []
                    for page in pages:
                        page_doc_type = page.document_type if hasattr(page, 'document_type') else page.get('document_type')
                        if page_doc_type == doc_type:
                            page_num = page.page_number if hasattr(page, 'page_number') else page.get('page_number')
                            conf = page.confidence if hasattr(page, 'confidence') else page.get('confidence')
                            page_numbers.append(page_num)
                            if conf:
                                confidences.append(conf)
                    
                    avg_confidence = sum(confidences) / len(confidences) if confidences else None
                    
                    # Get file size from upload result (if available)
                    size_bytes = uploaded_file.get("size_bytes", 0)
                    
                    # Generate document ID
                    document_id = str(uuid.uuid4())
                    
                    # Build document record
                    document_data = {
                        "id": document_id,
                        "document_id": document_id,
                        "case_id": case_id,
                        "filename": Path(original_path).name if original_path else f"{doc_type}.pdf",
                        "content_type": "application/pdf",
                        "size_bytes": size_bytes,
                        "blob_path": blob_path,
                        "classification": doc_type,
                        "classification_confidence": avg_confidence,
                        "confidence_score": avg_confidence,  # Alias for API response
                        "processing_status": "completed",
                        "source": "extracted",  # Mark as extracted from main document
                        "parent_document_id": None,  # Could link to main doc if tracked
                        "page_range": f"{min(page_numbers)}-{max(page_numbers)}" if page_numbers else None,
                        "page_numbers": page_numbers,
                        "page_count": len(page_numbers),
                        "blob_upload_status": uploaded_file.get("upload_status", "unknown"),
                        "metadata": {
                            "source_document": original_path,
                            "document_type": doc_type,
                            "extraction_method": "classification_split",
                        },
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "created_by": user_id,
                        # Processing timestamps
                        "processing_started_at": workflow_started_at.isoformat(),
                        "processing_completed_at": now.isoformat(),
                        "processing_error": None,
                    }
                    
                    # ========== EMBED EXTRACTION RESULTS ==========
                    # If extraction was performed for this document type, embed the results
                    extraction_info = extraction_by_doc_type.get(doc_type)
                    if extraction_info and extraction_info.get("status") == "success" and extraction_info.get("data"):
                        ext_data = extraction_info["data"]
                        document_data["extraction"] = {
                            "extraction_id": ext_data.get("extraction_id"),
                            "status": ext_data.get("status", "completed"),
                            "fields": ext_data.get("fields", []),
                            "needs_review": ext_data.get("needs_review", False),
                            "models_used": ext_data.get("models_used", []),
                            "processing_time_ms": ext_data.get("processing_time_ms", 0),
                            "error_message": ext_data.get("error_message"),
                            "extraction_completed_at": now.isoformat(),
                        }
                        logger.info(f"    Embedded extraction: {len(ext_data.get('fields', []))} fields, needs_review={ext_data.get('needs_review', False)}")
                    elif extraction_info:
                        # Extraction was attempted but failed/skipped
                        document_data["extraction"] = {
                            "extraction_id": None,
                            "status": extraction_info.get("status", "skipped"),
                            "fields": [],
                            "needs_review": False,
                            "models_used": [],
                            "processing_time_ms": 0,
                            "error_message": extraction_info.get("error") or extraction_info.get("reason"),
                            "extraction_completed_at": now.isoformat(),
                        }
                        logger.info(f"    Extraction {extraction_info.get('status')}: {extraction_info.get('reason') or extraction_info.get('error')}")
                    else:
                        # No extraction attempted for this document type
                        document_data["extraction"] = None
                    
                    try:
                        created_doc = await self.document_repo.create_document(document_data)
                        created_document_ids.append(document_id)
                        logger.info(f"  ✓ Created document [{idx + 1}]: {document_id} ({doc_type})")
                    except Exception as doc_err:
                        logger.error(f"  ✗ Failed to create document record: {doc_err}")
                
                logger.info(f"Total documents created: {len(created_document_ids)}")
                logger.info("-" * 60)
                
                # Update case: processing status + case status transition to IN_REVIEW
                
                # Build status history entry for status transition
                current_case = await self.case_repo.get_case(case_id)
                status_history = current_case.get("status_history", [])
                status_history.append({
                    "previous_status": CaseStatus.DRAFT.value,
                    "new_status": CaseStatus.IN_REVIEW.value,
                    "changed_by": "workflow_system",
                    "changed_at": now.isoformat(),
                    "reason": "Workflow completed - documents classified and processed",
                })
                
                await self.case_repo.update_case(
                    case_id,
                    {
                        "status": CaseStatus.IN_REVIEW.value,  # Transition from DRAFT to IN_REVIEW
                        "processing_status": workflow_result.get('status', 'completed'),
                        "processing_completed_at": now.isoformat(),
                        "total_documents_expected": documents_count,
                        "documents_processed_count": documents_count,
                        "status_history": status_history,
                    },
                    user_id=user_id,
                )
                
                # Reload case to get updated data after workflow
                created = await self.case_repo.get_case(case_id)
                
            except Exception as e:
                # Log error but don't fail case creation
                logger.error(
                    f"Workflow failed for case {case_id}: {e}", 
                    exc_info=True
                )
                # Update case with workflow error
                await self.case_repo.update_case(
                    case_id,
                    {
                        "processing_status": "failed",
                        "processing_error": str(e),
                    },
                    user_id=user_id,
                )
                created = await self.case_repo.get_case(case_id)
            finally:
                # Clean up temp file
                if local_temp_path:
                    try:
                        Path(local_temp_path).unlink(missing_ok=True)
                        logger.debug(f"Cleaned up temp file: {local_temp_path}")
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to clean up temp file {local_temp_path}: {cleanup_err}")

        # Load documents for the case (may have been created during classification)
        documents = await self.document_repo.list_documents_for_case(case_id)
        return self._to_detail_response(created, documents)

    async def get_case(self, case_id: str) -> CaseDetailResponse:
        """
        Get case details by ID.

        Args:
            case_id: Case identifier

        Returns:
            Case details

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        # Load documents for the case
        documents = await self.document_repo.list_documents_for_case(case_id)

        return self._to_detail_response(case, documents)

    async def update_case(
        self,
        case_id: str,
        request: CaseUpdateRequest,
        user_id: str,
        new_document_content: Optional[bytes] = None,
        new_document_filename: Optional[str] = None,
        new_document_content_type: Optional[str] = None,
    ) -> CaseDetailResponse:
        """
        Update an existing case.

        Args:
            case_id: Case identifier
            request: Update request
            user_id: User making the update
            new_document_content: Optional new document file content
            new_document_filename: Optional new document filename
            new_document_content_type: Optional new document MIME type

        Returns:
            Updated case details

        Raises:
            NotFoundError: If case not found
            ConflictError: If status transition is invalid
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        now = datetime.now(timezone.utc)
        updates: dict[str, Any] = {"updated_at": now.isoformat()}
        status_changed = False

        # Apply updates
        if request.client_name is not None:
            updates["client_name"] = request.client_name

        if request.policy_type is not None:
            updates["policy_type"] = request.policy_type

        if request.metadata is not None:
            updates["metadata"] = request.metadata

        # Handle status transition
        if request.status is not None:
            current_status = CaseStatus(case["status"])
            if request.status != current_status:
                # Validate transition
                if not validate_status_transition(current_status, request.status):
                    raise ConflictError(
                        f"Invalid status transition from {current_status.value} to {request.status.value}"
                    )

                updates["status"] = request.status.value
                status_changed = True

                # Add to status history
                history = case.get("status_history", [])
                history.append(
                    {
                        "previous_status": current_status.value,
                        "new_status": request.status.value,
                        "changed_by": user_id,
                        "changed_at": now.isoformat(),
                        "reason": None,
                    }
                )
                updates["status_history"] = history

        # Upload new document if provided
        if new_document_content and new_document_filename and self.storage_service:
            await self._add_document_to_case(
                case_id=case_id,
                document_content=new_document_content,
                document_filename=new_document_filename,
                document_content_type=new_document_content_type or "application/octet-stream",
            )

        updated = await self.case_repo.update_case(case_id, updates)
        logger.info(f"Case {case_id} updated, status_changed={status_changed}")

        documents = await self.document_repo.list_documents_for_case(case_id)
        return self._to_detail_response(updated, documents)

    async def _add_document_to_case(
        self,
        case_id: str,
        document_content: bytes,
        document_filename: str,
        document_content_type: str,
        document_type: Optional[str] = None,
        document_metadata: Optional[dict[str, Any]] = None,
        source: str = "manual_upload",
    ) -> str:
        """
        Internal helper to add a document to a case.

        Args:
            case_id: Case identifier
            document_content: File content
            document_filename: Original filename
            document_content_type: MIME type
            document_type: Optional document classification
            document_metadata: Optional document metadata
            source: Document source (main_upload, extracted, manual_upload)

        Returns:
            Document ID of the created document
        """
        import uuid

        now = datetime.now(timezone.utc)
        document_id = str(uuid.uuid4())

        # Upload to blob storage
        blob_path = f"{case_id}/documents/{document_id}/{document_filename}"
        if self.storage_service:
            await self.storage_service.upload_blob(
                blob_path=blob_path,
                content=document_content,
                content_type=document_content_type,
            )
            logger.info(f"Document uploaded to {blob_path}")

        # Create document record in database
        document_data = {
            "id": document_id,
            "document_id": document_id,
            "case_id": case_id,
            "filename": document_filename,
            "content_type": document_content_type,
            "size_bytes": len(document_content),
            "blob_path": blob_path,
            "processing_status": "pending",
            "classification": document_type,
            "source": source,
            "parent_document_id": None,
            "page_range": None,
            "summary": None,
            "metadata": document_metadata or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await self.document_repo.create_document(document_data)
        logger.info(f"Document {document_id} created for case {case_id}")

        return document_id

    async def add_document_to_case(
        self,
        case_id: str,
        document_content: bytes,
        document_filename: str,
        document_content_type: str,
        document_type: Optional[str] = None,
        document_metadata: Optional[dict[str, Any]] = None,
    ) -> CaseDetailResponse:
        """
        Add a new document to an existing case.

        Args:
            case_id: Case identifier
            document_content: File content
            document_filename: Original filename
            document_content_type: MIME type
            document_type: Optional document classification
            document_metadata: Optional document metadata

        Returns:
            Updated case details

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        # Add the document
        document_id = await self._add_document_to_case(
            case_id=case_id,
            document_content=document_content,
            document_filename=document_filename,
            document_content_type=document_content_type,
            document_type=document_type,
            document_metadata=document_metadata,
            source="manual_upload",
        )

        # Update case updated_at timestamp
        now = datetime.now(timezone.utc)
        await self.case_repo.update_case(case_id, {"updated_at": now.isoformat()})

        logger.info(f"Document {document_id} added to case {case_id}")

        # Return updated case
        documents = await self.document_repo.list_documents_for_case(case_id)
        return self._to_detail_response(case, documents)

    async def delete_case(self, case_id: str, user_id: str) -> None:
        """
        Soft delete a case.

        Args:
            case_id: Case identifier
            user_id: User performing the deletion

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        await self.case_repo.soft_delete_case(case_id, user_id)
        logger.info(f"Case {case_id} soft deleted by {user_id}")

    async def restore_case(self, case_id: str, user_id: str) -> CaseDetailResponse:
        """
        Restore a soft-deleted case.

        Args:
            case_id: Case identifier
            user_id: User performing the restore

        Returns:
            Restored case details

        Raises:
            NotFoundError: If case not found
            ConflictError: If case is not deleted
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if not case.get("is_deleted"):
            raise ConflictError(f"Case {case_id} is not deleted")

        restored = await self.case_repo.restore_case(case_id, user_id)
        logger.info(f"Case {case_id} restored by {user_id}")

        documents = await self.document_repo.list_documents_for_case(case_id)
        return self._to_detail_response(restored, documents)

    async def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CaseStatus] = None,
        client_name_search: Optional[str] = None,
        include_deleted: bool = False,
    ) -> CaseListResponse:
        """
        List cases with filtering and pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            status: Filter by status
            client_name_search: Search in client name
            include_deleted: Include soft-deleted cases

        Returns:
            Paginated list of cases
        """
        if page < 1:
            raise BadRequestError("Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise BadRequestError("Page size must be between 1 and 100")

        # Build filters
        filters: dict[str, Any] = {}
        if not include_deleted:
            filters["is_deleted"] = False

        if status:
            filters["status"] = status.value

        # Get cases
        offset = (page - 1) * page_size
        cases, total = await self.case_repo.list_cases(
            filters=filters,
            client_name_search=client_name_search,
            limit=page_size,
            offset=offset,
        )

        # Get document counts for all cases
        case_ids = [c["case_id"] for c in cases]
        document_counts = await self._get_document_counts(case_ids)

        # Convert to response
        items = []
        for case in cases:
            counts = document_counts.get(case["case_id"], {"total": 0, "processed": 0})
            items.append(
                CaseSummaryResponse(
                    case_id=case["case_id"],
                    client_name=case["client_name"],
                    policy_type=case["policy_type"],
                    status=CaseStatus(case["status"]),
                    document_count=counts["total"],
                    documents_processed=counts["processed"],
                    created_at=datetime.fromisoformat(case["created_at"]),
                    updated_at=datetime.fromisoformat(case["updated_at"]),
                )
            )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return CaseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_status_history(self, case_id: str) -> StatusHistoryResponse:
        """
        Get status change history for a case.

        Args:
            case_id: Case identifier

        Returns:
            Status history

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        history_data = case.get("status_history", [])
        history = []
        for entry in history_data:
            history.append(
                StatusHistoryEntry(
                    previous_status=(
                        CaseStatus(entry["previous_status"])
                        if entry.get("previous_status")
                        else None
                    ),
                    new_status=CaseStatus(entry["new_status"]),
                    changed_by=entry["changed_by"],
                    changed_at=datetime.fromisoformat(entry["changed_at"]),
                    reason=entry.get("reason"),
                )
            )

        return StatusHistoryResponse(case_id=case_id, history=history)

    async def update_processing_status(
        self,
        case_id: str,
        processing_status: str,
        total_documents_expected: Optional[int] = None,
        processing_error: Optional[str] = None,
    ) -> None:
        """
        Update the processing status of a case.

        Args:
            case_id: Case identifier
            processing_status: New processing status
            total_documents_expected: Total documents expected (set during extraction)
            processing_error: Error message if processing failed
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        now = datetime.now(timezone.utc)
        updates: dict[str, Any] = {
            "processing_status": processing_status,
            "updated_at": now.isoformat(),
        }

        if processing_status == "extracting_documents":
            updates["processing_started_at"] = now.isoformat()
        elif processing_status in ("completed", "failed"):
            updates["processing_completed_at"] = now.isoformat()

        if total_documents_expected is not None:
            updates["total_documents_expected"] = total_documents_expected

        if processing_error:
            updates["processing_error"] = processing_error

        await self.case_repo.update_case(case_id, updates)
        logger.info(f"Case {case_id} processing status updated to {processing_status}")

    async def increment_documents_processed(self, case_id: str) -> int:
        """
        Increment the documents processed count and check if all documents are done.

        Args:
            case_id: Case identifier

        Returns:
            Updated documents_processed_count
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        new_count = case.get("documents_processed_count", 0) + 1
        await self.case_repo.update_case(
            case_id,
            {
                "documents_processed_count": new_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info(f"Case {case_id} documents processed: {new_count}")
        return new_count

    async def set_case_summary(
        self, case_id: str, summary: str
    ) -> None:
        """
        Set the case summary after all documents are processed.

        Args:
            case_id: Case identifier
            summary: Generated case summary
        """
        case = await self.case_repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        now = datetime.now(timezone.utc)
        await self.case_repo.update_case(
            case_id,
            {
                "case_summary": summary,
                "case_summary_updated_at": now.isoformat(),
                "processing_status": "completed",
                "processing_completed_at": now.isoformat(),
                "updated_at": now.isoformat(),
            },
        )
        logger.info(f"Case {case_id} summary set and processing completed")

    async def _get_document_counts(
        self, case_ids: list[str]
    ) -> dict[str, dict[str, int]]:
        """Get document counts for multiple cases."""
        counts: dict[str, dict[str, int]] = {}
        for case_id in case_ids:
            documents = await self.document_repo.list_documents_for_case(case_id)
            total = len(documents)
            processed = sum(
                1 for d in documents if d.get("processing_status") == "completed"
            )
            counts[case_id] = {"total": total, "processed": processed}
        return counts

    def _to_detail_response(
        self,
        case: dict[str, Any],
        documents: Optional[list[dict[str, Any]]] = None,
    ) -> CaseDetailResponse:
        """Convert case data to detail response."""
        doc_summaries = []
        if documents:
            for doc in documents:
                doc_summaries.append(
                    DocumentSummaryInCase(
                        document_id=doc["document_id"],
                        filename=doc["filename"],
                    )
                )

        return CaseDetailResponse(
            case_id=case["case_id"],
            client_name=case["client_name"],
            policy_type=case["policy_type"],
            submission_date=date.fromisoformat(case["submission_date"]),
            status=CaseStatus(case["status"]),
            created_at=datetime.fromisoformat(case["created_at"]),
            updated_at=datetime.fromisoformat(case["updated_at"]),
            created_by=case["created_by"],
            metadata=case.get("metadata", {}),
            main_document_blob_path=case.get("main_document_blob_path"),
            # Processing tracking fields
            processing_status=case.get("processing_status", "not_started"),
            total_documents_expected=case.get("total_documents_expected"),
            documents_processed_count=case.get("documents_processed_count", 0),
            processing_started_at=(
                datetime.fromisoformat(case["processing_started_at"])
                if case.get("processing_started_at")
                else None
            ),
            processing_completed_at=(
                datetime.fromisoformat(case["processing_completed_at"])
                if case.get("processing_completed_at")
                else None
            ),
            processing_error=case.get("processing_error"),
            documents=doc_summaries,
            case_summary=case.get("case_summary"),
            case_summary_updated_at=(
                datetime.fromisoformat(case["case_summary_updated_at"])
                if case.get("case_summary_updated_at")
                else None
            ),
        )
