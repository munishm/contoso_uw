"""
Common models shared across API endpoints.

These models define standard error responses, pagination, and health check responses.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ValidationErrorDetail(BaseModel):
    """Detail for a single validation error."""

    field: str = Field(..., description="The field that failed validation")
    message: str = Field(..., description="Validation error message")
    code: str = Field(..., description="Error code for programmatic handling")


class ValidationErrorResponse(BaseModel):
    """Validation error response with field-level details."""

    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(..., description="Summary error message")
    details: list[ValidationErrorDetail] = Field(
        default_factory=list, description="List of validation errors"
    )


class HealthResponse(BaseModel):
    """Health check response with service status."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    cosmos_db: str = Field(..., description="Cosmos DB connection status")
    blob_storage: str = Field(..., description="Blob Storage connection status")
    service_bus: str = Field(..., description="Service Bus connection status")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def from_total(cls, total: int, page: int, page_size: int) -> "PaginationMeta":
        """Create pagination metadata from total count."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
