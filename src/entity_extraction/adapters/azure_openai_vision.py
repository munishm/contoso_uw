"""Azure OpenAI Vision adapter for document extraction."""

import base64
import json
from typing import Any, Dict, List

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

from ..models import Citation, DocumentTypeVersion, BoundingBox
from .base import ExtractionModelAdapter


class AzureOpenAIVisionAdapter(ExtractionModelAdapter):
    """Adapter for Azure OpenAI GPT-4 Vision model."""
    
    def __init__(self, endpoint: str, api_key: str = None, deployment: str = "gpt-4-vision"):
        """
        Initialize Azure OpenAI Vision adapter.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key (if None, uses DefaultAzureCredential)
            deployment: Deployment name
        """
        self.endpoint = endpoint
        self.deployment = deployment
        
        if api_key:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-15-preview"
            )
        else:
            credential = DefaultAzureCredential()
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=lambda: credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                ).token,
                api_version="2024-02-15-preview"
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
        
        prompt = f"""You are a document extraction system. Analyze this document image and extract the following fields:

{chr(10).join(field_descriptions)}

Return a JSON object with this structure:
{{
  "field_name": {{
    "value": extracted_value_or_null,
    "confidence": confidence_score_0_to_1,
    "page": page_number,
    "location": "brief description of where found (e.g., 'top left', 'middle of page')"
  }}
}}

Rules:
1. If a field is not found, set value to null and confidence to 0.0
2. confidence should reflect your certainty (0.0 = uncertain, 1.0 = certain)
3. page should be the 1-indexed page number where the field was found
4. location should describe the approximate position on the page

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
    
    async def extract(
        self,
        document_content: bytes,
        document_type: str,
        schema_version: DocumentTypeVersion,
        field_names: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured data using GPT-4 Vision.
        
        Args:
            document_content: Raw document bytes (PDF converted to images)
            document_type: Type of document
            schema_version: Schema defining extraction
            field_names: Fields to extract
        
        Returns:
            Extraction results dictionary
        """
        # Encode document as base64 for API
        base64_image = base64.b64encode(document_content).decode('utf-8')
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(schema_version, field_names)
        
        # Call GPT-4 Vision
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
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.0  # Deterministic extraction
        )
        
        # Parse JSON response
        content = response.choices[0].message.content
        try:
            # Extract JSON from potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            extraction_data = json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            raise ValueError(f"Failed to parse GPT-4 Vision response: {e}")
        
        # Enhance with citations
        results = {}
        for field_name, field_data in extraction_data.items():
            # Estimate bounding box from location description
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
