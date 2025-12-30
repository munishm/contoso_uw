"""Split documents based on classification response into separate PDFs by document type."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from PyPDF2 import PdfReader, PdfWriter
from src.shared.models.classification import ClassificationResponse, PageClassification


logger = logging.getLogger(__name__)


class DocumentSplitter:
    """Split PDF documents based on classification results."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize document splitter.
        
        Args:
            output_dir: Directory to save split documents. If None, uses same directory as source.
        """
        self.output_dir = Path(output_dir) if output_dir else None
        
    def split_document(self, response: ClassificationResponse) -> Dict[str, str]:
        """
        Split a document based on classification response.
        
        Args:
            response: ClassificationResponse containing page classifications
            
        Returns:
            Dict mapping document_type to output file path
            
        Raises:
            FileNotFoundError: If source document doesn't exist
            ValueError: If no pages to process
        """
        source_path = Path(response.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source document not found: {source_path}")
            
        if not response.pages:
            raise ValueError("No page classifications found in response")
            
        # Set output directory - create folder named after source file
        if self.output_dir:
            base_output_dir = Path(self.output_dir)
        else:
            base_output_dir = source_path.parent
            
        # Create subfolder named after the source file (without extension)
        file_folder_name = source_path.stem
        output_dir = base_output_dir / file_folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Group pages by document type
        pages_by_type = self._group_pages_by_type(response.pages)
        
        logger.info(f"Splitting document {source_path.name} into {len(pages_by_type)} document types")
        
        # Load the source PDF
        try:
            reader = PdfReader(str(source_path))
            total_pages = len(reader.pages)
            
            logger.info(f"Source document has {total_pages} pages")
            
        except Exception as e:
            raise RuntimeError(f"Failed to read source PDF: {e}")
        
        # Create separate PDFs for each document type
        output_files = {}
        
        for doc_type, page_numbers in pages_by_type.items():
            try:
                output_path = self._create_output_path(source_path, doc_type, output_dir)
                self._extract_pages(reader, page_numbers, output_path, total_pages)
                output_files[doc_type] = str(output_path)
                
                logger.info(f"Created {doc_type} document: {output_path.name} ({len(page_numbers)} pages)")
                
            except Exception as e:
                logger.error(f"Failed to create {doc_type} document: {e}")
                continue
                
        return output_files
    
    def _group_pages_by_type(self, pages: List[PageClassification]) -> Dict[str, Set[int]]:
        """
        Group pages by document type.
        
        Args:
            pages: List of page classifications
            
        Returns:
            Dict mapping document_type to set of page numbers
        """
        pages_by_type = defaultdict(set)
        
        for page in pages:
            pages_by_type[page.document_type].add(page.page_number)
            
        # Convert sets to sorted lists for consistent output
        return {doc_type: sorted(page_set) for doc_type, page_set in pages_by_type.items()}
    
    def _create_output_path(self, source_path: Path, doc_type: str, output_dir: Path) -> Path:
        """
        Create output file path for a document type.
        
        Args:
            source_path: Original document path
            doc_type: Document type for this split
            output_dir: Output directory (already includes source file folder)
            
        Returns:
            Path for the output file
        """
        # Clean document type for filename
        clean_doc_type = self._clean_filename(doc_type)
        
        # Use just the document type as filename (since we're already in a source-file-named folder)
        output_filename = f"{clean_doc_type}.pdf"
        output_path = output_dir / output_filename
        
        # Handle filename conflicts
        counter = 1
        while output_path.exists():
            output_filename = f"{clean_doc_type}_{counter}.pdf"
            output_path = output_dir / output_filename
            counter += 1
            
        return output_path
    
    def _clean_filename(self, text: str) -> str:
        """
        Clean text for use in filename.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text suitable for filename
        """
        # Replace spaces and special characters
        cleaned = text.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Remove other problematic characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            cleaned = cleaned.replace(char, "")
            
        return cleaned.lower()
    
    def _extract_pages(self, reader: PdfReader, page_numbers: List[int], output_path: Path, total_pages: int):
        """
        Extract specified pages to a new PDF.
        
        Args:
            reader: PDF reader for source document
            page_numbers: List of page numbers to extract (1-indexed)
            output_path: Path for output PDF
            total_pages: Total pages in source document
            
        Raises:
            ValueError: If invalid page numbers provided
        """
        writer = PdfWriter()
        
        # Validate and extract pages
        valid_pages = []
        for page_num in page_numbers:
            if 1 <= page_num <= total_pages:
                # Convert to 0-indexed for PyPDF2
                writer.add_page(reader.pages[page_num - 1])
                valid_pages.append(page_num)
            else:
                logger.warning(f"Invalid page number {page_num} (document has {total_pages} pages)")
        
        if not valid_pages:
            raise ValueError(f"No valid pages found in {page_numbers}")
            
        # Write the output PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
            
        logger.debug(f"Extracted pages {valid_pages} to {output_path}")


def split_document_from_response(response: ClassificationResponse, output_dir: str = None) -> Dict[str, str]:
    """
    Convenience function to split a document from a classification response.
    
    Args:
        response: ClassificationResponse containing page classifications
        output_dir: Directory to save split documents. If None, uses same directory as source.
        
    Returns:
        Dict mapping document_type to output file path
    """
    splitter = DocumentSplitter(output_dir)
    return splitter.split_document(response)
