"""
Processing results service.

Handles retrieval of entity extraction results, summaries, and explanations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from src.api.middleware.error_handler import BadRequestError, NotFoundError
from src.api.models.entity import (
    EntityAggregateResponse,
    EntityExplainResponse,
    EntityListResponse,
    EntityResponse,
    EntityTypeCount,
)
from src.api.models.summary import (
    CaseSummaryDetailResponse,
    DocumentSummaryDetailResponse,
    ReprocessRequest,
    ReprocessResponse,
    SummaryExplainResponse,
)
from src.api.repositories.case_repository import CaseRepository
from src.api.repositories.document_repository import DocumentRepository
from src.api.repositories.entity_repository import EntityRepository
from src.api.repositories.summary_repository import SummaryRepository
from src.api.services.queue_service import QueueService

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for processing results operations."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        case_repository: CaseRepository,
        entity_repository: EntityRepository,
        summary_repository: SummaryRepository,
        queue_service: QueueService,
    ) -> None:
        """
        Initialize processing service with dependencies.

        Args:
            document_repository: Repository for document data access
            case_repository: Repository for case data access
            entity_repository: Repository for entity data access
            summary_repository: Repository for summary data access
            queue_service: Service for message queue operations
        """
        self.document_repo = document_repository
        self.case_repo = case_repository
        self.entity_repo = entity_repository
        self.summary_repo = summary_repository
        self.queue_service = queue_service

    async def get_document_entities(
        self, case_id: str, document_id: str
    ) -> EntityListResponse:
        """
        Get all entities extracted from a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            List of extracted entities

        Raises:
            NotFoundError: If document not found
        """
        document = await self._verify_document(case_id, document_id)

        entities = await self.entity_repo.get_entities_for_document(document_id)

        entity_responses = [
            EntityResponse(
                entity_id=e["entity_id"],
                document_id=e["document_id"],
                case_id=e["case_id"],
                entity_type=e["entity_type"],
                value=e["value"],
                confidence=e.get("confidence", 0.0),
                source_location=e.get("source_location"),
                normalized_value=e.get("normalized_value"),
                metadata=e.get("metadata", {}),
                created_at=datetime.fromisoformat(e["created_at"]),
            )
            for e in entities
        ]

        return EntityListResponse(
            document_id=document_id,
            case_id=case_id,
            entities=entity_responses,
            total=len(entity_responses),
            extraction_status=document.get("processing_status", "pending"),
            extraction_completed_at=(
                datetime.fromisoformat(document["processing_completed_at"])
                if document.get("processing_completed_at")
                else None
            ),
        )

    async def explain_entity(
        self, case_id: str, document_id: str, entity_id: str
    ) -> EntityExplainResponse:
        """
        Get explanation for an entity extraction.

        Args:
            case_id: Case identifier
            document_id: Document identifier
            entity_id: Entity identifier

        Returns:
            Explanation of the entity extraction

        Raises:
            NotFoundError: If entity not found
        """
        await self._verify_document(case_id, document_id)

        entity = await self.entity_repo.get_entity(entity_id, document_id)
        if not entity:
            raise NotFoundError(
                f"Entity {entity_id} not found in document {document_id}"
            )

        # Generate explanation (in a real system, this would come from the AI model)
        explanation = self._generate_entity_explanation(entity)

        return EntityExplainResponse(
            entity_id=entity_id,
            entity_type=entity["entity_type"],
            value=entity["value"],
            confidence=entity.get("confidence", 0.0),
            explanation=explanation,
            source_text=entity.get("source_text"),
            extraction_method=entity.get("extraction_method", "NER"),
            alternatives=entity.get("alternatives", []),
        )

    async def get_document_summary(
        self, case_id: str, document_id: str
    ) -> DocumentSummaryDetailResponse:
        """
        Get the AI-generated summary for a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            Document summary details

        Raises:
            NotFoundError: If document not found
        """
        document = await self._verify_document(case_id, document_id)

        summary = await self.summary_repo.get_summary_for_document(document_id)

        return DocumentSummaryDetailResponse(
            document_id=document_id,
            case_id=case_id,
            summary=summary.get("summary") if summary else document.get("summary"),
            key_points=summary.get("key_points", []) if summary else [],
            document_type=document.get("classification"),
            confidence_score=summary.get("confidence_score") if summary else None,
            word_count=summary.get("word_count") if summary else None,
            summary_word_count=summary.get("summary_word_count") if summary else None,
            generated_at=(
                datetime.fromisoformat(summary["generated_at"])
                if summary and summary.get("generated_at")
                else None
            ),
            model_version=summary.get("model_version") if summary else None,
        )

    async def explain_summary(
        self, case_id: str, document_id: str
    ) -> SummaryExplainResponse:
        """
        Get explanation of how a document summary was generated.

        Args:
            case_id: Case identifier
            document_id: Document identifier

        Returns:
            Explanation of summary generation

        Raises:
            NotFoundError: If document not found or no summary exists
        """
        document = await self._verify_document(case_id, document_id)

        summary = await self.summary_repo.get_summary_for_document(document_id)
        summary_text = (
            summary.get("summary") if summary else document.get("summary")
        )

        if not summary_text:
            raise NotFoundError(f"No summary found for document {document_id}")

        # Generate explanation (in a real system, this would be stored with the summary)
        explanation = self._generate_summary_explanation(summary or {}, document)

        return SummaryExplainResponse(
            document_id=document_id,
            summary=summary_text,
            explanation=explanation,
            key_sections_used=summary.get("key_sections_used", []) if summary else [],
            extraction_method=summary.get("method", "abstractive") if summary else "abstractive",
            model_name=summary.get("model_name", "gpt-4") if summary else "gpt-4",
            processing_time_ms=summary.get("processing_time_ms") if summary else None,
        )

    async def reprocess_document(
        self, case_id: str, document_id: str, request: ReprocessRequest, user_id: str
    ) -> ReprocessResponse:
        """
        Request reprocessing of a document.

        Args:
            case_id: Case identifier
            document_id: Document identifier
            request: Reprocess request details
            user_id: User requesting reprocessing

        Returns:
            Reprocess response

        Raises:
            NotFoundError: If document not found
            BadRequestError: If document is currently processing
        """
        document = await self._verify_document(case_id, document_id)

        # Check if already processing
        if document.get("processing_status") == "processing" and not request.force:
            raise BadRequestError(
                f"Document {document_id} is currently being processed. "
                "Use force=true to override."
            )

        # Validate stages
        valid_stages = {"classification", "extraction", "summarization"}
        invalid_stages = set(request.stages) - valid_stages
        if invalid_stages:
            raise BadRequestError(
                f"Invalid processing stages: {invalid_stages}. "
                f"Valid stages: {valid_stages}"
            )

        # Queue for reprocessing
        await self.queue_service.send_reprocess_event(
            document_id=document_id,
            case_id=case_id,
            blob_path=document["blob_path"],
            stages=request.stages,
        )

        # Update document status
        await self.document_repo.update_processing_status(
            document_id, case_id, "pending"
        )

        logger.info(
            f"Document {document_id} queued for reprocessing by {user_id}, "
            f"stages: {request.stages}"
        )

        return ReprocessResponse(
            document_id=document_id,
            case_id=case_id,
            message="Document queued for reprocessing",
            queued=True,
            stages=request.stages,
        )

    async def get_case_entities_aggregate(
        self, case_id: str
    ) -> EntityAggregateResponse:
        """
        Get aggregated entity statistics for a case.

        Args:
            case_id: Case identifier

        Returns:
            Aggregated entity statistics

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case or case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        documents = await self.document_repo.list_documents_for_case(case_id)

        # Count documents by processing status
        docs_processed = sum(
            1 for d in documents if d.get("processing_status") == "completed"
        )
        docs_pending = len(documents) - docs_processed

        # Get all entities for the case
        all_entities: list[dict[str, Any]] = []
        for doc in documents:
            entities = await self.entity_repo.get_entities_for_document(
                doc["document_id"]
            )
            all_entities.extend(entities)

        # Aggregate by type
        type_counts: dict[str, int] = {}
        for entity in all_entities:
            entity_type = entity["entity_type"]
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        by_type = [
            EntityTypeCount(entity_type=t, count=c)
            for t, c in sorted(type_counts.items())
        ]

        return EntityAggregateResponse(
            case_id=case_id,
            total_entities=len(all_entities),
            documents_processed=docs_processed,
            documents_pending=docs_pending,
            by_type=by_type,
        )

    async def get_case_summary(self, case_id: str) -> CaseSummaryDetailResponse:
        """
        Get comprehensive summary of all documents in a case.

        Args:
            case_id: Case identifier

        Returns:
            Case summary with all document summaries

        Raises:
            NotFoundError: If case not found
        """
        case = await self.case_repo.get_case(case_id)
        if not case or case.get("is_deleted"):
            raise NotFoundError(f"Case {case_id} not found")

        documents = await self.document_repo.list_documents_for_case(case_id)

        # Get summaries for all documents
        doc_summaries = []
        docs_summarized = 0
        for doc in documents:
            summary = await self.summary_repo.get_summary_for_document(
                doc["document_id"]
            )
            if summary or doc.get("summary"):
                docs_summarized += 1
                doc_summaries.append(
                    DocumentSummaryDetailResponse(
                        document_id=doc["document_id"],
                        case_id=case_id,
                        summary=summary.get("summary") if summary else doc.get("summary"),
                        key_points=summary.get("key_points", []) if summary else [],
                        document_type=doc.get("classification"),
                        confidence_score=summary.get("confidence_score") if summary else None,
                        word_count=summary.get("word_count") if summary else None,
                        summary_word_count=summary.get("summary_word_count") if summary else None,
                        generated_at=(
                            datetime.fromisoformat(summary["generated_at"])
                            if summary and summary.get("generated_at")
                            else None
                        ),
                        model_version=summary.get("model_version") if summary else None,
                    )
                )

        # Get case-level summary
        case_summary_data = await self.summary_repo.get_case_summary(case_id)

        return CaseSummaryDetailResponse(
            case_id=case_id,
            case_summary=case.get("case_summary") or (
                case_summary_data.get("summary") if case_summary_data else None
            ),
            document_summaries=doc_summaries,
            key_findings=case_summary_data.get("key_findings", []) if case_summary_data else [],
            risk_indicators=case_summary_data.get("risk_indicators", []) if case_summary_data else [],
            missing_information=case_summary_data.get("missing_information", []) if case_summary_data else [],
            total_documents=len(documents),
            documents_summarized=docs_summarized,
            generated_at=(
                datetime.fromisoformat(case["case_summary_updated_at"])
                if case.get("case_summary_updated_at")
                else None
            ),
        )

    async def _verify_document(
        self, case_id: str, document_id: str
    ) -> dict[str, Any]:
        """Verify document exists and belongs to case."""
        document = await self.document_repo.get_document(document_id)
        if not document or document.get("case_id") != case_id:
            raise NotFoundError(
                f"Document {document_id} not found in case {case_id}"
            )
        return document

    def _generate_entity_explanation(self, entity: dict[str, Any]) -> str:
        """Generate explanation for entity extraction."""
        entity_type = entity["entity_type"]
        value = entity["value"]
        confidence = entity.get("confidence", 0.0)
        method = entity.get("extraction_method", "NER")

        return (
            f"The {entity_type} '{value}' was extracted using {method} "
            f"with {confidence:.0%} confidence. "
            f"This entity was identified based on contextual patterns "
            f"and entity type definitions in the document."
        )

    def _generate_summary_explanation(
        self, summary: dict[str, Any], document: dict[str, Any]
    ) -> str:
        """Generate explanation for summary generation."""
        method = summary.get("method", "abstractive")
        model = summary.get("model_name", "gpt-4")

        return (
            f"This summary was generated using {method} summarization "
            f"with the {model} model. The document was analyzed to identify "
            f"key information relevant to underwriting decisions, including "
            f"risk factors, financial data, and client information."
        )
