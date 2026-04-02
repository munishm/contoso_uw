"""Integration tests: run full pipelines with mocked services."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.config import load_pipeline
from src.orchestrator.context import PipelineContext
from src.orchestrator.engine import PipelineEngine
from src.orchestrator.registry import StepRegistry, register_step
from src.orchestrator.steps.base import Step

# Ensure real steps are registered
import src.orchestrator.steps  # noqa: F401


PIPELINES_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "orchestrator"
    / "pipelines"
)


def _mock_send_context_managers():
    """Create mock session and secret for send step."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="OK")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_secret = MagicMock()
    mock_secret.value = "key-123"

    return mock_session, mock_secret


class TestDocumentSummaryPipeline:
    """Full DocumentSummary pipeline with all services mocked."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, sample_message: dict) -> None:
        ctx = PipelineContext.from_message(sample_message)
        ctx.settings = {
            "in_storage_blob_account_url": "https://account.blob.core.windows.net",
            "incoming_container": "incoming-doc",
            "src_raw_container": "src-raw-doc",
            "front_end_url": "https://frontend.example.com/api",
            "key_vault_url": "https://vault.azure.net",
            "secret_name": "func-key",
        }
        pipeline_def = load_pipeline("document_summary", pipelines_dir=PIPELINES_DIR)

        # -- Classification mocks --
        mock_doc_output = SimpleNamespace(
            attachment_id="att-456",
            doc_type="ACORD",
            confidence=0.95,
            document_url="https://blob/doc.pdf",
        )
        mock_sas_blob = MagicMock()
        mock_sas_blob.generate_sas_url.return_value = "https://sas"

        mock_blob_client_target = MagicMock()
        mock_azure_blob = MagicMock()
        mock_azure_blob.get_blob_client.return_value = mock_blob_client_target
        mock_azure_blob.get_blob_url.return_value = "https://blob/src-raw-doc/doc.pdf"

        blob_call_count = 0
        def blob_factory(**kwargs):
            nonlocal blob_call_count
            blob_call_count += 1
            if blob_call_count == 1:
                return mock_sas_blob
            return mock_azure_blob

        # -- OCR mocks --
        mock_ocr_output = SimpleNamespace(
            summary_json={"messageId": "msg-001", "pages": 5, "text": "Hello"},
        )

        # -- Send mocks --
        mock_session, mock_secret = _mock_send_context_managers()

        mock_classifier = MagicMock()
        mock_classifier.service.return_value = mock_doc_output

        mock_ocr_service = MagicMock()
        mock_ocr_service.service.return_value = mock_ocr_output

        with (
            # Classification patches
            patch("src.services.classifier_service.ClassifierService", create=True, return_value=mock_classifier),
            patch("src.utils.storage_blob.AzureStorageBlobClient", create=True, side_effect=blob_factory),
            patch("src.utils.request_context.set_request_context", create=True),
            patch("src.schemas.doc_input.DOCInput", create=True),
            # OCR patches
            patch("src.schemas.doc_output.DOCOutput", create=True, return_value=mock_doc_output),
            patch("src.services.ocr_service.OCRService", create=True, return_value=mock_ocr_service),
            # Send patches
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("azure.identity.DefaultAzureCredential"),
            patch("azure.keyvault.secrets.SecretClient") as MockSC,
        ):
            MockSC.return_value.get_secret.return_value = mock_secret

            engine = PipelineEngine(pipeline_def)
            result = await engine.run(ctx)

        assert "classification" in result.step_results
        assert "ocr" in result.step_results
        assert "send" in result.step_results
        assert result.step_results["send"]["status"] == "sent"
        assert result.errors == []


class TestCaseSummaryPipeline:
    """Full CaseSummary pipeline with all services mocked."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, case_message: dict) -> None:
        ctx = PipelineContext.from_message(case_message)
        ctx.settings = {
            "out_data_blob_container": "out-container",
            "ocr_output_folder": "output/",
            "front_end_url": "https://frontend.example.com/api",
            "key_vault_url": "https://vault.azure.net",
            "secret_name": "func-key",
        }
        pipeline_def = load_pipeline("case_summary", pipelines_dir=PIPELINES_DIR)

        # -- NER mocks --
        ocr_blob = json.dumps({"summary_json": {"pages": 2}}).encode()
        mock_ner_output = SimpleNamespace(
            final_summary_json={"entities": [{"name": "Alice"}]},
        )

        mock_blob_download = MagicMock()
        mock_blob_download.readall.return_value = ocr_blob

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

        # -- Send mocks --
        mock_session, mock_secret = _mock_send_context_managers()

        with (
            # NER patches
            patch("src.utils.storage_blob.AzureStorageBlobClient", create=True, return_value=mock_azure_blob),
            patch("src.utils.request_context.set_request_context", create=True),
            patch("src.schemas.ocr_output.OCROutput", create=True, return_value=SimpleNamespace(summary_json={"pages": 2})),
            patch("src.schemas.ner_input.NERInput", create=True, return_value=mock_ner_input),
            patch("src.services.ner_service.NERService", create=True, return_value=mock_ner_service),
            # Send patches
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("azure.identity.DefaultAzureCredential"),
            patch("azure.keyvault.secrets.SecretClient") as MockSC,
        ):
            MockSC.return_value.get_secret.return_value = mock_secret

            engine = PipelineEngine(pipeline_def)
            result = await engine.run(ctx)

        assert "ner" in result.step_results
        assert "send" in result.step_results
        assert result.step_results["send"]["status"] == "sent"
        assert result.errors == []


class TestSkipPolicyIntegration:
    """Test that on_failure: skip works across a full pipeline."""

    @pytest.mark.asyncio
    async def test_failing_step_skipped(self, sample_context: PipelineContext) -> None:
        @register_step("int_pass", "v1")
        class PassStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                context.step_results["pass"] = "ok"
                return context

        @register_step("int_fail", "v1")
        class FailStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                raise RuntimeError("kaboom")

        pipeline_def = {
            "pipeline": {
                "name": "skip_test",
                "version": "1.0",
                "stages": [
                    {
                        "name": "risky",
                        "steps": [
                            {"name": "int_fail", "version": "v1", "on_failure": "skip"},
                        ],
                    },
                    {
                        "name": "safe",
                        "steps": [
                            {"name": "int_pass", "version": "v1"},
                        ],
                    },
                ],
            }
        }

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        assert result.step_results["pass"] == "ok"
        assert len(result.errors) == 1
        assert "kaboom" in result.errors[0]["error"]
