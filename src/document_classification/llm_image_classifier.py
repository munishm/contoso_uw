"""ACU + LLM Image classifier implementation."""

import base64
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .utils.config import Config
from .utils.auth import get_azure_credential
from pdf2image import convert_from_path


logger = logging.getLogger(__name__)


class LLMImageClassifier:
    """
    Document classifier using LLM with image input (GPT-4 Vision).
    
    This approach:
    1. Converts PDF pages to images
    2. Sends images directly to GPT-4 Vision for classification
    """
    
    def __init__(self, config: Config = None):
        """
        Initialize the ACU+LLM image classifier.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or Config()
        self.config.validate()
        
        # Validate OpenAI config
        if not self.config.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required for ACU+LLM image method")
        
        # PDF conversion settings
        self.dpi = 300
        self.poppler_path = "/opt/homebrew/bin" if Path("/opt/homebrew/bin").exists() else None
        
        # Get Azure credential for OpenAI
        self._credential = get_azure_credential(self.config.AZURE_TENANT_ID)
        
        self._confidence_threshold = self.config.CONFIDENCE_THRESHOLD
        
        # Temporary directory for images
        self._temp_image_dir = self.config.OUTPUT_DIR / "temp_images"
        self._temp_image_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ACU+LLM Image Classifier initialized")
    
    def _convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Convert a PDF file to individual page images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            
        Returns:
            List of paths to the generated images
        """
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        # Create output directory
        pdf_name = Path(pdf_path).stem
        page_dir = Path(output_dir) / pdf_name
        page_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert PDF to images
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                poppler_path=self.poppler_path
            )
            
            image_paths = []
            for i, image in enumerate(images, start=1):
                image_path = page_dir / f"page_{i}.jpg"
                image.save(str(image_path), 'JPEG')
                image_paths.append(str(image_path))
                logger.debug(f"Saved page {i} to {image_path}")
            
            logger.info(f"Converted PDF to {len(image_paths)} images")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise RuntimeError(f"Failed to convert PDF: {e}")
    
    def _get_openai_token(self) -> str:
        """Get access token for Azure OpenAI."""
        try:
            token = self._credential.get_token(
                "https://cognitiveservices.azure.com/.default",
                tenant_id=self.config.AZURE_TENANT_ID
            )
        except TypeError:
            token = self._credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
        return token.token
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _classify_image_with_llm(self, image_path: str, page_number: int) -> Dict[str, Any]:
        """
        Classify a single image using GPT-4 Vision.
        
        Args:
            image_path: Path to the image file
            page_number: Page number being classified
            
        Returns:
            Classification result from LLM
        """
        # Build category descriptions
        categories_text = "\n\n".join([
            f"{i+1}. **{name}**\n   {desc}"
            for i, (name, desc) in enumerate(self.config.DOCUMENT_CATEGORIES.items())
        ])
        
        prompt = f"""You are an expert insurance document classifier.

Classify the document into EXACTLY ONE of the following categories:

{categories_text}

### Classification Rules (IMPORTANT)
- If the document contains **test values and lab measurements → Lab Report**
- If it contains **diagnostic imaging results or medical findings → Medical Report**
- If it is a **doctor-written narrative or consultation note → Medical Letter**
- Choose the **most specific category**, especially for medical documents

### Response Format (STRICT)
Respond with ONLY valid JSON:
{{"category": "category_name", "confidence": 0.00-1.00, "reasoning": "Brief explanation"}}
"""
        
        try:
            # Encode image
            base64_image = self._encode_image(image_path)
            
            access_token = self._get_openai_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            endpoint = self.config.AZURE_OPENAI_ENDPOINT.strip('"')
            deployment = self.config.AZURE_OPENAI_DEPLOYMENT
            api_version = self.config.AZURE_OPENAI_API_VERSION
            
            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a document classifier. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.1
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Extract token usage
                usage = result.get("usage", {})
                token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
                
                try:
                    classification = json.loads(content)
                    return {
                        "page_number": page_number,
                        "classification": classification,
                        "token_usage": token_usage,
                        "success": True
                    }
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {content}")
                    return {
                        "page_number": page_number,
                        "error": f"Invalid JSON response: {content}",
                        "token_usage": token_usage,
                        "success": False
                    }
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "page_number": page_number,
                    "error": error_msg,
                    "success": False
                }
        except Exception as e:
            logger.exception(f"Error classifying image: {e}")
            return {
                "page_number": page_number,
                "error": f"Exception: {str(e)}",
                "success": False
            }
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document using image-based LLM classification.
        
        Args:
            document: Document dict with 'path' key
            
        Returns:
            Classification result
        """
        file_path = document.get('path') or document.get('file_path')
        if not file_path:
            raise ValueError("Document must contain 'path' or 'file_path' key")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = Path(file_path).name
        logger.info(f"Classifying document: {file_path}")
        
        # Step 1: Convert PDF to images
        logger.debug("Converting PDF to images...")
        try:
            image_paths = self._convert_pdf_to_images(
                file_path,
                str(self._temp_image_dir)
            )
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            return {
                'document_type': 'Other',
                'confidence': 0.0,
                'alternatives': [],
                'error': f'PDF conversion failed: {str(e)}',
                'metadata': {
                    'file_path': file_path,
                    'filename': filename,
                    'method': 'llm_image'
                }
            }
        
        logger.debug(f"Converted to {len(image_paths)} images")
        
        # Step 2: Classify each page/image
        page_results = []
        total_tokens = 0
        
        for i, image_path in enumerate(image_paths, 1):
            logger.debug(f"Classifying page {i}/{len(image_paths)}...")
            result = self._classify_image_with_llm(image_path, i)
            page_results.append(result)
            
            if result.get('success'):
                token_usage = result.get('token_usage', {})
                total_tokens += token_usage.get('total_tokens', 0)
        
        # Determine overall classification (most common category from pages)
        successful_results = [r for r in page_results if r.get('success')]
        
        if not successful_results:
            return {
                'document_type': 'Other',
                'confidence': 0.0,
                'alternatives': [],
                'error': 'All page classifications failed',
                'metadata': {
                    'file_path': file_path,
                    'filename': filename,
                    'method': 'llm_image',
                    'total_pages': len(image_paths)
                }
            }
        
        # Get most common category
        categories = [r['classification']['category'] for r in successful_results]
        from collections import Counter
        category_counts = Counter(categories)
        primary_category = category_counts.most_common(1)[0][0]
        
        # Average confidence for primary category
        primary_confidences = [
            r['classification']['confidence']
            for r in successful_results
            if r['classification']['category'] == primary_category
        ]
        avg_confidence = sum(primary_confidences) / len(primary_confidences)
        
        logger.info(f"Classified as: {primary_category} (confidence: {avg_confidence:.3f})")
        
        result = {
            'document_type': primary_category,
            'confidence': avg_confidence,
            'alternatives': [],
            'page_classifications': [
                {
                    'page': r['page_number'],
                    'category': r['classification']['category'],
                    'confidence': r['classification']['confidence']
                }
                for r in successful_results
            ],
            'metadata': {
                'file_path': file_path,
                'filename': filename,
                'method': 'llm_image',
                'total_pages': len(image_paths),
                'successful_pages': len(successful_results),
                'total_tokens': total_tokens
            }
        }
        
        # Save result if configured
        if self.config.SAVE_RESULTS:
            self._save_results([result])
        
        return result
    
    def classify_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple documents.
        
        Args:
            documents: List of document dicts
            
        Returns:
            List of classification results
        """
        results = []
        
        for doc in documents:
            try:
                result = self.classify(doc)
                result['status'] = 'success'
            except Exception as e:
                logger.error(f"Error classifying {doc.get('path', 'unknown')}: {e}")
                result = {
                    'document_type': 'Other',
                    'confidence': 0.0,
                    'alternatives': [],
                    'error': str(e),
                    'status': 'error',
                    'metadata': {
                        'file_path': doc.get('path', 'unknown'),
                        'method': 'llm_image'
                    }
                }
            
            results.append(result)
        
        # Save results if configured
        if self.config.SAVE_RESULTS and results:
            self._save_results(results)
        
        return results
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """Save classification results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.OUTPUT_DIR / f"llm_image_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
    
    def get_document_types(self) -> List[str]:
        """Get list of possible document types."""
        return list(self.config.DOCUMENT_CATEGORIES.keys())
    
    def set_confidence_threshold(self, threshold: float):
        """Set minimum confidence threshold for classification."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self._confidence_threshold = threshold
    
    @property
    def confidence_threshold(self) -> float:
        """Get current confidence threshold."""
        return self._confidence_threshold
