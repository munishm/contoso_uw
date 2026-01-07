"""
PDF Annotation Service for drawing extraction citations on documents.

Uses PyMuPDF (fitz) to draw bounding boxes on PDFs to visualize
where extracted data came from.
"""

import logging
from typing import Optional

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

logger = logging.getLogger(__name__)


# Color palette for different fields (RGB values 0-1)
FIELD_COLORS = [
    (1.0, 0.0, 0.0),      # Red
    (0.0, 0.5, 1.0),      # Blue
    (0.0, 0.8, 0.0),      # Green
    (1.0, 0.5, 0.0),      # Orange
    (0.6, 0.0, 0.8),      # Purple
    (0.0, 0.7, 0.7),      # Teal
    (1.0, 0.0, 0.5),      # Pink
    (0.5, 0.3, 0.0),      # Brown
    (0.0, 0.4, 0.0),      # Dark Green
    (0.3, 0.3, 0.8),      # Indigo
]

# Colors for specific states
REVIEW_REQUIRED_COLOR = (1.0, 0.8, 0.0)  # Yellow/Amber for review required
LOW_CONFIDENCE_COLOR = (1.0, 0.5, 0.0)    # Orange for low confidence


class PDFAnnotationService:
    """Service for annotating PDFs with extraction citations."""

    def __init__(self):
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF annotation. "
                "Install with: pip install pymupdf"
            )

    def annotate_pdf_with_citations(
        self,
        pdf_content: bytes,
        extraction_fields: list[dict],
        highlight_field: Optional[str] = None,
        show_labels: bool = True,
        confidence_threshold: float = 0.7,
    ) -> bytes:
        """
        Annotate a PDF with bounding boxes from extraction citations.

        Args:
            pdf_content: Original PDF file content as bytes
            extraction_fields: List of extracted fields with citations
            highlight_field: Specific field name to highlight (None for all)
            show_labels: Whether to show field labels on annotations
            confidence_threshold: Below this, show as low confidence

        Returns:
            Annotated PDF content as bytes
        """
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        try:
            field_color_map = {}
            color_index = 0
            
            for field in extraction_fields:
                # Support both 'field_name' and 'name' keys for backward compatibility
                field_name = field.get("field_name") or field.get("name", "")
                citations = field.get("citations", [])
                needs_review = field.get("needs_review", False)
                confidence = field.get("confidence", 0.0)
                value = field.get("value")
                
                # Skip fields without citations or without values
                if not citations or value is None:
                    continue
                
                # Skip if we're only highlighting a specific field
                if highlight_field and field_name != highlight_field:
                    continue
                
                # Assign a consistent color to this field
                if field_name not in field_color_map:
                    field_color_map[field_name] = FIELD_COLORS[color_index % len(FIELD_COLORS)]
                    color_index += 1
                
                # Determine box color based on status
                if needs_review:
                    color = REVIEW_REQUIRED_COLOR
                elif confidence < confidence_threshold:
                    color = LOW_CONFIDENCE_COLOR
                else:
                    color = field_color_map[field_name]
                
                for citation in citations:
                    self._draw_citation_box(
                        doc=doc,
                        citation=citation,
                        field_name=field_name,
                        color=color,
                        show_label=show_labels,
                        needs_review=needs_review,
                        confidence=confidence,
                    )
            
            # Save to bytes
            annotated_content = doc.tobytes(garbage=4, deflate=True)
            logger.info(f"Annotated PDF with {len(field_color_map)} fields")
            return annotated_content
            
        finally:
            doc.close()

    def _draw_citation_box(
        self,
        doc: "fitz.Document",
        citation: dict,
        field_name: str,
        color: tuple[float, float, float],
        show_label: bool = True,
        needs_review: bool = False,
        confidence: float = 1.0,
    ) -> None:
        """
        Draw a single citation bounding box on the PDF.

        Args:
            doc: PyMuPDF document
            citation: Citation data with page and bbox
            field_name: Name of the field for labeling
            color: RGB color tuple (0-1 range)
            show_label: Whether to show field label
            needs_review: Whether field needs review
            confidence: Confidence score
        """
        page_num = citation.get("page", 1) - 1  # Convert to 0-indexed
        bbox_data = citation.get("bbox")
        
        if page_num < 0 or page_num >= len(doc):
            logger.warning(f"Invalid page number {page_num + 1} for field {field_name}")
            return
        
        page = doc[page_num]
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        if bbox_data:
            # Normalized coordinates (0.0-1.0) to page coordinates
            x = bbox_data.get("x", 0) * page_width
            y = bbox_data.get("y", 0) * page_height
            width = bbox_data.get("width", 0) * page_width
            height = bbox_data.get("height", 0) * page_height
            
            # Create rectangle with slight padding
            padding = 2
            rect = fitz.Rect(
                x - padding,
                y - padding,
                x + width + padding,
                y + height + padding
            )
        else:
            # No bbox, highlight a portion of the page as indicator
            logger.debug(f"No bbox for field {field_name} on page {page_num + 1}")
            return
        
        # Draw the rectangle
        # Use semi-transparent fill for highlighting
        fill_color = (*color, 0.15)  # 15% opacity fill
        stroke_color = color
        
        # Draw highlight rectangle
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(
            color=stroke_color,
            fill=stroke_color,
            fill_opacity=0.15,
            width=1.5,
            dashes="[3 2]" if needs_review else None,  # Dashed line for review items
        )
        shape.commit()
        
        # Add label if requested
        if show_label:
            label = self._format_field_label(field_name, confidence, needs_review)
            
            # Position label above or below the box
            label_y = rect.y0 - 12 if rect.y0 > 20 else rect.y1 + 2
            label_point = fitz.Point(rect.x0, label_y)
            
            # Draw label background for readability
            font_size = 8
            text_width = len(label) * font_size * 0.5  # Approximate width
            
            label_bg_rect = fitz.Rect(
                label_point.x - 2,
                label_point.y - font_size,
                label_point.x + text_width + 4,
                label_point.y + 2
            )
            
            # Ensure label background stays within page bounds
            if label_bg_rect.x1 > page_width:
                offset = label_bg_rect.x1 - page_width + 5
                label_bg_rect.x0 -= offset
                label_bg_rect.x1 -= offset
                label_point.x -= offset
            
            # Draw white background for label
            page.draw_rect(label_bg_rect, color=None, fill=(1, 1, 1), fill_opacity=0.9)
            
            # Draw label text
            page.insert_text(
                label_point,
                label,
                fontsize=font_size,
                fontname="helv",
                color=stroke_color,
            )

    def _format_field_label(
        self,
        field_name: str,
        confidence: float,
        needs_review: bool
    ) -> str:
        """Format the label text for a field annotation."""
        # Convert snake_case to Title Case
        display_name = field_name.replace("_", " ").title()
        
        # Truncate long names
        if len(display_name) > 20:
            display_name = display_name[:17] + "..."
        
        # Add confidence indicator
        conf_pct = int(confidence * 100)
        
        if needs_review:
            return f"⚠ {display_name} ({conf_pct}%)"
        return f"{display_name} ({conf_pct}%)"

    def get_field_colors(
        self,
        extraction_fields: list[dict]
    ) -> dict[str, dict]:
        """
        Get the color mapping for all fields.

        Returns a dictionary mapping field names to their colors,
        useful for building a legend in the UI.
        """
        field_colors = {}
        color_index = 0
        
        for field in extraction_fields:
            # Support both 'field_name' and 'name' keys for backward compatibility
            field_name = field.get("field_name") or field.get("name", "")
            if field_name and field_name not in field_colors:
                color = FIELD_COLORS[color_index % len(FIELD_COLORS)]
                field_colors[field_name] = {
                    "color": f"rgb({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)})",
                    "hex": f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}",
                    "needs_review": field.get("needs_review", False),
                }
                color_index += 1
        
        return field_colors


# Global service instance
pdf_annotation_service = PDFAnnotationService() if HAS_PYMUPDF else None
