"""ACU + LLM Text classifier implementation."""

import base64
import json
import logging
import requests
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from pdf2image import convert_from_path
from .utils.config import Config
from .utils.auth import get_azure_credential, create_token_provider


logger = logging.getLogger(__name__)


class ACULLMTextClassifier:
    """
    Document classifier using PDF to image conversion + ACU for text extraction + LLM for classification.
    
    This approach:
    1. Converts PDF pages to images
    2. Uses Azure Content Understanding to extract text from each image (OCR)
    3. Stores extracted text in JSON format
    4. Sends each page's text to Azure OpenAI LLM for classification
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
        
        # PDF to image conversion settings
        self.dpi = 300
        self.poppler_path = "/opt/homebrew/bin" if Path("/opt/homebrew/bin").exists() else None
        
        # Temporary directory for images
        self._temp_image_dir = self.config.OUTPUT_DIR / "temp_images"
        self._temp_image_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ACU+LLM Text Classifier initialized with PDF to image conversion")
    
    def _get_acu_token(self) -> str:
        """Get access token for ACU."""
        return self._token_provider()
    
    def _convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> tuple[List[str], float]:
        """
        Convert a PDF file to individual page images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the images
            
        Returns:
            Tuple of (list of paths to the generated images, conversion time)
        """
        conversion_start_time = time.time()
        logger.debug(f"Converting PDF to images: {pdf_path}")
        
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
            
            conversion_duration = time.time() - conversion_start_time
            logger.info(f"Converted PDF to {len(image_paths)} images in {conversion_duration:.2f}s")
            return image_paths, conversion_duration
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise RuntimeError(f"Failed to convert PDF: {e}")
    
    def _extract_text_from_image(self, image_path: str, page_number: int) -> Dict[str, Any]:
        """
        Extract text from a single image using ACU.
        
        Args:
            image_path: Path to the image file
            page_number: Page number for logging
            
        Returns:
            Dictionary with extracted text and metadata
        """
        ocr_start_time = time.time()
        logger.debug(f"Starting OCR extraction from image: {Path(image_path).name}")
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Submit analyze request
        url = f"{self.cu_endpoint}/contentunderstanding/analyzers/{self.analyzer_id}:analyzeBinary?api-version={self.cu_api_version}"
        access_token = self._get_acu_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream",
            "x-ms-client-request-id": str(uuid.uuid4())
        }
        
        response = requests.post(url, headers=headers, data=image_data, timeout=60)
        
        if response.status_code != 202:
            error_msg = f"ACU analyze failed for page {page_number}: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                "page_number": page_number,
                "text": "",
                "word_count": 0,
                "error": error_msg,
                "ocr_duration": 0
            }
        
        op_location = response.headers.get("Operation-Location")
        if not op_location:
            error_msg = f"No Operation-Location header for page {page_number}"
            return {
                "page_number": page_number,
                "text": "",
                "word_count": 0,
                "error": error_msg,
                "ocr_duration": 0
            }
        
        # Poll for results
        start_time = time.time()
        while time.time() - start_time < 180:
            resp = requests.get(op_location, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
            resp.raise_for_status()
            
            data = resp.json()
            status = data.get("status", "").lower()
            
            if status == "succeeded":
                result = data.get("result", {})
                ocr_duration = time.time() - ocr_start_time
                
                # Extract text from ACU result
                extracted_text = self._extract_text_from_acu_result(result)
                
                logger.info(f"OCR extraction completed for page {page_number} in {ocr_duration:.2f}s")
                return {
                    "page_number": page_number,
                    "text": extracted_text,
                    "word_count": len(extracted_text.split()) if extracted_text else 0,
                    "image_path": image_path,
                    "ocr_duration": ocr_duration
                }
                
            elif status in ("failed", "canceled"):
                error_msg = f"ACU analysis failed for page {page_number} with status: {status}"
                logger.error(error_msg)
                return {
                    "page_number": page_number,
                    "text": "",
                    "word_count": 0,
                    "error": error_msg,
                    "ocr_duration": time.time() - ocr_start_time
                }
            
            time.sleep(2)
        
        # Timeout
        error_msg = f"ACU polling timed out for page {page_number}"
        logger.error(error_msg)
        return {
            "page_number": page_number,
            "text": "",
            "word_count": 0,
            "error": error_msg,
            "ocr_duration": time.time() - ocr_start_time
        }
    
    def _extract_text_from_acu_result(self, acu_result: Dict[str, Any]) -> str:
        """
        Extract text content from ACU result.
        
        Args:
            acu_result: ACU analysis result
            
        Returns:
            Extracted text as string
        """
        try:
            # Try to get text from markdown first
            contents = acu_result.get("contents", [])
            if contents:
                doc = contents[0]
                markdown = doc.get("markdown", "")
                if markdown and markdown.strip():
                    return markdown.strip()
                
                # Try pages if no markdown
                pages = doc.get("pages", [])
                if pages:
                    page_texts = []
                    for page in pages:
                        # Try lines first
                        lines = page.get("lines", [])
                        if lines:
                            line_texts = [line.get("text", "").strip() for line in lines if line.get("text")]
                            page_text = "\n".join(line_texts)
                        else:
                            # Fallback to words
                            words = page.get("words", [])
                            word_texts = [w.get("text", "") for w in words if w.get("text")]
                            page_text = " ".join(word_texts)
                        
                        if page_text.strip():
                            page_texts.append(page_text.strip())
                    
                    return "\n\n".join(page_texts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from ACU result: {e}")
            return ""
    
    def _process_pdf_to_json(self, pdf_path: str) -> tuple[List[Dict[str, Any]], float, float]:
        """
        Convert PDF to images, extract text from each image, and store in JSON format.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (list of page data dictionaries, conversion time, total OCR time)
        """
        logger.info(f"Processing PDF to JSON: {Path(pdf_path).name}")
        
        # Step 1: Convert PDF to images
        image_paths, conversion_time = self._convert_pdf_to_images(pdf_path, str(self._temp_image_dir))
        
        # Step 2: Extract text from each image and store in JSON format
        page_data = []
        total_ocr_time = 0.0
        
        for i, image_path in enumerate(image_paths, start=1):
            logger.info(f"Extracting text from page {i}/{len(image_paths)}")
            page_info = self._extract_text_from_image(image_path, i)
            page_data.append(page_info)
            total_ocr_time += page_info.get('ocr_duration', 0)
        
        logger.info(f"Completed text extraction from {len(page_data)} pages")
        return page_data, conversion_time, total_ocr_time
    
    def _classify_page_with_llm(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single page's text using LLM.
        
        Args:
            page_data: Dictionary containing page text and metadata
            
        Returns:
            Classification result from LLM
        """
        page_number = page_data['page_number']
        page_text = page_data.get('text', '')
        
        if not page_text.strip():
            return {
                'page_number': page_number,
                'document_type': 'Other',
                'confidence': 0.0,
                'reasoning': 'No text found on page',
                'error': 'Empty text'
            }
        
        llm_start_time = time.time()
        logger.debug(f"Starting LLM classification for page {page_number}")
        
        # Build category descriptions
        categories_text = "\\n\\n".join([
            f"{i+1}. **{name}**\\n   {desc}"
            for i, (name, desc) in enumerate(self.config.DOCUMENT_CATEGORIES.items())
        ])
        
        prompt = f"""You are an expert insurance document classifier analyzing page {page_number} of a document.

Classify this page into EXACTLY ONE of the following categories:

{categories_text}

### Classification Rules (IMPORTANT)
- If the page contains **test values and lab measurements → Lab Report**
- If it contains **diagnostic imaging results or medical findings → Medical Report**
- If it is a **doctor-written narrative or consultation note → Medical Letter**
- Choose the **most specific category**, especially for medical documents

### Response Format (STRICT)
```json
{{
    "document_type": "Category Name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this category was chosen"
}}
```

**Page {page_number} Content:**
{page_text[:4000]}{"..." if len(page_text) > 4000 else ""}
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self._get_openai_token()}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": "You are an expert insurance document classifier. Always respond with valid JSON format as requested."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.1,
                "top_p": 0.1
            }
            
            url = f"{self.config.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.config.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={self.config.AZURE_OPENAI_API_VERSION}"
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract token usage
            usage = result.get("usage", {})
            token_usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
            
            # Parse JSON response
            if content.strip().startswith("```json"):
                content = content.strip()[7:]
            if content.strip().endswith("```"):
                content = content.strip()[:-3]
            
            classification = json.loads(content.strip())
            
            # Add timing, page info, and token usage
            llm_duration = time.time() - llm_start_time
            classification["page_number"] = page_number
            classification["llm_duration"] = llm_duration
            classification["text_length"] = len(page_text)
            classification["token_usage"] = token_usage
            
            logger.info(f"Page {page_number} classified as '{classification.get('document_type')}' with confidence {classification.get('confidence'):.2f} in {llm_duration:.2f}s")
            return classification
            
        except Exception as e:
            logger.error(f"LLM classification failed for page {page_number}: {e}")
            return {
                "page_number": page_number,
                "document_type": "Other",
                "confidence": 0.0,
                "reasoning": f"Classification failed: {str(e)}",
                "error": str(e),
                "llm_duration": time.time() - llm_start_time
            }
    
    def _aggregate_page_classifications(self, page_classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate page-level classifications into document-level result.
        
        Args:
            page_classifications: List of page classification results
            
        Returns:
            Aggregated document classification result
        """
        if not page_classifications:
            return {
                "document_type": "Other",
                "confidence": 0.0,
                "reasoning": "No pages to classify"
            }
        
        # Count document types across pages
        type_counts = {}
        confidence_sums = {}
        
        for page_result in page_classifications:
            doc_type = page_result.get("document_type", "Other")
            confidence = page_result.get("confidence", 0.0)
            
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            confidence_sums[doc_type] = confidence_sums.get(doc_type, 0.0) + confidence
        
        # Find the most common document type
        most_common_type = max(type_counts.items(), key=lambda x: x[1])
        winning_type = most_common_type[0]
        winning_count = most_common_type[1]
        
        # Calculate average confidence for the winning type
        avg_confidence = confidence_sums[winning_type] / winning_count
        
        # Calculate consensus strength
        total_pages = len(page_classifications)
        consensus_ratio = winning_count / total_pages
        
        # Adjust final confidence based on consensus
        final_confidence = avg_confidence * consensus_ratio
        
        # Aggregate token usage across all pages
        total_token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        for page_result in page_classifications:
            page_tokens = page_result.get("token_usage", {})
            total_token_usage["prompt_tokens"] += page_tokens.get("prompt_tokens", 0)
            total_token_usage["completion_tokens"] += page_tokens.get("completion_tokens", 0)
            total_token_usage["total_tokens"] += page_tokens.get("total_tokens", 0)
        
        return {
            "document_type": winning_type,
            "confidence": round(final_confidence, 3),
            "reasoning": f"Consensus classification: {winning_count}/{total_pages} pages classified as '{winning_type}'",
            "token_usage": total_token_usage,
            "page_consensus": {
                "total_pages": total_pages,
                "winning_pages": winning_count,
                "consensus_ratio": round(consensus_ratio, 3),
                "type_distribution": type_counts
            },
            "page_classifications": page_classifications
        }
    
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
        llm_start_time = time.time()
        logger.debug(f"Starting LLM classification for: {document_id}")
        
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
            llm_duration = time.time() - llm_start_time
            
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
                    logger.info(f"LLM classification completed in {llm_duration:.2f}s for {document_id}")
                    return {
                        "document_id": document_id,
                        "classification": classification,
                        "token_usage": token_usage,
                        "llm_duration": llm_duration,
                        "success": True
                    }
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {content}")
                    return {
                        "document_id": document_id,
                        "error": f"Invalid JSON response: {content}",
                        "token_usage": token_usage,
                        "llm_duration": llm_duration,
                        "success": False
                    }
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "document_id": document_id,
                    "error": error_msg,
                    "llm_duration": llm_duration,
                    "success": False
                }
        except Exception as e:
            llm_duration = time.time() - llm_start_time
            logger.exception(f"Error classifying with LLM: {e}")
            return {
                "document_id": document_id,
                "error": f"Exception: {str(e)}",
                "llm_duration": llm_duration,
                "success": False
            }
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document using the new workflow:
        1. Convert PDF to images
        2. Extract text from each image using ACU
        3. Put extracted text to JSON
        4. Iterate over JSON and send each object to LLM for classification
        
        Args:
            document: Document object with 'path' key
            
        Returns:
            Classification result
        """
        start_time = time.time()
        file_path = document.get('path')
        
        if not file_path:
            raise ValueError("Document must have a 'path' key")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        document_id = Path(file_path).name
        logger.info(f"Starting ACU LLM Text classification for: {document_id}")
        
        try:
            # Step 1 & 2: Convert PDF to images and extract text from each image
            logger.info("Step 1-2: Converting PDF to images and extracting text via ACU")
            page_data_json, conversion_time, total_ocr_time = self._process_pdf_to_json(file_path)
            
            if not page_data_json:
                logger.warning(f"No pages processed from {document_id}")
                return {
                    "document_type": "Other",
                    "confidence": 0.0,
                    "reasoning": "No text extracted from document",
                    "token_usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    },
                    "metadata": {
                        "method": "acu_llm_text_updated",
                        "file_path": file_path,
                        "conversion_time": conversion_time,
                        "total_ocr_time": total_ocr_time,
                        "total_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat(),
                        "pages_processed": 0
                    }
                }
            
            # Step 3: The text is already in JSON format (page_data_json)
            logger.info(f"Step 3: Text extracted and stored in JSON format for {len(page_data_json)} pages")
            
            # Step 4: Iterate over JSON and send each object to LLM for classification
            logger.info("Step 4: Iterating over JSON and classifying each page with LLM")
            page_classifications = []
            
            for page_data in page_data_json:
                if page_data.get('error'):
                    logger.warning(f"Skipping page {page_data['page_number']} due to error: {page_data['error']}")
                    continue
                
                if not page_data.get('text', '').strip():
                    logger.warning(f"Skipping page {page_data['page_number']} - no text content")
                    continue
                
                logger.info(f"Classifying page {page_data['page_number']} ({page_data['word_count']} words)")
                page_result = self._classify_page_with_llm(page_data)
                page_classifications.append(page_result)
            
            # Step 5: Aggregate page classifications
            final_result = self._aggregate_page_classifications(page_classifications)
            
            # Add metadata
            total_time = time.time() - start_time
            final_result["metadata"] = {
                "method": "acu_llm_text_updated",
                "file_path": file_path,
                "conversion_time": conversion_time,
                "total_ocr_time": total_ocr_time,
                "total_time": total_time,
                "timestamp": datetime.now().isoformat(),
                "pages_processed": len(page_classifications),
                "total_pages_found": len(page_data_json)
            }
            
            logger.info(f"ACU LLM Text classification completed for {document_id}: "
                       f"'{final_result['document_type']}' (confidence: {final_result['confidence']:.3f}) "
                       f"in {total_time:.2f}s")
            
            # Save result if configured
            if self.config.SAVE_RESULTS:
                self._save_results([final_result])
            
            return final_result
            
        except Exception as e:
            logger.error(f"Classification failed for {document_id}: {e}")
            return {
                "document_type": "Other",
                "confidence": 0.0,
                "reasoning": f"Classification error: {str(e)}",
                "error": str(e),
                "token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "metadata": {
                    "method": "acu_llm_text_updated",
                    "file_path": file_path,
                    "total_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                }
            }
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """Save classification results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.OUTPUT_DIR / f"acu_llm_text_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
    
    def get_document_types(self) -> List[str]:
        """
        Get list of possible document types.
        
        Returns:
            List of document type identifiers
        """
        return list(self.config.DOCUMENT_CATEGORIES.keys())
