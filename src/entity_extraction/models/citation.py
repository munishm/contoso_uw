"""Citation models for tracking extraction sources."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBox(BaseModel):
    """Bounding box coordinates using normalized values (0.0-1.0)."""
    
    x: float = Field(..., ge=0.0, le=1.0, description="X coordinate (left) as percentage of page width")
    y: float = Field(..., ge=0.0, le=1.0, description="Y coordinate (top) as percentage of page height")
    width: float = Field(..., ge=0.0, le=1.0, description="Width as percentage of page width")
    height: float = Field(..., ge=0.0, le=1.0, description="Height as percentage of page height")
    
    @model_validator(mode='after')
    def validate_bounds(self):
        """Ensure bounding box stays within page boundaries."""
        if self.x + self.width > 1.0:
            raise ValueError(f"Bounding box exceeds page width: x={self.x}, width={self.width}")
        if self.y + self.height > 1.0:
            raise ValueError(f"Bounding box exceeds page height: y={self.y}, height={self.height}")
        return self


class Citation(BaseModel):
    """Source location citation for an extracted field value."""
    
    type: str = Field(..., pattern="^(page|bounding_box)$", description="Citation type")
    page: int = Field(..., ge=1, description="Page number (1-indexed)")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates if type is bounding_box")
    text_snippet: Optional[str] = Field(None, max_length=500, description="Text excerpt from citation location")
    
    @model_validator(mode='after')
    def validate_citation(self):
        """Ensure bounding box is provided when type is bounding_box."""
        if self.type == "bounding_box" and self.bbox is None:
            raise ValueError("Bounding box must be provided when citation type is 'bounding_box'")
        if self.type == "page" and self.bbox is not None:
            # Allow bbox for page-level citations but not required
            pass
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "page",
                    "page": 1,
                    "text_snippet": "Account Number: 1234567890"
                },
                {
                    "type": "bounding_box",
                    "page": 2,
                    "bbox": {"x": 0.12, "y": 0.45, "width": 0.08, "height": 0.02},
                    "text_snippet": "Balance: $15,234.56"
                }
            ]
        }
    )
