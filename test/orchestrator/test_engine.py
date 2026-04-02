"""Tests for PipelineEngine."""

from __future__ import annotations

import asyncio

import pytest

from src.orchestrator.context import PipelineContext
from src.orchestrator.engine import PipelineEngine
from src.orchestrator.registry import register_step
from src.orchestrator.steps.base import Step


# ---------------------------------------------------------------------------
# Helper steps for engine tests
# ---------------------------------------------------------------------------

@register_step("engine_step_a", "v1")
class EngineStepA(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        context.step_results["a"] = "done"
        return context


@register_step("engine_step_b", "v1")
class EngineStepB(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        context.step_results["b"] = "done"
        return context


@register_step("engine_step_fail", "v1")
class EngineStepFail(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise RuntimeError("intentional failure")


_retry_counter = 0


@register_step("engine_step_flaky", "v1")
class EngineStepFlaky(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        global _retry_counter
        _retry_counter += 1
        if _retry_counter < 3:
            raise RuntimeError(f"flaky attempt {_retry_counter}")
        context.step_results["flaky"] = "recovered"
        return context


@register_step("engine_step_slow", "v1")
class EngineStepSlow(Step):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        await asyncio.sleep(0.05)
        context.step_results["slow"] = "done"
        return context


# ---------------------------------------------------------------------------
# Pipeline definition helpers
# ---------------------------------------------------------------------------

def _pipeline(stages: list) -> dict:
    return {
        "pipeline": {
            "name": "test_pipeline",
            "version": "1.0",
            "stages": stages,
        }
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSequentialExecution:
    @pytest.mark.asyncio
    async def test_two_stages_sequential(self, sample_context: PipelineContext) -> None:
        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [{"name": "engine_step_a", "version": "v1"}],
            },
            {
                "name": "stage2",
                "steps": [{"name": "engine_step_b", "version": "v1"}],
            },
        ])

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        assert result.step_results["a"] == "done"
        assert result.step_results["b"] == "done"
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_empty_pipeline(self, sample_context: PipelineContext) -> None:
        engine = PipelineEngine(_pipeline([]))
        result = await engine.run(sample_context)
        assert result.step_results == {}


class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_parallel_steps(self, sample_context: PipelineContext) -> None:
        pipeline_def = _pipeline([
            {
                "name": "parallel_stage",
                "parallel": True,
                "steps": [
                    {"name": "engine_step_a", "version": "v1"},
                    {"name": "engine_step_b", "version": "v1"},
                ],
            },
        ])

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        assert result.step_results["a"] == "done"
        assert result.step_results["b"] == "done"


class TestFailurePolicies:
    @pytest.mark.asyncio
    async def test_on_failure_stop(self, sample_context: PipelineContext) -> None:
        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [
                    {"name": "engine_step_fail", "version": "v1", "on_failure": "stop"},
                ],
            },
            {
                "name": "stage2",
                "steps": [{"name": "engine_step_a", "version": "v1"}],
            },
        ])

        engine = PipelineEngine(pipeline_def)

        with pytest.raises(RuntimeError, match="intentional failure"):
            await engine.run(sample_context)

        # Step A should not have run
        assert "a" not in sample_context.step_results

    @pytest.mark.asyncio
    async def test_on_failure_skip(self, sample_context: PipelineContext) -> None:
        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [
                    {"name": "engine_step_fail", "version": "v1", "on_failure": "skip"},
                ],
            },
            {
                "name": "stage2",
                "steps": [{"name": "engine_step_a", "version": "v1"}],
            },
        ])

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        # Pipeline continued past the failure
        assert result.step_results["a"] == "done"
        # Error was recorded
        assert len(result.errors) == 1
        assert result.errors[0]["step"] == "engine_step_fail"

    @pytest.mark.asyncio
    async def test_on_failure_retry_recovers(self, sample_context: PipelineContext) -> None:
        global _retry_counter
        _retry_counter = 0

        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [
                    {"name": "engine_step_flaky", "version": "v1", "on_failure": "retry"},
                ],
            },
        ])

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        assert result.step_results["flaky"] == "recovered"
        assert _retry_counter == 3

    @pytest.mark.asyncio
    async def test_on_failure_retry_exhausted_stops(self, sample_context: PipelineContext) -> None:
        """When all retries are exhausted, default fallback is stop."""
        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [
                    {"name": "engine_step_fail", "version": "v1", "on_failure": "retry"},
                ],
            },
        ])

        engine = PipelineEngine(pipeline_def)

        with pytest.raises(RuntimeError, match="intentional failure"):
            await engine.run(sample_context)

    @pytest.mark.asyncio
    async def test_on_failure_retry_exhausted_skip(self, sample_context: PipelineContext) -> None:
        """When retries exhaust with retry_fallback=skip, pipeline continues."""
        pipeline_def = _pipeline([
            {
                "name": "stage1",
                "steps": [
                    {
                        "name": "engine_step_fail",
                        "version": "v1",
                        "on_failure": "retry",
                        "retry_fallback": "skip",
                    },
                ],
            },
            {
                "name": "stage2",
                "steps": [{"name": "engine_step_a", "version": "v1"}],
            },
        ])

        engine = PipelineEngine(pipeline_def)
        result = await engine.run(sample_context)

        assert result.step_results["a"] == "done"
        assert any(e.get("retries_exhausted") for e in result.errors)


class TestEngineMetadata:
    def test_pipeline_name_and_version(self) -> None:
        engine = PipelineEngine({
            "pipeline": {"name": "my_pipe", "version": "2.5", "stages": []}
        })
        assert engine.name == "my_pipe"
        assert engine.version == "2.5"
