"""Pydantic models for document classification responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PageClassification(BaseModel):
    """Classification result for a specific page."""
    page_number: int = Field(description="Page number (1-indexed)")
    document_type: str = Field(description="Classified document type/category")
    segment_id: str = Field(description="Unique identifier for the segment")
    confidence: Optional[float] = Field(None, description="Confidence score for the classification")

class TokenUsage(BaseModel):
    """Token usage details for LLM-based classification."""
    prompt_tokens: int = Field(description="Number of tokens in the prompt")
    completion_tokens: int = Field(description="Number of tokens in the completion")
    total_tokens: int = Field(description="Total number of tokens used")
    contextualization_tokens: Optional[int] = Field(None, description="Number of tokens used for contextualization")

class Documents(BaseModel):
    """List of document types."""
    file_path: str = Field(description="Path to the document")
    document_type: str = Field(description="Type/category of the document")

class ClassificationResponse(BaseModel):
    """Complete classification response from the document analyzer."""
    analyzer_id: str = Field(description="ID of the analyzer used for classification")
    file_path: str = Field(description="Path to the analyzed document")
    total_pages: int = Field(description="Total number of pages in the document")
    total_segments: int = Field(description="Total number of segments identified")
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage details for classification")
    pages: Optional[List[PageClassification]] = Field(None, description="Page-level classification results")
    documents: Optional[List[Documents]] = Field(None, description="DocumentType and the paths")
