"""NerStep v1: multi-attachment NER extraction."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..registry import register_step
from ..context import PipelineContext
from .base import Step

logger = logging.getLogger(__name__)


@register_step("ner", "v1")
class NerStep(Step):
    """For each attachment in the payload, read its ``document-output.json``
    from blob storage, assemble all OCR outputs into a single
    :class:`NERInput`, and run :class:`NERService`.

    Writes the result to ``context.step_results["ner"]``.
    """

    async def execute(self, context: PipelineContext) -> PipelineContext:
        from src.schemas.ocr_output import OCROutput
        from src.schemas.ner_input import NERInput
        from src.services.ner_service import NERService
        from src.utils.storage_blob import AzureStorageBlobClient
        from src.utils.request_context import set_request_context

        set_request_context(
            request_id=context.message_id,
            request_type=context.request_type,
            record_id=context.record_id,
            timestamp=context.timestamp,
        )

        ner_input = NERInput(ocroutput=[])
        document_result_checking = True

        for item in context.payload:
            attachment_id = item.get("attachmentId")
            logger.info("Processing attachmentId: %s", attachment_id)

            blob_service_client = AzureStorageBlobClient()
            out_data_blob_container = context.settings["out_data_blob_container"]
            ocr_output_folder = context.settings["ocr_output_folder"]

            blob_names = blob_service_client.list_blobs(
                container_name=out_data_blob_container,
                prefix=ocr_output_folder,
            )

            pattern = re.compile(
                rf"^.*{re.escape(attachment_id)}.*document-output\.json$"
            )
            matched = [b for b in blob_names if pattern.match(b)]

            if not matched:
                document_result_checking = False
                logger.warning(
                    "No document-result for attachmentId %s", attachment_id
                )
                continue

            logger.info("Matched blob: %s", matched[0])
            blob_client = blob_service_client.get_blob_client(
                container_name=out_data_blob_container,
                blob_name=matched[0],
            )
            blob_data = blob_client.download_blob().readall()
            blob_json = json.loads(blob_data.decode("utf-8"))
            ocr_output = OCROutput(**blob_json)

            ner_input.ocroutput.append(ocr_output)
            ner_input.uuid = context.message_id
            ner_input.timestamp = context.timestamp

        if not document_result_checking:
            raise ValueError(
                "document-result checking failed — please verify the "
                "attachmentId values in the message payload."
            )

        message_body = json.dumps(context.raw_message)
        ner_service = NERService()
        ner_output = ner_service.service(input=ner_input, message=message_body)

        context.step_results["ner"] = _serialize(ner_output)
        logger.info("NER extraction complete")
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
