"""Split documents based on classification response into separate PDFs by document type."""

import logging
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

import pikepdf
from pikepdf import Pdf

from src.shared.models.classification import ClassificationResponse, PageClassification

logger = logging.getLogger(__name__)


class DocumentSplitter:
    """Split PDF documents based on classification results."""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else None

    def split_document(self, response: ClassificationResponse) -> Dict[str, str]:
        source_path = Path(response.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source document not found: {source_path}")

        if not response.pages:
            raise ValueError("No page classifications found in response")

        base_output_dir = self.output_dir or source_path.parent
        output_dir = base_output_dir / source_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        pages_by_type = self._group_pages_by_type(response.pages)
        logger.info(
            f"Splitting document {source_path.name} into {len(pages_by_type)} document types"
        )

        output_files: Dict[str, str] = {}

        with Pdf.open(source_path) as src_pdf:
            total_pages = len(src_pdf.pages)
            logger.info(f"Source document has {total_pages} pages")

            for doc_type, page_numbers in pages_by_type.items():
                try:
                    output_path = self._create_output_path(
                        source_path, doc_type, output_dir
                    )
                    self._extract_pages(
                        src_pdf, page_numbers, output_path, total_pages
                    )
                    output_files[doc_type] = str(output_path)
                    logger.info(
                        f"Created {doc_type} document: {output_path.name} "
                        f"({len(page_numbers)} pages)"
                    )
                except Exception as e:
                    logger.error(f"Failed to create {doc_type} document: {e}")

        return output_files

    def _group_pages_by_type(
        self, pages: List[PageClassification]
    ) -> Dict[str, Set[int]]:
        pages_by_type = defaultdict(set)
        for page in pages:
            pages_by_type[page.document_type].add(page.page_number)
        return {k: sorted(v) for k, v in pages_by_type.items()}

    def _create_output_path(
        self, source_path: Path, doc_type: str, output_dir: Path
    ) -> Path:
        clean_doc_type = self._clean_filename(doc_type)
        output_path = output_dir / f"{clean_doc_type}.pdf"

        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{clean_doc_type}_{counter}.pdf"
            counter += 1

        return output_path

    def _clean_filename(self, text: str) -> str:
        invalid_chars = '<>:"|?*'
        for ch in invalid_chars:
            text = text.replace(ch, "")
        return text.replace(" ", "_").replace("/", "-").lower()

    def _extract_pages(
        self,
        src_pdf: Pdf,
        page_numbers: List[int],
        output_path: Path,
        total_pages: int,
    ):
        new_pdf = Pdf.new()

        selected_page_indexes: Set[int] = set()

        for page_num in page_numbers:
            if 1 <= page_num <= total_pages:
                idx = page_num - 1
                new_pdf.pages.append(src_pdf.pages[idx])
                selected_page_indexes.add(idx)
            else:
                logger.warning(
                    f"Invalid page number {page_num} (document has {total_pages} pages)"
                )

        if not selected_page_indexes:
            raise ValueError("No valid pages to extract")

        self._preserve_form_structure(src_pdf, new_pdf, selected_page_indexes)
        new_pdf.save(output_path)

    def _preserve_form_structure(
        self,
        src_pdf: Pdf,
        dst_pdf: Pdf,
        selected_page_indexes: Set[int],
    ):
        """
        Preserve AcroForm fields that belong to extracted pages.
        """
        try:
            if not hasattr(src_pdf, "Root"):
                logger.debug("PDF has no Root catalog")
                return

            if "/AcroForm" not in src_pdf.Root:
                logger.debug("No AcroForm found in source document")
                return

            src_acroform = src_pdf.Root.AcroForm
            dst_pdf.Root.AcroForm = src_acroform

            if not hasattr(src_acroform, "Fields"):
                return

            filtered_fields = []

            for field in src_acroform.Fields:
                field_obj = field.get_object()

                page_ref = getattr(field_obj, "P", None)
                if page_ref is not None:
                    try:
                        page_index = src_pdf.pages.index(page_ref)
                        if page_index in selected_page_indexes:
                            filtered_fields.append(field)
                    except ValueError:
                        continue
                else:
                    filtered_fields.append(field)

            dst_pdf.Root.AcroForm.Fields = filtered_fields
            logger.debug("Preserved AcroForm fields for extracted pages")

        except Exception as e:
            logger.warning(f"Failed to preserve AcroForm structure: {e}")


def split_document_from_response(
    response: ClassificationResponse, output_dir: str = None
) -> Dict[str, str]:
    splitter = DocumentSplitter(output_dir)
    return splitter.split_document(response)
