"""Tests for ClassificationStep."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.steps.classification_step import ClassificationStep


@pytest.fixture()
def ctx(sample_message: dict) -> PipelineContext:
    ctx = PipelineContext.from_message(sample_message)
    ctx.settings = {
        "in_storage_blob_account_url": "https://account.blob.core.windows.net",
        "incoming_container": "incoming-doc",
        "src_raw_container": "src-raw-doc",
    }
    return ctx


class TestClassificationStep:
    @pytest.mark.asyncio
    async def test_execute_stores_classification_result(self, ctx: PipelineContext) -> None:
        mock_doc_output = SimpleNamespace(
            attachment_id="att-456",
            doc_type="ACORD",
            confidence=0.95,
            document_url="https://storage.blob.core.windows.net/src-raw-doc/doc.pdf",
        )

        mock_blob_client = MagicMock()
        mock_azure_blob = MagicMock()
        mock_azure_blob.get_blob_client.return_value = mock_blob_client
        mock_azure_blob.get_blob_url.return_value = (
            "https://storage.blob.core.windows.net/src-raw-doc/doc.pdf"
        )

        mock_sas_blob = MagicMock()
        mock_sas_blob.generate_sas_url.return_value = "https://sas-url"

        call_count = 0
        def blob_factory(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_sas_blob
            return mock_azure_blob

        mock_classifier = MagicMock()
        mock_classifier.service.return_value = mock_doc_output

        with (
            patch("src.services.classifier_service.ClassifierService", return_value=mock_classifier, create=True),
            patch("src.utils.storage_blob.AzureStorageBlobClient", side_effect=blob_factory, create=True),
            patch("src.utils.request_context.set_request_context", create=True),
            patch("src.schemas.doc_input.DOCInput", create=True),
            patch("src.schemas.doc_output.DOCOutput", create=True),
        ):
            step = ClassificationStep()
            result = await step.execute(ctx)

        assert "classification" in result.step_results
        classification = result.step_results["classification"]
        assert classification["doc_type"] == "ACORD"
        assert classification["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_step_name_and_version(self) -> None:
        assert ClassificationStep.step_name == "classification"
        assert ClassificationStep.step_version == "v3"
