"""Azure Document Intelligence OCR helper for precise bounding boxes."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    HAS_DOC_INTELLIGENCE = True
except ImportError:
    HAS_DOC_INTELLIGENCE = False

logger = logging.getLogger(__name__)


@dataclass
class OCRWord:
    """Represents a word from OCR with its bounding box."""
    text: str
    page: int
    x: float  # Normalized 0-1
    y: float  # Normalized 0-1
    width: float  # Normalized 0-1
    height: float  # Normalized 0-1
    confidence: float


@dataclass 
class OCRLine:
    """Represents a line from OCR."""
    text: str
    page: int
    x: float
    y: float
    width: float
    height: float
    words: List[OCRWord]


class DocumentIntelligenceOCR:
    """
    Azure Document Intelligence client for getting precise OCR with bounding boxes.
    
    This class provides OCR functionality that returns text with exact pixel/normalized
    coordinates, which can be used to locate extracted field values on the document.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None
    ):
        """
        Initialize Document Intelligence OCR client.
        
        Args:
            endpoint: Azure Document Intelligence endpoint
            api_key: API key (if None, uses DefaultAzureCredential)
        """
        if not HAS_DOC_INTELLIGENCE:
            raise ImportError(
                "azure-ai-documentintelligence is required. "
                "Install with: pip install azure-ai-documentintelligence"
            )
        
        self.endpoint = endpoint
        
        if api_key:
            credential = AzureKeyCredential(api_key)
        else:
            credential = DefaultAzureCredential()
        
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=credential
        )
    
    async def get_ocr_results(self, document_content: bytes) -> Dict[int, List[OCRLine]]:
        """
        Run OCR on document and return text with bounding boxes.
        
        Args:
            document_content: Raw document bytes (PDF or image)
            
        Returns:
            Dictionary mapping page numbers (1-indexed) to list of OCRLine objects
        """
        # Use prebuilt-read model for OCR
        # Note: azure-ai-documentintelligence SDK uses 'body' parameter for document content
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-read",
            body=document_content,
            content_type="application/octet-stream"
        )
        
        result: AnalyzeResult = poller.result()
        
        pages_ocr: Dict[int, List[OCRLine]] = {}
        
        if not result.pages:
            return pages_ocr
        
        for page in result.pages:
            page_num = page.page_number
            page_width = page.width or 1
            page_height = page.height or 1
            
            lines: List[OCRLine] = []
            
            if page.lines:
                for line in page.lines:
                    # Get bounding polygon and convert to normalized coordinates
                    if line.polygon and len(line.polygon) >= 4:
                        # Polygon is [x1,y1, x2,y2, x3,y3, x4,y4] - top-left, top-right, bottom-right, bottom-left
                        min_x = min(line.polygon[0], line.polygon[6]) / page_width
                        min_y = min(line.polygon[1], line.polygon[3]) / page_height
                        max_x = max(line.polygon[2], line.polygon[4]) / page_width
                        max_y = max(line.polygon[5], line.polygon[7]) / page_height
                        
                        line_width = max_x - min_x
                        line_height = max_y - min_y
                    else:
                        # Fallback
                        min_x, min_y = 0.0, 0.0
                        line_width, line_height = 1.0, 0.02
                    
                    # Get words in this line
                    words: List[OCRWord] = []
                    if page.words:
                        for word in page.words:
                            # Check if word is in this line by comparing content
                            if word.content in line.content:
                                if word.polygon and len(word.polygon) >= 4:
                                    w_min_x = min(word.polygon[0], word.polygon[6]) / page_width
                                    w_min_y = min(word.polygon[1], word.polygon[3]) / page_height
                                    w_max_x = max(word.polygon[2], word.polygon[4]) / page_width
                                    w_max_y = max(word.polygon[5], word.polygon[7]) / page_height
                                    
                                    words.append(OCRWord(
                                        text=word.content,
                                        page=page_num,
                                        x=w_min_x,
                                        y=w_min_y,
                                        width=w_max_x - w_min_x,
                                        height=w_max_y - w_min_y,
                                        confidence=word.confidence or 0.9
                                    ))
                    
                    lines.append(OCRLine(
                        text=line.content,
                        page=page_num,
                        x=min_x,
                        y=min_y,
                        width=line_width,
                        height=line_height,
                        words=words
                    ))
            
            pages_ocr[page_num] = lines
        
        return pages_ocr
    
    def find_text_bbox(
        self,
        search_text: str,
        ocr_results: Dict[int, List[OCRLine]],
        page_hint: Optional[int] = None
    ) -> Optional[Tuple[int, float, float, float, float]]:
        """
        Find the bounding box for a specific text string in OCR results.
        
        Args:
            search_text: Text to find
            ocr_results: OCR results from get_ocr_results()
            page_hint: Optional page number to search first
            
        Returns:
            Tuple of (page, x, y, width, height) or None if not found
        """
        if not search_text or not ocr_results:
            return None
        
        search_text_lower = search_text.lower().strip()
        
        # Search pages in order, starting with hint page if provided
        pages_to_search = list(ocr_results.keys())
        if page_hint and page_hint in pages_to_search:
            pages_to_search.remove(page_hint)
            pages_to_search.insert(0, page_hint)
        
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            
            for line in lines:
                line_text_lower = line.text.lower().strip()
                
                # Exact match
                if search_text_lower == line_text_lower:
                    return (page_num, line.x, line.y, line.width, line.height)
                
                # Partial match - search_text is contained in line
                if search_text_lower in line_text_lower:
                    # Try to find exact word boundaries
                    for word in line.words:
                        if word.text.lower().strip() == search_text_lower:
                            return (page_num, word.x, word.y, word.width, word.height)
                    
                    # If multi-word, use the line bbox
                    if len(search_text.split()) > 1:
                        return (page_num, line.x, line.y, line.width, line.height)
                
                # Line is contained in search_text (multi-line value)
                if line_text_lower in search_text_lower:
                    return (page_num, line.x, line.y, line.width, line.height)
        
        # Fuzzy match - try to find best match
        best_match = None
        best_score = 0.0
        
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            
            for line in lines:
                score = self._similarity_score(search_text_lower, line.text.lower())
                if score > best_score and score > 0.7:  # 70% threshold
                    best_score = score
                    best_match = (page_num, line.x, line.y, line.width, line.height)
        
        return best_match
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """Calculate simple similarity score between two strings."""
        if not s1 or not s2:
            return 0.0
        
        # Simple Jaccard-like similarity on characters
        set1 = set(s1.replace(" ", ""))
        set2 = set(s2.replace(" ", ""))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
