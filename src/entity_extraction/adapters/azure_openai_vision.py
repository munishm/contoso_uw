"""Azure OpenAI Vision adapter for document extraction."""

import base64
import io
import json
from typing import Any, Dict, List, Tuple

from openai import AzureOpenAI, BadRequestError
from azure.identity import DefaultAzureCredential
from PIL import Image

from ..models import Citation, DocumentTypeVersion, BoundingBox
from .base import ExtractionModelAdapter

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class AzureOpenAIVisionAdapter(ExtractionModelAdapter):
    """Adapter for Azure OpenAI GPT-4 Vision model."""
    
    def __init__(self, endpoint: str, api_key: str = None, deployment: str = "gpt-4-vision", api_version: str = "2024-02-15-preview"):
        """
        Initialize Azure OpenAI Vision adapter.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key (if None, uses DefaultAzureCredential)
            deployment: Deployment name
            api_version: Azure OpenAI API version
        """
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version
        
        if api_key:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
        else:
            credential = DefaultAzureCredential()
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=lambda: credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                ).token,
                api_version=api_version
            )
    
    def _build_extraction_prompt(
        self,
        schema_version: DocumentTypeVersion,
        field_names: List[str]
    ) -> str:
        """
        Build schema-aware prompt for field extraction.
        
        Args:
            schema_version: Schema defining fields to extract
            field_names: Specific fields to extract
        
        Returns:
            Formatted prompt string
        """
        input_schema = schema_version.input_schema
        properties = input_schema.get("properties", {})
        
        # Filter properties if specific fields requested
        if "*" not in field_names:
            properties = {k: v for k, v in properties.items() if k in field_names}
        
        field_descriptions = []
        for field_name, field_spec in properties.items():
            field_type = field_spec.get("type", "string")
            description = field_spec.get("description", "")
            hints = field_spec.get("extraction_hints", [])
            
            field_desc = f"- {field_name} ({field_type}): {description}"
            if hints:
                field_desc += f"\n  Hints: {', '.join(hints)}"
            field_descriptions.append(field_desc)
        
        prompt = f"""You are a document extraction system with precise visual grounding. Analyze this document image and extract the following fields:

{chr(10).join(field_descriptions)}

Return a JSON object with this structure:
{{
  "field_name": {{
    "value": extracted_value_or_null,
    "confidence": confidence_score_0_to_1,
    "page": page_number,
    "bbox": {{
      "x": normalized_x_position_0_to_1,
      "y": normalized_y_position_0_to_1,
      "width": normalized_width_0_to_1,
      "height": normalized_height_0_to_1
    }}
  }}
}}

Rules:
1. If a field is not found, set value to null and confidence to 0.0
2. confidence should reflect your certainty (0.0 = uncertain, 1.0 = certain)
3. page should be the 1-indexed page number where the field was found
4. bbox coordinates are CRITICAL - they must accurately locate the extracted value:
   - x: horizontal position from left edge (0.0 = left edge, 1.0 = right edge)
   - y: vertical position from top edge (0.0 = top edge, 1.0 = bottom edge)
   - width: width of the field value text (typically 0.1 to 0.4)
   - height: height of the field value text (typically 0.02 to 0.05)
   - The bbox should tightly bound the actual VALUE text, not the field label
5. Be precise with bbox - look at where the actual value text appears on the page

Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _estimate_bounding_box(
        self,
        location_description: str,
        page: int
    ) -> BoundingBox:
        """
        Estimate bounding box from GPT-4 Vision's spatial description.
        
        Args:
            location_description: Text description of location (e.g., "top left")
            page: Page number
        
        Returns:
            Estimated bounding box with normalized coordinates
        """
        # Simple heuristic mapping of location descriptions to coordinates
        # In production, this would use visual grounding API or more sophisticated parsing
        location_lower = location_description.lower()
        
        # Default to center if no clear indicator
        x, y = 0.4, 0.4
        width, height = 0.2, 0.05
        
        if "top" in location_lower:
            y = 0.1
        elif "bottom" in location_lower:
            y = 0.8
        elif "middle" in location_lower or "center" in location_lower:
            y = 0.45
        
        if "left" in location_lower:
            x = 0.1
        elif "right" in location_lower:
            x = 0.7
        elif "center" in location_lower:
            x = 0.4
        
        return BoundingBox(x=x, y=y, width=width, height=height)
    
    def _convert_pdf_to_images(self, pdf_content: bytes, max_size_mb: float = 5.0) -> List[Tuple[int, str]]:
        """
        Convert PDF to list of page images.
        
        Args:
            pdf_content: Raw PDF bytes
            max_size_mb: Maximum size per image in MB (for compression)
        
        Returns:
            List of (page_number, base64_image) tuples
        """
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF processing. "
                "Install with: pip install pymupdf"
            )
        
        page_images = []
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image at 150 DPI (good balance of quality and size)
                pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Compress if needed
                output = io.BytesIO()
                img.save(output, format='PNG', optimize=True)
                img_bytes = output.getvalue()
                
                # Check size and compress more if needed
                img_size_mb = len(img_bytes) / (1024 * 1024)
                if img_size_mb > max_size_mb:
                    # Try JPEG with quality reduction
                    output = io.BytesIO()
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    quality = 85
                    while img_size_mb > max_size_mb and quality > 30:
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=quality, optimize=True)
                        img_bytes = output.getvalue()
                        img_size_mb = len(img_bytes) / (1024 * 1024)
                        quality -= 10
                
                # Encode to base64
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                page_images.append((page_num + 1, base64_image))  # 1-indexed page numbers
                
                print(f"  Page {page_num + 1}: {img_size_mb:.2f} MB")
        
        finally:
            pdf_document.close()
        
        return page_images
    
    def _is_pdf(self, content: bytes) -> bool:
        """Check if content is a PDF file."""
        return content[:4] == b'%PDF'
    
    async def _extract_from_image(
        self,
        base64_image: str,
        prompt: str,
        page_number: int = 1
    ) -> Dict[str, Any]:
        """
        Extract data from a single image.
        
        Args:
            base64_image: Base64 encoded image
            prompt: Extraction prompt
            page_number: Page number for citation
        
        Returns:
            Extraction results dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.0
            )
        except BadRequestError as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    error_message = json.dumps(error_body, indent=2)
                except:
                    error_message = e.response.text if hasattr(e.response, 'text') else str(e)
            
            raise ValueError(
                f"Azure OpenAI API error on page {page_number}: Bad Request (400)\n"
                f"Error details: {error_message}\n"
                f"Deployment: {self.deployment}, Endpoint: {self.endpoint}, API Version: {self.api_version}"
            )
        except Exception as e:
            raise ValueError(
                f"Azure OpenAI API error on page {page_number}: {str(e)}. "
                f"Deployment: {self.deployment}, Endpoint: {self.endpoint}, API Version: {self.api_version}"
            )
        
        # Parse JSON response
        content = response.choices[0].message.content
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            extraction_data = json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            raise ValueError(f"Failed to parse GPT-4 Vision response on page {page_number}: {e}")
        
        return extraction_data
    
    def _merge_extraction_results(
        self,
        page_results: List[Tuple[int, Dict[str, Any]]],
        schema_version: DocumentTypeVersion
    ) -> Dict[str, Any]:
        """
        Merge extraction results from multiple pages.
        
        Strategy: For each field, take the result with highest confidence,
        or concatenate multi-page fields.
        
        Args:
            page_results: List of (page_number, extraction_data) tuples
            schema_version: Schema version for citation level
        
        Returns:
            Merged extraction results
        """
        merged = {}
        
        for page_num, extraction_data in page_results:
            for field_name, field_data in extraction_data.items():
                value = field_data.get("value")
                confidence = field_data.get("confidence", 0.0)
                
                if value is None:
                    continue
                
                # Use actual bbox from response if available, otherwise fall back to estimation
                bbox_data = field_data.get("bbox")
                if bbox_data and isinstance(bbox_data, dict):
                    # Use actual coordinates from GPT-4 Vision response
                    bbox = BoundingBox(
                        x=float(bbox_data.get("x", 0.4)),
                        y=float(bbox_data.get("y", 0.4)),
                        width=float(bbox_data.get("width", 0.2)),
                        height=float(bbox_data.get("height", 0.05))
                    )
                else:
                    # Fall back to estimation from location description (legacy support)
                    location_desc = field_data.get("location", "unknown")
                    bbox = self._estimate_bounding_box(location_desc, page_num)
                
                citation = Citation(
                    type="bounding_box" if schema_version.citation_level.value in ["bounding_box", "both"] else "page",
                    page=page_num,
                    bbox=bbox if schema_version.citation_level.value in ["bounding_box", "both"] else None,
                    text_snippet=str(value)[:500] if value else None
                )
                
                # Merge logic: keep highest confidence, but collect all citations
                if field_name not in merged:
                    merged[field_name] = {
                        "value": value,
                        "confidence": confidence,
                        "citations": [citation]
                    }
                else:
                    # If this has higher confidence, replace value but keep all citations
                    if confidence > merged[field_name]["confidence"]:
                        merged[field_name]["value"] = value
                        merged[field_name]["confidence"] = confidence
                    
                    # Always add citation
                    merged[field_name]["citations"].append(citation)
        
        return merged
    
    async def extract(
        self,
        document_content: bytes,
        document_type: str,
        schema_version: DocumentTypeVersion,
        field_names: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data using GPT-4 Vision.
        Automatically handles PDF by converting to per-page images.
        
        Args:
            document_content: Raw document bytes (PDF or image)
            document_type: Type of document
            schema_version: Schema defining extraction
            field_names: Fields to extract
        
        Returns:
            Extraction results dictionary
        """
        doc_size_mb = len(document_content) / (1024 * 1024)
        print(f"Document size: {doc_size_mb:.2f} MB")
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(schema_version, field_names)
        prompt_size_kb = len(prompt) / 1024
        print(f"Prompt size: {prompt_size_kb:.2f} KB")
        
        # Check if PDF and convert to images
        if self._is_pdf(document_content):
            print(f"PDF detected, converting to per-page images...")
            page_images = self._convert_pdf_to_images(document_content, max_size_mb=5.0)
            print(f"Converted to {len(page_images)} page(s)")
        else:
            # Single image - encode directly
            if doc_size_mb > 20:
                raise ValueError(
                    f"Image size ({doc_size_mb:.2f} MB) exceeds Azure OpenAI Vision limit of 20 MB"
                )
            base64_image = base64.b64encode(document_content).decode('utf-8')
            page_images = [(1, base64_image)]
            print(f"Single image document")
        
        # Extract from each page
        page_results = []
        for page_num, base64_image in page_images:
            print(f"Extracting from page {page_num}...")
            extraction_data = await self._extract_from_image(base64_image, prompt, page_num)
            page_results.append((page_num, extraction_data))
        
        # Merge results from all pages
        if len(page_results) == 1:
            # Single page - enhance with citations
            extraction_data = page_results[0][1]
            results = {}
            for field_name, field_data in extraction_data.items():
                location_desc = field_data.get("location", "unknown")
                page = field_data.get("page", 1)
                
                bbox = self._estimate_bounding_box(location_desc, page)
                
                citation = Citation(
                    type="bounding_box" if schema_version.citation_level.value in ["bounding_box", "both"] else "page",
                    page=page,
                    bbox=bbox if schema_version.citation_level.value in ["bounding_box", "both"] else None,
                    text_snippet=field_data.get("value", "")[:500] if field_data.get("value") else None
                )
                
                results[field_name] = {
                    "value": field_data.get("value"),
                    "confidence": field_data.get("confidence", 0.5),
                    "citations": [citation] if field_data.get("value") is not None else []
                }
            return results
        else:
            # Multi-page - merge results
            print(f"Merging results from {len(page_results)} pages...")
            return self._merge_extraction_results(page_results, schema_version)
    
    def get_confidence(self, extraction_result: Dict[str, Any], field_name: str) -> float:
        """Get confidence score for a field."""
        field_data = extraction_result.get(field_name, {})
        return field_data.get("confidence", 0.0)
    
    def supports_document_type(self, document_type: str) -> bool:
        """GPT-4 Vision supports all document types."""
        return True
    
    def get_model_metadata(self) -> Dict[str, Any]:
        """Get model metadata."""
        return {
            "name": "azure_gpt4_vision",
            "version": self.deployment,
            "type": "vision",
            "capabilities": ["ocr", "structured_extraction", "spatial_understanding"]
        }
