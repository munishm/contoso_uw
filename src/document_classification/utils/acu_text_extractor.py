"""Azure Content Understanding text extractor."""

import time
import uuid
import json
import logging
import requests
from typing import Dict, Any
from pathlib import Path

from .auth import create_token_provider


logger = logging.getLogger(__name__)


class ACUTextExtractor:
    """
    Extract text from documents using Azure Content Understanding.
    
    Uses the prebuilt-document analyzer for OCR and text extraction.
    """
    
    def __init__(self, config):
        """
        Initialize the text extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.endpoint = config.CU_ENDPOINT.rstrip('/')
        self.api_version = config.CU_API_VERSION
        self.analyzer_id = 'prebuilt-document'  # Use prebuilt-document analyzer (same as original notebook)
        
        # Create token provider
        self._token_provider = create_token_provider(config.AZURE_TENANT_ID)
        
        logger.info("ACU Text Extractor initialized")
    
    def _get_access_token(self) -> str:
        """Get access token for ACU."""
        return self._token_provider()
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a document using ACU.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from: {file_path}")
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Submit analyze request
        op_location = self._submit_analyze(file_data)
        
        # Poll for results
        result = self._poll_result(op_location)
        
        # Extract text from result
        text = self._extract_text_from_result(result)
        
        logger.info(f"Extracted {len(text)} characters")
        return text
    
    def extract_text_by_page(self, file_path: str) -> Dict[int, str]:
        """
        Extract text from a document page by page using ACU.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary mapping page number to extracted text
        """
        logger.info(f"Extracting text by page from: {file_path}")
        
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Submit analyze request
        op_location = self._submit_analyze(file_data)
        
        # Poll for results
        result = self._poll_result(op_location)
        
        # Extract text per page
        pages_text = self._extract_text_by_page(result)
        
        logger.info(f"Extracted text from {len(pages_text)} pages")
        return pages_text
    
    def _submit_analyze(self, file_data: bytes) -> str:
        """
        Submit ACU analyze request.
        
        Args:
            file_data: Binary file data
            
        Returns:
            Operation location URL for polling
        """
        url = f"{self.endpoint}/contentunderstanding/analyzers/{self.analyzer_id}:analyzeBinary?api-version={self.api_version}"
        
        access_token = self._get_access_token()
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
        
        return op_location
    
    def _poll_result(self, op_location: str, timeout_sec: int = 180) -> Dict[str, Any]:
        """
        Poll ACU operation until complete.
        
        Args:
            op_location: Operation location URL
            timeout_sec: Maximum time to wait
            
        Returns:
            Result JSON
        """
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            response = requests.get(op_location, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status", "").lower()
            
            if status == "succeeded":
                logger.debug("ACU analysis succeeded")
                return data.get("result", {})
            elif status in ("failed", "canceled"):
                error_msg = f"ACU analysis failed with status: {status}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            time.sleep(2)
        
        raise TimeoutError("ACU polling timed out")
    
    def _extract_text_from_result(self, result: Dict[str, Any]) -> str:
        """
        Extract text from ACU result.
        
        Prefers markdown format, falls back to concatenating words by page.
        
        Args:
            result: ACU result JSON
            
        Returns:
            Extracted text
        """
        contents = result.get("contents", [])
        if not contents:
            return ""
        
        doc = contents[0]
        
        # Prefer markdown format
        markdown = doc.get("markdown")
        if markdown:
            return markdown.strip()
        
        # Fallback: concatenate words by page
        pieces = []
        pages = doc.get("pages", []) or []
        
        for i, page in enumerate(pages, start=1):
            words = page.get("words", []) or []
            if words:
                pieces.append(f"# Page {i}")
                pieces.append(" ".join(w.get("text", "") for w in words))
        
        return "\n\n".join(pieces).strip()
    
    def _extract_text_by_page(self, result: Dict[str, Any]) -> Dict[int, str]:
        """
        Extract text from ACU result page by page.
        
        Args:
            result: ACU result JSON
            
        Returns:
            Dictionary mapping page number to text
        """
        contents = result.get("contents", [])
        if not contents:
            logger.warning("No contents in ACU result")
            return {}
        
        doc = contents[0]
        pages = doc.get("pages", []) or []
        
        if not pages:
            logger.warning("No pages in ACU result")
            return {}
        
        # First try structured content (words or lines per page)
        pages_text = {}
        has_structured_content = False
        
        for i, page in enumerate(pages, start=1):
            words = page.get("words", []) or []
            lines = page.get("lines", []) or []
            
            if words:
                page_text = " ".join(w.get("text", "") or w.get("content", "") for w in words)
                pages_text[i] = page_text.strip()
                has_structured_content = True
            elif lines:
                line_texts = [line.get("content", "") or line.get("text", "") for line in lines]
                pages_text[i] = " ".join(line_texts).strip()
                has_structured_content = True
            else:
                pages_text[i] = ""
        
        # If we have structured content for at least some pages, return it
        if has_structured_content and any(pages_text.values()):
            return pages_text
        
        # Fallback: try to extract from markdown using page spans
        markdown = doc.get("markdown")
        if markdown and pages:
            logger.debug("Attempting to extract text per page from markdown using page spans")
            pages_text = {}
            
            # Get page spans (character offsets in markdown)
            for i, page in enumerate(pages, start=1):
                spans = page.get("spans", [])
                if spans:
                    # Extract text from markdown using spans
                    page_chars = []
                    for span in spans:
                        offset = span.get("offset", 0)
                        length = span.get("length", 0)
                        if offset is not None and length:
                            page_chars.append(markdown[offset:offset + length])
                    
                    if page_chars:
                        pages_text[i] = " ".join(page_chars).strip()
                    else:
                        pages_text[i] = ""
                else:
                    pages_text[i] = ""
            
            # If span extraction worked, return it
            if any(pages_text.values()):
                return pages_text
            
            # Last resort: split markdown roughly by page count
            logger.warning("No span information, splitting markdown by page count")
            # Just use full markdown for each page as ACU doesn't provide per-page breakdown
            # This is not ideal but maintains compatibility
            for i in range(1, len(pages) + 1):
                pages_text[i] = markdown.strip()
            
            return pages_text
        
        logger.warning("Could not extract page-level text content")
        return {}
