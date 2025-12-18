"""
Summary models.

Pydantic models for document and case summary API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentSummaryDetailResponse(BaseModel):
    """Detailed summary response for a document."""

    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Parent case identifier")
    summary: Optional[str] = Field(
        default=None, description="AI-generated summary of the document"
    )
    key_points: list[str] = Field(
        default_factory=list, description="Key points extracted from the document"
    )
    document_type: Optional[str] = Field(
        default=None, description="Classified document type"
    )
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Summary confidence"
    )
    word_count: Optional[int] = Field(
        default=None, ge=0, description="Word count of original document"
    )
    summary_word_count: Optional[int] = Field(
        default=None, ge=0, description="Word count of summary"
    )
    generated_at: Optional[datetime] = Field(
        default=None, description="When summary was generated"
    )
    model_version: Optional[str] = Field(
        default=None, description="AI model version used for summarization"
    )

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SummaryExplainResponse(BaseModel):
    """Explanation of how a summary was generated."""

    document_id: str = Field(..., description="Document identifier")
    summary: str = Field(..., description="The generated summary")
    explanation: str = Field(
        ..., description="Explanation of how the summary was generated"
    )
    key_sections_used: list[str] = Field(
        default_factory=list,
        description="Sections of the document used to generate summary",
    )
    extraction_method: str = Field(
        ..., description="Summarization method (e.g., 'extractive', 'abstractive')"
    )
    model_name: str = Field(..., description="AI model used for summarization")
    processing_time_ms: Optional[int] = Field(
        default=None, ge=0, description="Processing time in milliseconds"
    )

    model_config = ConfigDict(protected_namespaces=())


class CaseSummaryDetailResponse(BaseModel):
    """Comprehensive summary of all documents in a case."""

    case_id: str = Field(..., description="Case identifier")
    case_summary: Optional[str] = Field(
        default=None, description="AI-generated summary of all case documents"
    )
    document_summaries: list[DocumentSummaryDetailResponse] = Field(
        default_factory=list, description="Individual document summaries"
    )
    key_findings: list[str] = Field(
        default_factory=list, description="Key findings across all documents"
    )
    risk_indicators: list[str] = Field(
        default_factory=list, description="Identified risk indicators"
    )
    missing_information: list[str] = Field(
        default_factory=list, description="Information typically needed but not found"
    )
    total_documents: int = Field(..., ge=0, description="Total documents in case")
    documents_summarized: int = Field(
        ..., ge=0, description="Documents with completed summaries"
    )
    generated_at: Optional[datetime] = Field(
        default=None, description="When case summary was last generated"
    )

    model_config = ConfigDict(from_attributes=True)


class ReprocessRequest(BaseModel):
    """Request to reprocess a document."""

    force: bool = Field(
        default=False,
        description="Force reprocessing even if already completed",
    )
    stages: list[str] = Field(
        default_factory=lambda: ["classification", "extraction", "summarization"],
        description="Processing stages to run",
    )


class ReprocessResponse(BaseModel):
    """Response after requesting document reprocessing."""

    document_id: str = Field(..., description="Document identifier")
    case_id: str = Field(..., description="Case identifier")
    message: str = Field(..., description="Status message")
    queued: bool = Field(..., description="Whether reprocessing was queued")
    stages: list[str] = Field(..., description="Stages that will be reprocessed")
