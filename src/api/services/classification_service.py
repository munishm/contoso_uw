"""
Document classification service.

Handles document classification using the classifier module and updates case/document records.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.api.middleware.error_handler import BadRequestError, NotFoundError
from src.api.models.enums import DocumentType, ProcessingStatus
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for document classification operations."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        case_repository: CaseRepository,
        storage_service: StorageService,
    ) -> None:
        """
        Initialize classification service with dependencies.

        Args:
            document_repository: Repository for document data access
            case_repository: Repository for case data access
            storage_service: Service for blob storage operations
        """
        self.document_repo = document_repository
        self.case_repo = case_repository
        self.storage_service = storage_service
        self._classifier = None

    def _get_classifier(self):
        """
        Lazy initialize the classifier with blob storage support.
        
        Returns:
            DocumentClassifier instance configured with storage service
        """
        if self._classifier is None:
            # Import here to avoid circular imports and lazy load
            from src.interfaces.classifier import DocumentClassifier
            # Pass storage service to enable blob operations
            self._classifier = DocumentClassifier(storage_service=self.storage_service)
            logger.info("Document classifier initialized with blob storage support")
        return self._classifier

    async def classify_case_documents(
        self,
        case_id: str,
        main_document_blob_path: str,
    ) -> dict[str, Any]:
        """
        Classify documents for a case.

        Uses the classifier's blob storage support to download and classify
        the document, then creates individual document records for each segment.

        Args:
            case_id: Case identifier
            main_document_blob_path: Blob path to the main uploaded document

        Returns:
            Classification results with created document records
        """
        logger.info(f"Starting classification for case {case_id}")

        # Update case processing status
        await self._update_case_processing_status(
            case_id,
            processing_status="classifying",
            processing_started_at=datetime.now(timezone.utc),
        )

        try:
            # Get classifier with blob storage support
            classifier = self._get_classifier()
            
            # Classify directly from blob storage (handles download internally)
            classification_result = await classifier.classify_from_blob(
                blob_path=main_document_blob_path,
                cleanup=True  # Auto-cleanup temp files
            )

            # Process classification results and create document records
            documents_created = await self._process_classification_results(
                case_id=case_id,
                main_document_blob_path=main_document_blob_path,
                classification_result=classification_result,
            )

            # Update case with classification completion
            await self._update_case_processing_status(
                case_id,
                processing_status="completed",
                processing_completed_at=datetime.now(timezone.utc),
                total_documents_expected=len(documents_created),
                documents_processed_count=len(documents_created),
            )

            logger.info(
                f"Classification completed for case {case_id}: "
                f"{len(documents_created)} documents identified"
            )

            return {
                "case_id": case_id,
                "status": "completed",
                "documents_created": len(documents_created),
                "classification_result": classification_result,
                "documents": documents_created,
            }

        except Exception as e:
            logger.error(f"Classification failed for case {case_id}: {e}", exc_info=True)
            
            # Update case with failure status
            await self._update_case_processing_status(
                case_id,
                processing_status="failed",
                processing_error=str(e),
            )

            return {
                "case_id": case_id,
                "status": "failed",
                "error": str(e),
            }

    async def _process_classification_results(
        self,
        case_id: str,
        main_document_blob_path: str,
        classification_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Process classification results and create document records.

        Args:
            case_id: Case identifier
            main_document_blob_path: Path to the main document in blob storage
            classification_result: Result from the classifier

        Returns:
            List of created document records
        """
        import uuid

        documents_created = []
        now = datetime.now(timezone.utc)

        # Get segments from classification result
        segments = classification_result.get("segments", [])
        page_classifications = classification_result.get("page_classifications", [])

        if segments:
            # Create a document record for each segment
            for segment in segments:
                document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
                
                # Map classifier category to DocumentType enum
                category = segment.get("category", "Other")
                document_type = self._map_category_to_document_type(category)
                
                # Determine page range
                start_page = segment.get("start_page", 1)
                end_page = segment.get("end_page", 1)
                page_range = f"{start_page}-{end_page}" if start_page != end_page else str(start_page)

                # Extract filename from blob path
                original_filename = Path(main_document_blob_path).name
                segment_filename = f"{Path(original_filename).stem}_segment_{segment.get('segment_id', document_id)}{Path(original_filename).suffix}"

                document_data = {
                    "id": document_id,
                    "document_id": document_id,
                    "case_id": case_id,
                    "filename": segment_filename,
                    "content_type": "application/pdf",  # Assume PDF for segments
                    "size_bytes": 0,  # Will be updated when segment is extracted
                    "blob_path": main_document_blob_path,  # Reference to parent document
                    "processing_status": ProcessingStatus.COMPLETED.value,
                    "classification": document_type,
                    "confidence_score": segment.get("confidence"),
                    "extracted_text": None,
                    "summary": None,
                    "metadata": {
                        "segment_id": segment.get("segment_id"),
                        "category": category,
                        "start_page": start_page,
                        "end_page": end_page,
                        "classification_method": classification_result.get("metadata", {}).get("method", "unknown"),
                    },
                    "source": "extracted",
                    "parent_document_id": None,  # Will be set if we have a parent
                    "page_range": page_range,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "created_by": "classification_service",
                    "processing_started_at": now.isoformat(),
                    "processing_completed_at": now.isoformat(),
                    "processing_error": None,
                }

                await self.document_repo.create_document(document_data)
                documents_created.append(document_data)
                logger.info(
                    f"Created document {document_id} for case {case_id}: "
                    f"{category} (pages {page_range})"
                )
        else:
            # No segments - create a single document record for the whole file
            document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
            category = classification_result.get("document_type", "Other")
            document_type = self._map_category_to_document_type(category)
            original_filename = Path(main_document_blob_path).name

            document_data = {
                "id": document_id,
                "document_id": document_id,
                "case_id": case_id,
                "filename": original_filename,
                "content_type": "application/pdf",
                "size_bytes": 0,
                "blob_path": main_document_blob_path,
                "processing_status": ProcessingStatus.COMPLETED.value,
                "classification": document_type,
                "confidence_score": classification_result.get("confidence"),
                "extracted_text": None,
                "summary": None,
                "metadata": {
                    "category": category,
                    "classification_method": classification_result.get("metadata", {}).get("method", "unknown"),
                },
                "source": "main_upload",
                "parent_document_id": None,
                "page_range": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "created_by": "classification_service",
                "processing_started_at": now.isoformat(),
                "processing_completed_at": now.isoformat(),
                "processing_error": None,
            }

            await self.document_repo.create_document(document_data)
            documents_created.append(document_data)
            logger.info(
                f"Created document {document_id} for case {case_id}: {category}"
            )

        return documents_created

    def _map_category_to_document_type(self, category: str) -> str:
        """
        Map classifier category to DocumentType enum value.

        Args:
            category: Category string from classifier

        Returns:
            DocumentType value string
        """
        # Map common categories to DocumentType enum values
        category_mapping = {
            # Direct mappings
            "application_form": DocumentType.APPLICATION_FORM.value,
            "financial_statement": DocumentType.FINANCIAL_STATEMENT.value,
            "medical_report": DocumentType.MEDICAL_REPORT.value,
            "identity_document": DocumentType.IDENTITY_DOCUMENT.value,
            "property_assessment": DocumentType.PROPERTY_ASSESSMENT.value,
            "bank_statement": DocumentType.BANK_STATEMENT.value,
            "tax_return": DocumentType.TAX_RETURN.value,
            "insurance_policy": DocumentType.INSURANCE_POLICY.value,
            "legal_document": DocumentType.LEGAL_DOCUMENT.value,
            # Alternative mappings (handle variations from classifier)
            "application": DocumentType.APPLICATION_FORM.value,
            "financial": DocumentType.FINANCIAL_STATEMENT.value,
            "medical": DocumentType.MEDICAL_REPORT.value,
            "identity": DocumentType.IDENTITY_DOCUMENT.value,
            "property": DocumentType.PROPERTY_ASSESSMENT.value,
            "bank": DocumentType.BANK_STATEMENT.value,
            "tax": DocumentType.TAX_RETURN.value,
            "insurance": DocumentType.INSURANCE_POLICY.value,
            "legal": DocumentType.LEGAL_DOCUMENT.value,
            "other": DocumentType.OTHER.value,
        }

        # Normalize category and look up
        normalized = category.lower().replace(" ", "_").replace("-", "_")
        return category_mapping.get(normalized, DocumentType.OTHER.value)

    async def _update_case_processing_status(
        self,
        case_id: str,
        processing_status: str,
        processing_started_at: Optional[datetime] = None,
        processing_completed_at: Optional[datetime] = None,
        processing_error: Optional[str] = None,
        total_documents_expected: Optional[int] = None,
        documents_processed_count: Optional[int] = None,
    ) -> None:
        """
        Update case processing status fields.

        Args:
            case_id: Case identifier
            processing_status: New processing status
            processing_started_at: When processing started
            processing_completed_at: When processing completed
            processing_error: Error message if failed
            total_documents_expected: Total documents to process
            documents_processed_count: Documents processed so far
        """
        updates = {
            "processing_status": processing_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if processing_started_at:
            updates["processing_started_at"] = processing_started_at.isoformat()
        if processing_completed_at:
            updates["processing_completed_at"] = processing_completed_at.isoformat()
        if processing_error:
            updates["processing_error"] = processing_error
        if total_documents_expected is not None:
            updates["total_documents_expected"] = total_documents_expected
        if documents_processed_count is not None:
            updates["documents_processed_count"] = documents_processed_count

        await self.case_repo.update_case(case_id, updates)
        logger.debug(f"Updated case {case_id} processing status to: {processing_status}")

    async def classify_single_document(
        self,
        case_id: str,
        document_id: str,
        blob_path: str,
    ) -> dict[str, Any]:
        """
        Classify a single document.

        Args:
            case_id: Case identifier
            document_id: Document identifier
            blob_path: Path to document in blob storage

        Returns:
            Classification result
        """
        logger.info(f"Classifying document {document_id} for case {case_id}")

        # Update document status
        await self.document_repo.update_document(
            document_id,
            case_id,
            {"processing_status": ProcessingStatus.CLASSIFYING.value},
        )

        try:
            # Get classifier with blob storage support and classify directly
            classifier = self._get_classifier()
            classification_result = await classifier.classify_from_blob(
                blob_path=blob_path,
                cleanup=True
            )

            # Map category to document type
            category = classification_result.get("document_type", "Other")
            document_type = self._map_category_to_document_type(category)

            # Update document with classification result
            now = datetime.now(timezone.utc)
            await self.document_repo.update_document(
                document_id,
                case_id,
                {
                    "processing_status": ProcessingStatus.COMPLETED.value,
                    "classification": document_type,
                    "confidence_score": classification_result.get("confidence"),
                    "metadata": {
                        "category": category,
                        "classification_method": classification_result.get("metadata", {}).get("method", "unknown"),
                        "segments": classification_result.get("segments", []),
                    },
                    "processing_completed_at": now.isoformat(),
                },
            )

            logger.info(
                f"Document {document_id} classified as: {category} "
                f"(confidence: {classification_result.get('confidence')})"
            )

            return {
                "document_id": document_id,
                "status": "completed",
                "classification": document_type,
                "confidence": classification_result.get("confidence"),
                "classification_result": classification_result,
            }

        except Exception as e:
            logger.error(f"Classification failed for document {document_id}: {e}", exc_info=True)
            
            await self.document_repo.update_document(
                document_id,
                case_id,
                {
                    "processing_status": ProcessingStatus.FAILED.value,
                    "processing_error": str(e),
                },
            )

            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e),
            }
