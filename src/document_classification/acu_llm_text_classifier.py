"""ACU + LLM Text classifier implementation."""

import json
import logging
import requests
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .utils.config import Config
from .utils.auth import get_azure_credential, create_token_provider


logger = logging.getLogger(__name__)


class ACULLMTextClassifier:
    """
    Document classifier using ACU for text extraction + LLM for classification.
    
    This approach:
    1. Uses Azure Content Understanding to extract text (OCR)
    2. Sends the extracted text to Azure OpenAI LLM for classification
    """
    
    def __init__(self, config: Config = None):
        """
        Initialize the ACU+LLM text classifier.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or Config()
        self.config.validate()
        
        # Validate OpenAI config
        if not self.config.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required for ACU+LLM method")
        
        # ACU settings for text extraction
        self.cu_endpoint = self.config.CU_ENDPOINT.rstrip('/')
        self.cu_api_version = self.config.CU_API_VERSION
        self.analyzer_id = 'prebuilt-document'
        self._token_provider = create_token_provider(self.config.AZURE_TENANT_ID)
        
        # Get Azure credential for OpenAI
        self._credential = get_azure_credential(self.config.AZURE_TENANT_ID)
        
        self._confidence_threshold = self.config.CONFIDENCE_THRESHOLD
        
        logger.info("ACU+LLM Text Classifier initialized")
    
    def _get_acu_token(self) -> str:
        """Get access token for ACU."""
        return self._token_provider()
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image using ACU."""
        logger.debug(f"Extracting text from: {image_path}")
        
        # Read file
        with open(image_path, 'rb') as f:
            file_data = f.read()
        
        # Submit analyze request
        url = f"{self.cu_endpoint}/contentunderstanding/analyzers/{self.analyzer_id}:analyzeBinary?api-version={self.cu_api_version}"
        access_token = self._get_acu_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream",
            "x-ms-client-request-id": str(uuid.uuid4())
        }
        
        response = requests.post(url, headers=headers, data=file_data, timeout=60)
        
        if response.status_code != 202:
            error_msg = f"ACU analyze failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        op_location = response.headers.get("Operation-Location")
        if not op_location:
            raise RuntimeError("No Operation-Location header in response")
        
        # Poll for results
        start_time = time.time()
        while time.time() - start_time < 180:
            resp = requests.get(op_location, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
            resp.raise_for_status()
            
            data = resp.json()
            status = data.get("status", "").lower()
            
            if status == "succeeded":
                result = data.get("result", {})
                # Extract text from result
                contents = result.get("contents", [])
                if contents:
                    doc = contents[0]
                    markdown = doc.get("markdown")
                    if markdown:
                        return markdown.strip()
                    # Fallback to words
                    pages = doc.get("pages", []) or []
                    words_list = []
                    for page in pages:
                        words = page.get("words", []) or []
                        words_list.extend([w.get("text", "") for w in words])
                    return " ".join(words_list).strip()
                return ""
            elif status in ("failed", "canceled"):
                raise RuntimeError(f"ACU analysis failed with status: {status}")
            
            time.sleep(2)
        
        raise TimeoutError("ACU polling timed out")
    
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
    
    def _classify_with_llm(self, text: str, document_id: str) -> Dict[str, Any]:
        """
        Classify extracted text using LLM.
        
        Args:
            text: Extracted document text
            document_id: Document identifier
            
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

### Document Text:
{text[:1500]}...
"""
        
        try:
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
                        "content": prompt
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
                        "document_id": document_id,
                        "classification": classification,
                        "token_usage": token_usage,
                        "success": True
                    }
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {content}")
                    return {
                        "document_id": document_id,
                        "error": f"Invalid JSON response: {content}",
                        "token_usage": token_usage,
                        "success": False
                    }
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "document_id": document_id,
                    "error": error_msg,
                    "success": False
                }
        except Exception as e:
            logger.exception(f"Error classifying with LLM: {e}")
            return {
                "document_id": document_id,
                "error": f"Exception: {str(e)}",
                "success": False
            }
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document using ACU text extraction + LLM (page by page).
        
        For PDFs, splits into pages and processes each page separately.
        For images, processes as a single page.
        
        Args:
            document: Document dict with 'path' key
            
        Returns:
            Classification result with per-page classifications
        """
        file_path = document.get('path') or document.get('file_path')
        if not file_path:
            raise ValueError("Document must contain 'path' or 'file_path' key")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = Path(file_path).name
        file_ext = Path(file_path).suffix.lower()
        logger.info(f"Classifying document: {file_path}")
        
        # For PDFs, we need to convert to images first to get true page-level extraction
        # This matches the original working notebook approach
        if file_ext == '.pdf':
            logger.debug("PDF detected - converting to page images for true page-level extraction")
            from pdf2image import convert_from_path
            import tempfile
            
            try:
                # Convert PDF to images
                poppler_path = "/opt/homebrew/bin" if Path("/opt/homebrew/bin").exists() else None
                images = convert_from_path(file_path, dpi=150, poppler_path=poppler_path)
                logger.debug(f"Converted PDF to {len(images)} page images")
                
                # Process each page image
                page_classifications = []
                total_tokens = 0
                successful_pages = 0
                total_pages = len(images)
                
                # Create temp directory for page images
                with tempfile.TemporaryDirectory() as temp_dir:
                    for page_num, image in enumerate(images, start=1):
                        # Save page image temporarily
                        page_image_path = Path(temp_dir) / f"page_{page_num}.jpg"
                        image.save(page_image_path, 'JPEG')
                        
                        # Extract text from this page image
                        logger.debug(f"Extracting text from page {page_num}")
                        page_text = self._extract_text_from_image(str(page_image_path))
                        
                        if not page_text or not page_text.strip():
                            logger.warning(f"Page {page_num} has no text, skipping")
                            continue
                        
                        # Classify this page's text
                        llm_result = self._classify_with_llm(page_text, f"{filename}_page_{page_num}")
                        
                        if llm_result['success']:
                            classification = llm_result['classification']
                            page_classifications.append({
                                'page': page_num,
                                'category': classification.get('category', 'Other'),
                                'confidence': classification.get('confidence', 0.0),
                                'reasoning': classification.get('reasoning', ''),
                                'text_length': len(page_text)
                            })
                            total_tokens += llm_result.get('token_usage', {}).get('total_tokens', 0)
                            successful_pages += 1
                        else:
                            logger.warning(f"Failed to classify page {page_num}: {llm_result.get('error')}")
                
            except Exception as e:
                logger.error(f"Error processing PDF: {e}")
                return {
                    'document_type': 'Other',
                    'confidence': 0.0,
                    'alternatives': [],
                    'page_classifications': [],
                    'error': f'Failed to process PDF: {str(e)}',
                    'metadata': {
                        'file_path': file_path,
                        'filename': filename,
                        'method': 'acu_llm_text',
                        'total_pages': 0,
                        'successful_pages': 0
                    }
                }
        else:
            # For non-PDF files (images), process as a single page
            logger.debug("Image file detected - processing as single page")
            page_text = self._extract_text_from_image(file_path)
            
            if not page_text or not page_text.strip():
                return {
                    'document_type': 'Other',
                    'confidence': 0.0,
                    'alternatives': [],
                    'page_classifications': [],
                    'error': 'No text extracted from document',
                    'metadata': {
                        'file_path': file_path,
                        'filename': filename,
                        'method': 'acu_llm_text',
                        'total_pages': 1,
                        'successful_pages': 0
                    }
                }
            
            llm_result = self._classify_with_llm(page_text, filename)
            
            if not llm_result['success']:
                return {
                    'document_type': 'Other',
                    'confidence': 0.0,
                    'alternatives': [],
                    'page_classifications': [],
                    'error': llm_result.get('error', 'Classification failed'),
                    'metadata': {
                        'file_path': file_path,
                        'filename': filename,
                        'method': 'acu_llm_text',
                        'total_pages': 1,
                        'successful_pages': 0
                    }
                }
            
            classification = llm_result['classification']
            page_classifications = [{
                'page': 1,
                'category': classification.get('category', 'Other'),
                'confidence': classification.get('confidence', 0.0),
                'reasoning': classification.get('reasoning', ''),
                'text_length': len(page_text)
            }]
            total_tokens = llm_result.get('token_usage', {}).get('total_tokens', 0)
            successful_pages = 1
            total_pages = 1
        
        # Check if we got any results
        if not page_classifications:
            return {
                'document_type': 'Other',
                'confidence': 0.0,
                'alternatives': [],
                'page_classifications': [],
                'error': 'Failed to classify any pages',
                'metadata': {
                    'file_path': file_path,
                    'filename': filename,
                    'method': 'acu_llm_text',
                    'total_pages': total_pages if 'total_pages' in locals() else 0,
                    'successful_pages': 0
                }
            }
        
        # Aggregate results: most common category
        from collections import Counter
        categories = [p['category'] for p in page_classifications]
        most_common_category = Counter(categories).most_common(1)[0][0]
        
        # Average confidence for the most common category
        category_confidences = [p['confidence'] for p in page_classifications if p['category'] == most_common_category]
        avg_confidence = sum(category_confidences) / len(category_confidences) if category_confidences else 0.0
        
        logger.info(f"Classified as: {most_common_category} (avg confidence: {avg_confidence:.3f})")
        
        result = {
            'document_type': most_common_category,
            'confidence': avg_confidence,
            'alternatives': [],
            'page_classifications': page_classifications,
            'metadata': {
                'file_path': file_path,
                'filename': filename,
                'method': 'acu_llm_text',
                'total_pages': total_pages,
                'successful_pages': successful_pages,
                'total_tokens': total_tokens,
                'token_usage': {
                    'total_tokens': total_tokens,
                    'prompt_tokens': 0,  # Not tracked per-page
                    'completion_tokens': 0
                }
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
                        'method': 'acu_llm_text'
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
        output_file = self.config.OUTPUT_DIR / f"acu_llm_text_results_{timestamp}.json"
        
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
