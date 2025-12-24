"""
Case business logic service.

Handles case operations including validation, state transitions, and CRUD operations.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

from src.api.middleware.error_handler import BadRequestError, ConflictError, NotFoundError
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

logger = logging.getLogger(__name__)


class CaseService:
    """Service for case management operations."""

    def __init__(
        self,
        case_repository: CaseRepository,
        document_repository: DocumentRepository,
        counter_repository: CounterRepository,
        storage_service: Optional[StorageService] = None,
    ) -> None:
        """
        Initialize case service with repositories.

        Args:
            case_repository: Repository for case data access
            document_repository: Repository for document data access
            counter_repository: Repository for ID generation
            storage_service: Service for blob storage operations
        """
        self.case_repo = case_repository
        self.document_repo = document_repository
        self.counter_repo = counter_repository
        self.storage_service = storage_service

    async def create_case(
        self,
        client_name: str,
        policy_type: str,
        submission_date: date,
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
            submission_date: Date the case was submitted
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
            "submission_date": submission_date.isoformat(),
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

        return self._to_detail_response(created)

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

        if request.submission_date is not None:
            updates["submission_date"] = request.submission_date.isoformat()

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
                        content_type=doc["content_type"],
                        size_bytes=doc["size_bytes"],
                        processing_status=doc.get("processing_status", "pending"),
                        classification=doc.get("classification"),
                        source=doc.get("source"),
                        parent_document_id=doc.get("parent_document_id"),
                        page_range=doc.get("page_range"),
                        summary=doc.get("summary"),
                        created_at=datetime.fromisoformat(doc["created_at"]),
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
