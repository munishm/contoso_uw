"""PDF to images converter."""

import os
import logging
from pathlib import Path
from typing import List
from pdf2image import convert_from_path


logger = logging.getLogger(__name__)


class PDFToImageConverter:
    """Convert PDF documents to images for vision-based processing."""
    
    def __init__(self, dpi: int = 300, poppler_path: str = None):
        """
        Initialize the PDF to image converter.
        
        Args:
            dpi: Resolution for image conversion
            poppler_path: Path to poppler binaries (optional)
        """
        self.dpi = dpi
        self.poppler_path = poppler_path or "/opt/homebrew/bin"
        
    def convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
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
            
            logger.info(f"Converted {len(images)} pages from {pdf_path}")
            
            # Save each page as an image
            image_paths = []
            for i, image in enumerate(images):
                page_number = i + 1
                page_filename = f"page_{page_number}.jpg"
                page_path = page_dir / page_filename
                
                image.save(page_path, 'JPEG')
                image_paths.append(str(page_path))
                logger.debug(f"Saved page {page_number} as {page_path}")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Failed to convert PDF {pdf_path}: {e}")
            raise RuntimeError(f"Failed to convert PDF {pdf_path}: {e}")
