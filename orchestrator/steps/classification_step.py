"""ClassificationStep v3: blob copy + document classification."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import unquote

from ..registry import register_step
from ..context import PipelineContext
from .base import Step

logger = logging.getLogger(__name__)


@register_step("classification", "v3")
class ClassificationStep(Step):
    """Copy the document blob from the incoming container to the internal
    ``src-raw-doc`` container, then classify it via :class:`ClassifierService`.

    Writes the serialized :class:`DOCOutput` into
    ``context.step_results["classification"]``.
    """

    async def execute(self, context: PipelineContext) -> PipelineContext:
        from src.schemas.doc_input import DOCInput  # noqa: F811
        from src.schemas.doc_output import DOCOutput  # noqa: F811
        from src.services.classifier_service import ClassifierService  # noqa: F811
        from src.utils.storage_blob import AzureStorageBlobClient  # noqa: F811
        from src.utils.request_context import set_request_context  # noqa: F811

        set_request_context(
            request_id=context.message_id,
            request_type=context.request_type,
            record_id=context.record_id,
            timestamp=context.timestamp,
        )

        attachment = context.payload[0]
        attachment_id = attachment["attachmentId"]
        document_url = attachment["urlOfContainer"]
        incoming_blob = document_url.split("/")[-1]

        # -- blob copy from incoming to internal container --------------------
        account_url = context.settings["in_storage_blob_account_url"]
        incoming_container = context.settings["incoming_container"]
        src_raw_container = context.settings["src_raw_container"]

        source_url = AzureStorageBlobClient(
            account_url=account_url,
        ).generate_sas_url(
            container_name=incoming_container,
            blob_name=incoming_blob,
        )

        azure_blob_client = AzureStorageBlobClient()
        target_blob_client = azure_blob_client.get_blob_client(
            container_name=src_raw_container,
            blob_name=incoming_blob,
        )
        target_blob_client.start_copy_from_url(source_url)

        raw_document_url = azure_blob_client.get_blob_url(
            container_name=src_raw_container,
            blob_name=incoming_blob,
        )
        raw_document_url = unquote(raw_document_url)
        logger.info("Blob copied to internal raw: %s", raw_document_url)

        # -- classify ---------------------------------------------------------
        doc_input = DOCInput(
            attachment_id=attachment_id,
            document_url=raw_document_url,
            uuid=context.message_id,
            checksum="",
        )

        classifier_service = ClassifierService()
        doc_output: DOCOutput = classifier_service.service(input=doc_input)

        context.step_results["classification"] = _serialize(doc_output)
        logger.info("Classification complete for attachment %s", attachment_id)
        return context


def _serialize(obj: Any) -> dict[str, Any]:
    """Best-effort serialization of a schema object to a plain dict."""
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):  # Pydantic v1
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return dict(obj)
