"""OcrStep v2: OCR extraction from classified document."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..registry import register_step
from ..context import PipelineContext
from .base import Step

logger = logging.getLogger(__name__)


@register_step("ocr", "v2")
class OcrStep(Step):
    """Read the :class:`DOCOutput` from the pipeline context, run OCR via
    :class:`OCRService`, and write the result to
    ``context.step_results["ocr"]``.

    The OCR service also persists ``document-output.json`` to blob storage
    (required by downstream CaseSummary NER).
    """

    async def execute(self, context: PipelineContext) -> PipelineContext:
        doc_output_data = context.step_results.get("classification")
        if not doc_output_data:
            raise ValueError(
                "Classification result not found in pipeline context. "
                "Ensure the classification step runs before OCR."
            )

        from src.schemas.doc_output import DOCOutput
        from src.services.ocr_service import OCRService
        from src.utils.request_context import set_request_context

        set_request_context(
            request_id=context.message_id,
            request_type=context.request_type,
            record_id=context.record_id,
            timestamp=context.timestamp,
        )

        doc_output = DOCOutput(**doc_output_data)
        message_body = json.dumps(context.raw_message)

        logger.info("Starting OCR extraction")
        ocr_service = OCRService()
        ocr_output = ocr_service.service(input=doc_output, message=message_body)

        context.step_results["ocr"] = _serialize(ocr_output)
        logger.info("OCR extraction complete")
        return context


def _serialize(obj: Any) -> dict[str, Any]:
    """Best-effort serialization of a schema object to a plain dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return dict(obj)
