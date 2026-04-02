"""Tests for the Durable Functions adapter (durable_adapter.py).

These tests verify the core orchestrator logic, activity execution,
retry handling, and message decoding — all testable without Azure SDK.
"""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.registry import register_step, StepRegistry
from src.orchestrator.steps.base import Step
from src.orchestrator.durable_adapter import (
    build_activity_input,
    decode_queue_message,
    execute_step_activity,
    run_orchestrator,
)


# ---------------------------------------------------------------------------
# Lightweight test steps
# ---------------------------------------------------------------------------

@register_step("durable_test_a", "v1")
class DurableTestStepA(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        context.step_results["a"] = "done_a"
        return context


@register_step("durable_test_b", "v1")
class DurableTestStepB(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        context.step_results["b"] = "done_b"
        return context


@register_step("durable_test_fail", "v1")
class DurableTestStepFail(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise RuntimeError("activity boom")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TWO_STAGE_PIPELINE = {
    "pipeline": {
        "name": "test_durable",
        "version": "1.0",
        "stages": [
            {"name": "s1", "steps": [{"name": "durable_test_a", "version": "v1"}]},
            {"name": "s2", "steps": [{"name": "durable_test_b", "version": "v1"}]},
        ],
    }
}

PARALLEL_PIPELINE = {
    "pipeline": {
        "name": "test_parallel",
        "version": "1.0",
        "stages": [
            {
                "name": "parallel_stage",
                "parallel": True,
                "steps": [
                    {"name": "durable_test_a", "version": "v1"},
                    {"name": "durable_test_b", "version": "v1"},
                ],
            },
        ],
    }
}

SKIP_PIPELINE = {
    "pipeline": {
        "name": "test_skip",
        "version": "1.0",
        "stages": [
            {
                "name": "risky",
                "steps": [
                    {"name": "durable_test_fail", "version": "v1", "on_failure": "skip"},
                ],
            },
            {
                "name": "safe",
                "steps": [{"name": "durable_test_a", "version": "v1"}],
            },
        ],
    }
}


# ---------------------------------------------------------------------------
# Test: execute_step_activity
# ---------------------------------------------------------------------------

class TestExecuteStepActivity:
    """Test the activity function that executes a single step."""

    @pytest.mark.asyncio
    async def test_executes_step(self) -> None:
        ctx = PipelineContext.from_message({
            "requestType": "DocumentSummary",
            "messageId": "msg-act-1",
            "timestamp": "2026-03-26T10:00:00Z",
            "recordId": "rec-1",
            "payload": [],
        })

        activity_input = {
            "context": ctx.to_dict(),
            "step_def": {"name": "durable_test_a", "version": "v1"},
            "stage_name": "stage1",
        }

        result = await execute_step_activity(activity_input)

        assert result["step_results"]["a"] == "done_a"
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_on_failure_stop_raises(self) -> None:
        ctx = PipelineContext(message_id="msg-fail")
        activity_input = {
            "context": ctx.to_dict(),
            "step_def": {
                "name": "durable_test_fail",
                "version": "v1",
                "on_failure": "stop",
            },
            "stage_name": "stage1",
        }

        with pytest.raises(RuntimeError, match="activity boom"):
            await execute_step_activity(activity_input)

    @pytest.mark.asyncio
    async def test_on_failure_skip_continues(self) -> None:
        ctx = PipelineContext(message_id="msg-skip")
        activity_input = {
            "context": ctx.to_dict(),
            "step_def": {
                "name": "durable_test_fail",
                "version": "v1",
                "on_failure": "skip",
            },
            "stage_name": "stage1",
        }

        result = await execute_step_activity(activity_input)

        assert len(result["errors"]) == 1
        assert "activity boom" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_passes_config_to_step(self) -> None:
        @register_step("durable_cfg_test", "v1")
        class CfgStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                context.step_results["cfg"] = self.config.get("result_key", "none")
                return context

        ctx = PipelineContext(message_id="msg-cfg")
        activity_input = {
            "context": ctx.to_dict(),
            "step_def": {
                "name": "durable_cfg_test",
                "version": "v1",
                "config": {"result_key": "ocr"},
            },
            "stage_name": "s1",
        }

        result = await execute_step_activity(activity_input)
        assert result["step_results"]["cfg"] == "ocr"


# ---------------------------------------------------------------------------
# Test: run_orchestrator (the generator)
# ---------------------------------------------------------------------------

class TestRunOrchestrator:
    """Test the orchestrator generator with a mock context."""

    def test_sequential_stages(self) -> None:
        message = {
            "requestType": "DocumentSummary",
            "messageId": "msg-orch-1",
            "timestamp": "2026-03-26T10:00:00Z",
            "recordId": "rec-1",
            "payload": [],
        }

        ctx_after_a = PipelineContext.from_message(message)
        ctx_after_a.step_results["a"] = "done_a"
        ctx_after_b = PipelineContext.from_message(message)
        ctx_after_b.step_results.update({"a": "done_a", "b": "done_b"})

        mock_context = MagicMock()
        mock_context.get_input.return_value = message

        with patch(
            "src.orchestrator.durable_adapter.get_pipeline_for_request",
            return_value=TWO_STAGE_PIPELINE,
        ):
            gen = run_orchestrator(mock_context)

            # First yield: call_activity for step A
            task1 = next(gen)
            mock_context.call_activity.assert_called()
            args1 = mock_context.call_activity.call_args
            assert args1[0][0] == "pipeline_step_activity"
            assert args1[0][1]["step_def"]["name"] == "durable_test_a"

            # Send result of step A → yields call_activity for step B
            task2 = gen.send(ctx_after_a.to_dict())
            args2 = mock_context.call_activity.call_args
            assert args2[0][1]["step_def"]["name"] == "durable_test_b"

            # Send result of step B → generator returns final result
            try:
                gen.send(ctx_after_b.to_dict())
                pytest.fail("Generator should have returned")
            except StopIteration as e:
                final = e.value
                assert final["messageId"] == "msg-orch-1"
                assert final["pipeline"] == "test_durable"
                assert final["step_results"]["a"] == "done_a"
                assert final["step_results"]["b"] == "done_b"

    def test_parallel_stage_uses_task_all(self) -> None:
        message = {"requestType": "Test", "messageId": "msg-par-1", "payload": []}

        ctx_a = PipelineContext.from_message(message)
        ctx_a.step_results["a"] = "done_a"
        ctx_b = PipelineContext.from_message(message)
        ctx_b.step_results["b"] = "done_b"

        mock_context = MagicMock()
        mock_context.get_input.return_value = message

        with patch(
            "src.orchestrator.durable_adapter.get_pipeline_for_request",
            return_value=PARALLEL_PIPELINE,
        ):
            gen = run_orchestrator(mock_context)

            # First yield: task_all for parallel stage
            _task = next(gen)
            mock_context.task_all.assert_called_once()
            # Two call_activity calls were made (one per parallel step)
            assert mock_context.call_activity.call_count == 2

            # Send back list of results
            try:
                gen.send([ctx_a.to_dict(), ctx_b.to_dict()])
                pytest.fail("Generator should have returned")
            except StopIteration as e:
                final = e.value
                assert final["step_results"]["a"] == "done_a"
                assert final["step_results"]["b"] == "done_b"

    def test_string_message_input(self) -> None:
        """Orchestrator handles message passed as a JSON string."""
        message = {"requestType": "Test", "messageId": "msg-str", "payload": []}

        mock_context = MagicMock()
        mock_context.get_input.return_value = json.dumps(message)

        with patch(
            "src.orchestrator.durable_adapter.get_pipeline_for_request",
            return_value={"pipeline": {"name": "empty", "version": "1.0", "stages": []}},
        ):
            gen = run_orchestrator(mock_context)
            try:
                next(gen)
                pytest.fail("Generator should have returned (no stages)")
            except StopIteration as e:
                assert e.value["messageId"] == "msg-str"


# ---------------------------------------------------------------------------
# Test: decode_queue_message
# ---------------------------------------------------------------------------

class TestDecodeQueueMessage:
    def test_raw_json(self) -> None:
        message = {"requestType": "DocumentSummary", "messageId": "msg-q1"}
        raw = json.dumps(message).encode("utf-8")
        assert decode_queue_message(raw) == message

    def test_base64_encoded(self) -> None:
        message = {"requestType": "CaseSummary", "messageId": "msg-q2"}
        encoded = base64.b64encode(json.dumps(message).encode("utf-8"))
        assert decode_queue_message(encoded) == message


# ---------------------------------------------------------------------------
# Test: build_activity_input helper
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_build_activity_input(self) -> None:
        ctx_dict = {"message_id": "m1", "step_results": {}}
        step_def = {"name": "ocr", "version": "v2"}

        result = build_activity_input(ctx_dict, step_def, "extract")

        assert result["context"] == ctx_dict
        assert result["step_def"] == step_def
        assert result["stage_name"] == "extract"
