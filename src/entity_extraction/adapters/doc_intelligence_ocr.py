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
        print(f"[DocIntelligence] Starting OCR analysis...")
        print(f"[DocIntelligence] Document size: {len(document_content) / 1024:.1f} KB")
        
        # Use prebuilt-read model for OCR
        # Note: azure-ai-documentintelligence SDK uses 'body' parameter for document content
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-read",
            body=document_content,
            content_type="application/octet-stream"
        )
        
        print(f"[DocIntelligence] Waiting for analysis to complete...")
        result: AnalyzeResult = poller.result()
        
        pages_ocr: Dict[int, List[OCRLine]] = {}
        
        if not result.pages:
            print(f"[DocIntelligence] No pages found in document")
            return pages_ocr
        
        print(f"[DocIntelligence] Document has {len(result.pages)} pages")
        
        for page in result.pages:
            page_num = page.page_number
            page_width = page.width or 1
            page_height = page.height or 1
            print(f"[DocIntelligence] Page {page_num}: {page_width}x{page_height}, {len(page.lines or [])} lines")
            
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
        
        # Log sample of extracted text for debugging
        print(f"[DocIntelligence] OCR extraction summary:")
        for page_num, lines in pages_ocr.items():
            sample_texts = [line.text[:50] + "..." if len(line.text) > 50 else line.text for line in lines[:5]]
            print(f"[DocIntelligence]   Page {page_num}: {len(lines)} lines")
            for i, text in enumerate(sample_texts):
                print(f"[DocIntelligence]     Line {i+1}: '{text}'")
            if len(lines) > 5:
                print(f"[DocIntelligence]     ... and {len(lines) - 5} more lines")
        
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
            print(f"[DocIntelligence] find_text_bbox: empty search_text or ocr_results")
            return None
        
        search_text_lower = search_text.lower().strip()
        search_words = search_text_lower.split()
        print(f"[DocIntelligence] Searching for: '{search_text}' ({len(search_words)} words, page_hint={page_hint})")
        
        # Search pages in order, starting with hint page if provided
        pages_to_search = list(ocr_results.keys())
        if page_hint and page_hint in pages_to_search:
            pages_to_search.remove(page_hint)
            pages_to_search.insert(0, page_hint)
        
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            
            for line in lines:
                line_text_lower = line.text.lower().strip()
                
                # Exact match - whole line equals search text
                if search_text_lower == line_text_lower:
                    print(f"[DocIntelligence]   ✓ EXACT match on page {page_num}: '{line.text}'")
                    return (page_num, line.x, line.y, line.width, line.height)
                
                # Partial match - search_text is contained in line
                if search_text_lower in line_text_lower:
                    # Try to find exact word boundaries
                    for word in line.words:
                        if word.text.lower().strip() == search_text_lower:
                            print(f"[DocIntelligence]   ✓ WORD match on page {page_num}: '{word.text}' in line '{line.text}'")
                            return (page_num, word.x, word.y, word.width, word.height)
                    
                    # If multi-word search, use the line bbox
                    if len(search_words) > 1:
                        print(f"[DocIntelligence]   ✓ PARTIAL match on page {page_num}: '{search_text}' found in '{line.text}'")
                        return (page_num, line.x, line.y, line.width, line.height)
        
        # Multi-word value: Try to find all words and combine bboxes
        if len(search_words) > 1:
            combined_bbox = self._find_combined_bbox(search_words, ocr_results, pages_to_search)
            if combined_bbox:
                return combined_bbox
        
        # Single word that might be partial: Look for best containing line
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            for line in lines:
                line_text_lower = line.text.lower().strip()
                # Line is contained in search_text (partial match)
                if line_text_lower in search_text_lower and len(line_text_lower) > 2:
                    # But don't match too short strings
                    print(f"[DocIntelligence]   ~ LINE-IN-VALUE match on page {page_num}: '{line.text}' (partial)")
                    # Continue looking for better matches instead of returning immediately
        
        # Fuzzy match - try to find best match
        best_match = None
        best_score = 0.0
        best_line_text = ""
        
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            
            for line in lines:
                score = self._similarity_score(search_text_lower, line.text.lower())
                if score > best_score and score > 0.7:  # 70% threshold
                    best_score = score
                    best_match = (page_num, line.x, line.y, line.width, line.height)
                    best_line_text = line.text
        
        if best_match:
            print(f"[DocIntelligence]   ~ FUZZY match (score={best_score:.2f}): '{best_line_text}'")
        else:
            print(f"[DocIntelligence]   ✗ NO match found for '{search_text}'")
        
        return best_match
    
    def _find_combined_bbox(
        self, 
        search_words: List[str], 
        ocr_results: Dict[int, List[OCRLine]], 
        pages_to_search: List[int]
    ) -> Optional[Tuple[int, float, float, float, float]]:
        """
        Find all words from search and combine their bounding boxes.
        
        This handles cases where a value like "LOK WING CHING" is split across
        multiple OCR lines (e.g., Family Name: LOK, Given Name: WING CHING).
        
        STRICT matching: Only exact word matches, minimum 3 characters to avoid
        matching common short words like "in", "a", "the".
        """
        # Filter out very short words that cause false matches
        search_words_filtered = [w for w in search_words if len(w) >= 3]
        if not search_words_filtered:
            # If all words are short, use original
            search_words_filtered = search_words
        
        print(f"[DocIntelligence]   Looking for words: {search_words_filtered}")
        
        found_words = []
        target_page = None
        
        for page_num in pages_to_search:
            lines = ocr_results[page_num]
            page_found_words = []
            matched_search_words = set()
            
            for line in lines:
                for word in line.words:
                    word_text_lower = word.text.lower().strip()
                    
                    # STRICT: Only exact matches for each search word
                    for sw in search_words_filtered:
                        # Exact match only
                        if sw == word_text_lower:
                            page_found_words.append({
                                'text': word.text,
                                'x': word.x,
                                'y': word.y,
                                'width': word.width,
                                'height': word.height,
                                'search_word': sw
                            })
                            matched_search_words.add(sw)
                            break
            
            # Check how many unique search words we found on this page
            match_ratio = len(matched_search_words) / len(search_words_filtered) if search_words_filtered else 0
            print(f"[DocIntelligence]   Page {page_num}: found {len(matched_search_words)}/{len(search_words_filtered)} words ({match_ratio:.0%})")
            
            if match_ratio >= 0.6:  # Found at least 60% of words
                found_words = page_found_words
                target_page = page_num
                break
            elif len(matched_search_words) > len(set(w['search_word'] for w in found_words)):
                found_words = page_found_words
                target_page = page_num
        
        if not found_words or target_page is None:
            print(f"[DocIntelligence]   ✗ Could not find enough words for combined bbox")
            return None
        
        # Combine bounding boxes
        min_x = min(w['x'] for w in found_words)
        min_y = min(w['y'] for w in found_words)
        max_x = max(w['x'] + w['width'] for w in found_words)
        max_y = max(w['y'] + w['height'] for w in found_words)
        
        combined_width = max_x - min_x
        combined_height = max_y - min_y
        
        matched_texts = [w['text'] for w in found_words]
        print(f"[DocIntelligence]   ✓ COMBINED bbox on page {target_page}: matched [{', '.join(matched_texts)}]")
        print(f"[DocIntelligence]     Combined bbox: x={min_x:.3f}, y={min_y:.3f}, w={combined_width:.3f}, h={combined_height:.3f}")
        
        return (target_page, min_x, min_y, combined_width, combined_height)
    
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
