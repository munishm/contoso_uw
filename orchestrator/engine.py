"""PipelineEngine: reads a pipeline definition and executes stages in order."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .context import PipelineContext
from .registry import StepRegistry

logger = logging.getLogger(__name__)


class PipelineEngine:
    """Loads a pipeline definition, resolves steps from the registry, and
    executes stages in order.

    * Stages run **sequentially**.
    * Steps within a stage run in **parallel** when ``parallel: true`` is set
      on the stage (uses ``asyncio.gather``); otherwise they run sequentially.
    * Each step supports an ``on_failure`` policy: ``stop`` (default),
      ``skip``, or ``retry``.
    """

    def __init__(self, pipeline_def: dict[str, Any]) -> None:
        pipeline = pipeline_def.get("pipeline", {})
        self.name: str = pipeline.get("name", "unknown")
        self.version: str = pipeline.get("version", "0.0")
        self.stages: list[dict[str, Any]] = pipeline.get("stages", [])

    # -- public API -----------------------------------------------------------

    async def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the full pipeline and return the final context."""
        logger.info(
            "Pipeline '%s' v%s starting  correlation_id=%s",
            self.name,
            self.version,
            context.correlation_id,
        )

        for stage_def in self.stages:
            stage_name = stage_def.get("name", "unnamed")
            steps = stage_def.get("steps", [])
            parallel = stage_def.get("parallel", False)

            logger.info(
                "Stage '%s' starting (%s)",
                stage_name,
                "parallel" if parallel else "sequential",
            )

            if parallel:
                context = await self._run_parallel(stage_name, steps, context)
            else:
                context = await self._run_sequential(stage_name, steps, context)

            logger.info("Stage '%s' completed", stage_name)

        logger.info("Pipeline '%s' completed successfully", self.name)
        return context

    # -- internals ------------------------------------------------------------

    async def _run_sequential(
        self,
        stage_name: str,
        step_defs: list[dict[str, Any]],
        context: PipelineContext,
    ) -> PipelineContext:
        for step_def in step_defs:
            context = await self._execute_step(stage_name, step_def, context)
        return context

    async def _run_parallel(
        self,
        stage_name: str,
        step_defs: list[dict[str, Any]],
        context: PipelineContext,
    ) -> PipelineContext:
        tasks = [
            self._execute_step(stage_name, step_def, context)
            for step_def in step_defs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                raise result
            context.step_results.update(result.step_results)
            context.errors.extend(
                e for e in result.errors if e not in context.errors
            )

        return context

    async def _execute_step(
        self,
        stage_name: str,
        step_def: dict[str, Any],
        context: PipelineContext,
    ) -> PipelineContext:
        step_name = step_def["name"]
        step_version = step_def.get("version", "v1")
        on_failure = step_def.get("on_failure", "stop")
        config = step_def.get("config", {})

        step_cls = StepRegistry.get(step_name, step_version)
        step = step_cls(config=config)

        logger.info("Step '%s' v%s executing", step_name, step_version)
        start = time.monotonic()

        try:
            if on_failure == "retry":
                context = await self._execute_with_retry(
                    step, context, step_name, step_def
                )
            else:
                context = await step.execute(context)

            elapsed = time.monotonic() - start
            logger.info("Step '%s' completed in %.2fs", step_name, elapsed)

        except Exception as exc:
            elapsed = time.monotonic() - start
            error_info: dict[str, Any] = {
                "stage": stage_name,
                "step": step_name,
                "error": str(exc),
                "elapsed": round(elapsed, 4),
            }

            if on_failure == "skip":
                logger.warning("Step '%s' failed (skipping): %s", step_name, exc)
                context.errors.append(error_info)
            else:  # stop
                logger.error(
                    "Step '%s' failed (stopping pipeline): %s", step_name, exc
                )
                context.errors.append(error_info)
                raise

        return context

    async def _execute_with_retry(
        self,
        step: Any,
        context: PipelineContext,
        step_name: str,
        step_def: dict[str, Any],
        max_retries: int = 3,
    ) -> PipelineContext:
        fallback = step_def.get("retry_fallback", "stop")
        last_exc: BaseException | None = None

        for attempt in range(1, max_retries + 1):
            try:
                return await step.execute(context)
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    delay = 2**attempt
                    logger.warning(
                        "Step '%s' attempt %d/%d failed: %s  — retrying in %ds",
                        step_name,
                        attempt,
                        max_retries,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        if fallback == "skip":
            logger.warning(
                "Step '%s' retries exhausted (skipping): %s",
                step_name,
                last_exc,
            )
            context.errors.append(
                {
                    "step": step_name,
                    "error": str(last_exc),
                    "retries_exhausted": True,
                }
            )
            return context

        raise last_exc  # type: ignore[misc]
