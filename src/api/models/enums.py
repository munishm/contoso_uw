"""
Status enumerations for API models.

These enums define the valid states for cases, documents, and processing status.
"""

from enum import Enum


class CaseStatus(str, Enum):
    """Status values for underwriting cases."""

    DRAFT = "draft"
    IN_REVIEW = "in-review"
    PENDING_DOCUMENTS = "pending-documents"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"
    DELETED = "deleted"


class ProcessingStatus(str, Enum):
    """Status values for document processing."""

    PENDING = "pending"
    CLASSIFYING = "classifying"
    EXTRACTING_ENTITIES = "extracting-entities"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Classification types for documents."""

    APPLICATION_FORM = "application_form"
    FINANCIAL_STATEMENT = "financial_statement"
    MEDICAL_REPORT = "medical_report"
    IDENTITY_DOCUMENT = "identity_document"
    PROPERTY_ASSESSMENT = "property_assessment"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    INSURANCE_POLICY = "insurance_policy"
    LEGAL_DOCUMENT = "legal_document"
    OTHER = "other"


class CaseProcessingStatus(str, Enum):
    """Status values for overall case document processing."""

    NOT_STARTED = "not_started"  # No main document uploaded
    EXTRACTING_DOCUMENTS = "extracting_documents"  # Extracting individual docs from main doc
    PROCESSING_DOCUMENTS = "processing_documents"  # Individual docs being classified/summarized
    GENERATING_CASE_SUMMARY = "generating_case_summary"  # All docs done, generating case summary
    COMPLETED = "completed"  # All processing complete including case summary
    FAILED = "failed"  # Processing failed


class DocumentSource(str, Enum):
    """Source of a document - how it was added to the case."""

    MAIN_UPLOAD = "main_upload"  # The original uploaded main document
    EXTRACTED = "extracted"  # Extracted from the main document
    MANUAL_UPLOAD = "manual_upload"  # Manually uploaded separately (future use)


# Status transition rules for cases
VALID_CASE_TRANSITIONS: dict[CaseStatus, list[CaseStatus]] = {
    CaseStatus.DRAFT: [CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.IN_REVIEW: [
        CaseStatus.PENDING_DOCUMENTS,
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
        CaseStatus.DRAFT,
        CaseStatus.DELETED,
    ],
    CaseStatus.PENDING_DOCUMENTS: [CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.APPROVED: [CaseStatus.CLOSED, CaseStatus.DELETED],
    CaseStatus.REJECTED: [CaseStatus.CLOSED, CaseStatus.IN_REVIEW, CaseStatus.DELETED],
    CaseStatus.CLOSED: [CaseStatus.DELETED],
    CaseStatus.DELETED: [],  # Restore handled separately via /restore endpoint
}


def validate_status_transition(current: CaseStatus, new: CaseStatus) -> bool:
    """
    Validate if a status transition is allowed.

    Args:
        current: The current case status
        new: The target case status

    Returns:
        True if the transition is valid, False otherwise
    """
    return new in VALID_CASE_TRANSITIONS.get(current, [])
