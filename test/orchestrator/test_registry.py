"""Tests for StepRegistry."""

from __future__ import annotations

import pytest

from src.orchestrator.registry import StepRegistry, register_step
from src.orchestrator.steps.base import Step
from src.orchestrator.context import PipelineContext


class TestStepRegistration:
    def test_register_and_retrieve(self) -> None:
        @register_step("test_step", "v1")
        class TestStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        cls = StepRegistry.get("test_step", "v1")
        assert cls is TestStep

    def test_step_metadata(self) -> None:
        @register_step("meta_step", "v2")
        class MetaStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        assert MetaStep.step_name == "meta_step"
        assert MetaStep.step_version == "v2"

    def test_list_steps(self) -> None:
        @register_step("list_a", "v1")
        class StepA(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        @register_step("list_b", "v1")
        class StepB(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        steps = StepRegistry.list_steps()
        assert ("list_a", "v1") in steps
        assert ("list_b", "v1") in steps


class TestStepLookupFailures:
    def test_missing_step(self) -> None:
        with pytest.raises(KeyError, match="not_registered"):
            StepRegistry.get("not_registered", "v1")

    def test_wrong_version(self) -> None:
        @register_step("ver_step", "v1")
        class VerStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        with pytest.raises(KeyError, match="v99"):
            StepRegistry.get("ver_step", "v99")


class TestRegistryClear:
    def test_clear(self) -> None:
        @register_step("clear_step", "v1")
        class ClearStep(Step):
            async def execute(self, context: PipelineContext) -> PipelineContext:
                return context

        assert ("clear_step", "v1") in StepRegistry._steps
        StepRegistry.clear()
        assert ("clear_step", "v1") not in StepRegistry._steps
