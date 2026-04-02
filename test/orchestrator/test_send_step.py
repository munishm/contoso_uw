"""Tests for SendStep."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.steps.send_step import SendStep


@pytest.fixture()
def ctx_with_ocr(sample_message: dict) -> PipelineContext:
    ctx = PipelineContext.from_message(sample_message)
    ctx.settings = {
        "front_end_url": "https://frontend.example.com/api",
        "key_vault_url": "https://vault.azure.net",
        "secret_name": "func-key",
    }
    ctx.step_results["ocr"] = {
        "summary_json": {"messageId": "msg-001", "pages": 5},
    }
    return ctx


@pytest.fixture()
def ctx_with_ner(case_message: dict) -> PipelineContext:
    ctx = PipelineContext.from_message(case_message)
    ctx.settings = {
        "front_end_url": "https://frontend.example.com/api",
        "key_vault_url": "https://vault.azure.net",
        "secret_name": "func-key",
    }
    ctx.step_results["ner"] = {
        "final_summary_json": {"entities": [{"name": "John"}]},
    }
    return ctx


def _mock_send_dependencies(mock_config):
    """Return a context manager that mocks all SendStep external dependencies."""
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
    mock_secret.value = "test-function-key"

    return (mock_session, mock_secret, mock_response)


class TestSendStep:
    @pytest.mark.asyncio
    async def test_send_ocr_result(self, ctx_with_ocr: PipelineContext) -> None:
        mock_session, mock_secret, _ = _mock_send_dependencies(None)

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("azure.identity.DefaultAzureCredential"),
            patch("azure.keyvault.secrets.SecretClient") as MockSC,
        ):
            MockSC.return_value.get_secret.return_value = mock_secret

            step = SendStep(config={"result_key": "ocr"})
            result = await step.execute(ctx_with_ocr)

        assert result.step_results["send"]["status"] == "sent"
        assert result.step_results["send"]["message_id"] == "msg-001"

    @pytest.mark.asyncio
    async def test_send_ner_result(self, ctx_with_ner: PipelineContext) -> None:
        mock_session, mock_secret, _ = _mock_send_dependencies(None)

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            patch("azure.identity.DefaultAzureCredential"),
            patch("azure.keyvault.secrets.SecretClient") as MockSC,
        ):
            MockSC.return_value.get_secret.return_value = mock_secret

            step = SendStep(config={"result_key": "ner"})
            result = await step.execute(ctx_with_ner)

        assert result.step_results["send"]["status"] == "sent"

    @pytest.mark.asyncio
    async def test_missing_result_key_raises(
        self, sample_context: PipelineContext
    ) -> None:
        step = SendStep(config={"result_key": "nonexistent"})
        with pytest.raises(ValueError, match="No result found"):
            await step.execute(sample_context)


class TestEnvVarExpansion:
    def test_resolve_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_URL", "https://custom.example.com")
        step = SendStep(config={"url": "${MY_URL}"})
        resolved = step._resolve_config("url", "default")
        assert resolved == "https://custom.example.com"

    def test_resolve_missing_env_var_uses_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MISSING_VAR", raising=False)
        step = SendStep(config={"url": "${MISSING_VAR}"})
        resolved = step._resolve_config("url", "fallback")
        assert resolved == "fallback"

    def test_resolve_literal_value(self) -> None:
        step = SendStep(config={"url": "https://literal.com"})
        resolved = step._resolve_config("url", "default")
        assert resolved == "https://literal.com"

    def test_resolve_missing_key_uses_default(self) -> None:
        step = SendStep(config={})
        resolved = step._resolve_config("url", "default")
        assert resolved == "default"

    @pytest.mark.asyncio
    async def test_step_name_and_version(self) -> None:
        assert SendStep.step_name == "send"
        assert SendStep.step_version == "v1"
