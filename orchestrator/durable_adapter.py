"""Pure business logic for the pipeline orchestrator (Durable Functions).

Wraps :class:`PipelineEngine` for Azure Durable Functions so that each step
becomes a ``call_activity`` (checkpointed, independently scalable) and parallel
stages use ``task_all`` (fan-out / fan-in).

This module contains **only** pure logic — no Azure Functions decorators or
wiring.  The durable function handlers live in ``function_durable_pipeline.py``
and decorators are applied at module level in ``function_app.py``.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Any

from src.config.settings import config_settings

from src.orchestrator.config import get_pipeline_for_request
from src.orchestrator.context import PipelineContext
from src.orchestrator.registry import StepRegistry

# Ensure all steps are registered
import src.orchestrator.steps  # noqa: F401

logger = logging.getLogger(__name__)


def _settings_from_config() -> dict[str, Any]:
    """Read all environment-driven settings from config_settings into a plain
    dict.  This is called once when the context is created and flows through
    every step via ``context.settings``.
    """
    return {
        "in_storage_blob_account_url": getattr(config_settings, "in_storage_blob_account_url", ""),
        "incoming_container": getattr(config_settings, "incoming_container", ""),
        "src_raw_container": getattr(config_settings, "src_raw_container", ""),
        "out_data_blob_container": getattr(config_settings, "out_data_blob_container", ""),
        "ocr_output_folder": getattr(config_settings, "ocr_output_folder", ""),
        "front_end_url": getattr(config_settings, "front_end_url", ""),
        "key_vault_url": getattr(config_settings, "key_vault_url", ""),
        "secret_name": getattr(config_settings, "secret_name", ""),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Core logic — pure functions, easy to unit-test
# ═══════════════════════════════════════════════════════════════════════════

def decode_queue_message(raw: bytes) -> dict:
    """Decode a queue message body (raw JSON or base64-encoded)."""
    text = raw.decode("utf-8")
    try:
        decoded = base64.b64decode(text).decode("utf-8")
        return json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        return json.loads(text)


def build_activity_input(
    ctx_dict: dict, step_def: dict, stage_name: str
) -> dict:
    """Package the context and step definition for the activity."""
    return {
        "context": ctx_dict,
        "step_def": step_def,
        "stage_name": stage_name,
    }


def run_orchestrator(context: Any):
    """Core orchestrator logic as a generator.

    ``context`` must expose ``get_input()``, ``call_activity(name, input)``,
    and ``task_all(tasks)``.

    Yields Durable Functions tasks; receives their resolved results via
    ``.send()``.

    .. note::
        This function **must** remain deterministic — no ``datetime.now()``,
        no I/O, no random calls.
    """
    message = context.get_input()
    if isinstance(message, str):
        message = json.loads(message)

    request_type = message.get("requestType", "")
    message_id = message.get("messageId", "")

    ctx = PipelineContext.from_message(message)
    ctx.settings = _settings_from_config()
    ctx_dict = ctx.to_dict()

    pipeline_def = get_pipeline_for_request(request_type)
    pipeline_name = pipeline_def["pipeline"]["name"]
    stages = pipeline_def["pipeline"].get("stages", [])

    logger.info(
        "Pipeline '%s' starting  requestType=%s  messageId=%s",
        pipeline_name, request_type, message_id,
    )

    for stage_def in stages:
        stage_name = stage_def.get("name", "unnamed")
        steps = stage_def.get("steps", [])
        parallel = stage_def.get("parallel", False)

        if parallel and len(steps) > 1:
            tasks = [
                context.call_activity(
                    "pipeline_step_activity",
                    build_activity_input(ctx_dict, sd, stage_name),
                )
                for sd in steps
            ]
            results = yield context.task_all(tasks)

            for result_ctx in results:
                ctx_dict["step_results"].update(
                    result_ctx.get("step_results", {})
                )
                for err in result_ctx.get("errors", []):
                    if err not in ctx_dict["errors"]:
                        ctx_dict["errors"].append(err)
        else:
            for step_def in steps:
                ctx_dict = yield context.call_activity(
                    "pipeline_step_activity",
                    build_activity_input(ctx_dict, step_def, stage_name),
                )

    logger.info("Pipeline '%s' completed  messageId=%s", pipeline_name, message_id)

    return {
        "messageId": message_id,
        "pipeline": pipeline_name,
        "step_results": ctx_dict.get("step_results", {}),
        "errors": ctx_dict.get("errors", []),
    }


async def execute_step_activity(activity_input: dict) -> dict:
    """Execute a single pipeline step (the activity body).

    Receives the serialized :class:`PipelineContext` plus the step definition,
    resolves the step from the registry, runs it, and returns the updated
    context dict.
    """
    ctx_dict = activity_input["context"]
    step_def = activity_input["step_def"]
    stage_name = activity_input["stage_name"]

    step_name = step_def["name"]
    step_version = step_def.get("version", "v1")
    on_failure = step_def.get("on_failure", "stop")
    config = step_def.get("config", {})

    ctx = PipelineContext.from_dict(ctx_dict)

    logger.info(
        "Activity executing step '%s' v%s  stage=%s  messageId=%s",
        step_name, step_version, stage_name, ctx.message_id,
    )

    step_cls = StepRegistry.get(step_name, step_version)
    step = step_cls(config=config)

    try:
        if on_failure == "retry":
            ctx = await _execute_with_retry(step, ctx, step_name, step_def)
        else:
            ctx = await step.execute(ctx)
        logger.info("Step '%s' completed successfully", step_name)
    except Exception as exc:
        error_info = {"stage": stage_name, "step": step_name, "error": str(exc)}
        if on_failure == "skip":
            logger.warning("Step '%s' failed (skipping): %s", step_name, exc)
            ctx.errors.append(error_info)
        else:
            logger.error("Step '%s' failed (stopping): %s", step_name, exc)
            ctx.errors.append(error_info)
            raise

    return ctx.to_dict()


async def _execute_with_retry(
    step, ctx: PipelineContext, step_name: str, step_def: dict, max_retries: int = 3,
) -> PipelineContext:
    """Retry a step with exponential backoff inside the activity."""
    import asyncio

    fallback = step_def.get("retry_fallback", "stop")
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return await step.execute(ctx)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = 2 ** attempt
                logger.warning(
                    "Step '%s' attempt %d/%d failed: %s — retrying in %ds",
                    step_name, attempt, max_retries, exc, delay,
                )
                await asyncio.sleep(delay)

    if fallback == "skip":
        logger.warning("Step '%s' retries exhausted (skipping): %s", step_name, last_exc)
        ctx.errors.append({"step": step_name, "error": str(last_exc), "retries_exhausted": True})
        return ctx
    raise last_exc
