"""Tests for OcrStep."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.steps.ocr_step import OcrStep


@pytest.fixture()
def ctx_with_classification(sample_message: dict) -> PipelineContext:
    ctx = PipelineContext.from_message(sample_message)
    ctx.step_results["classification"] = {
        "attachment_id": "att-456",
        "doc_type": "ACORD",
        "confidence": 0.95,
        "document_url": "https://blob/src-raw-doc/doc.pdf",
    }
    return ctx


class TestOcrStep:
    @pytest.mark.asyncio
    async def test_execute_produces_ocr_result(
        self, ctx_with_classification: PipelineContext
    ) -> None:
        mock_ocr_output = SimpleNamespace(
            summary_json={"messageId": "msg-001", "pages": 5},
        )

        mock_ocr_service = MagicMock()
        mock_ocr_service.service.return_value = mock_ocr_output

        with (
            patch("src.schemas.doc_output.DOCOutput", create=True, return_value=SimpleNamespace(
                **ctx_with_classification.step_results["classification"]
            )),
            patch("src.services.ocr_service.OCRService", create=True, return_value=mock_ocr_service),
            patch("src.utils.request_context.set_request_context", create=True),
        ):
            step = OcrStep()
            result = await step.execute(ctx_with_classification)

        assert "ocr" in result.step_results
        assert result.step_results["ocr"]["summary_json"]["pages"] == 5

    @pytest.mark.asyncio
    async def test_missing_classification_raises(
        self, sample_context: PipelineContext
    ) -> None:
        step = OcrStep()
        with pytest.raises(ValueError, match="Classification result not found"):
            await step.execute(sample_context)

    @pytest.mark.asyncio
    async def test_step_name_and_version(self) -> None:
        assert OcrStep.step_name == "ocr"
        assert OcrStep.step_version == "v2"
