"""Tests for NerStep."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.steps.ner_step import NerStep


@pytest.fixture()
def ctx(case_message: dict) -> PipelineContext:
    ctx = PipelineContext.from_message(case_message)
    ctx.settings = {
        "out_data_blob_container": "out-container",
        "ocr_output_folder": "output/",
    }
    return ctx


class TestNerStep:
    @pytest.mark.asyncio
    async def test_execute_produces_ner_result(self, ctx: PipelineContext) -> None:
        ocr_blob_data = json.dumps({"summary_json": {"pages": 2}}).encode()
        mock_ner_output = SimpleNamespace(
            final_summary_json={"entities": [{"name": "John"}]},
        )

        mock_blob_download = MagicMock()
        mock_blob_download.readall.return_value = ocr_blob_data

        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.return_value = mock_blob_download

        mock_azure_blob = MagicMock()
        mock_azure_blob.list_blobs.return_value = [
            "output/att-100/document-output.json",
            "output/att-101/document-output.json",
        ]
        mock_azure_blob.get_blob_client.return_value = mock_blob_client

        mock_ner_input = MagicMock()
        mock_ner_input.ocroutput = []

        mock_ner_service = MagicMock()
        mock_ner_service.service.return_value = mock_ner_output

        with (
            patch("src.utils.storage_blob.AzureStorageBlobClient", create=True, return_value=mock_azure_blob),
            patch("src.utils.request_context.set_request_context", create=True),
            patch("src.schemas.ocr_output.OCROutput", create=True, return_value=SimpleNamespace(summary_json={"pages": 2})),
            patch("src.schemas.ner_input.NERInput", create=True, return_value=mock_ner_input),
            patch("src.services.ner_service.NERService", create=True, return_value=mock_ner_service),
        ):
            step = NerStep()
            result = await step.execute(ctx)

        assert "ner" in result.step_results
        assert result.step_results["ner"]["final_summary_json"]["entities"][0]["name"] == "John"

    @pytest.mark.asyncio
    async def test_missing_attachment_raises(self, ctx: PipelineContext) -> None:
        mock_azure_blob = MagicMock()
        mock_azure_blob.list_blobs.return_value = []

        mock_ner_input = MagicMock()
        mock_ner_input.ocroutput = []

        with (
            patch("src.utils.storage_blob.AzureStorageBlobClient", create=True, return_value=mock_azure_blob),
            patch("src.utils.request_context.set_request_context", create=True),
            patch("src.schemas.ner_input.NERInput", create=True, return_value=mock_ner_input),
            patch("src.schemas.ocr_output.OCROutput", create=True),
            patch("src.services.ner_service.NERService", create=True),
        ):
            step = NerStep()
            with pytest.raises(ValueError, match="document-result checking failed"):
                await step.execute(ctx)

    @pytest.mark.asyncio
    async def test_step_name_and_version(self) -> None:
        assert NerStep.step_name == "ner"
        assert NerStep.step_version == "v1"
