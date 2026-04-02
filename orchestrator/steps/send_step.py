"""SendStep v1: deliver pipeline results to the front-end API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from ..registry import register_step
from ..context import PipelineContext
from .base import Step

logger = logging.getLogger(__name__)


@register_step("send", "v1")
class SendStep(Step):
    """Retrieve the result identified by ``config.result_key`` from the
    pipeline context, fetch a function key from Azure Key Vault, and POST
    the result to a configurable front-end endpoint.

    Configuration (all with app-setting fallbacks):

    * ``result_key`` – key in ``step_results`` to send (default ``"ocr"``)
    * ``url`` – front-end URL (default: ``config_settings.front_end_url``)
    * ``key_vault_url`` – Key Vault URL
    * ``secret_name`` – secret name for the function key
    """

    async def execute(self, context: PipelineContext) -> PipelineContext:
        result_key = self.config.get("result_key", "ocr")
        step_result = context.step_results.get(result_key)

        if step_result is None:
            raise ValueError(
                f"No result found for key '{result_key}' in pipeline context"
            )

        import json
        import os

        import aiohttp
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        # Resolve endpoint configuration with fallback to context.settings
        url = self._resolve_config(
            "url", context.settings.get("front_end_url", "")
        )
        key_vault_url = self._resolve_config(
            "key_vault_url", context.settings.get("key_vault_url", "")
        )
        secret_name = self._resolve_config(
            "secret_name", context.settings.get("secret_name", "")
        )

        # Retrieve function key from Key Vault
        credential = DefaultAzureCredential()
        secret_client = SecretClient(
            vault_url=key_vault_url, credential=credential
        )
        string_key = secret_client.get_secret(secret_name).value
        if isinstance(string_key, bytes):
            string_key = string_key.decode("utf-8")

        headers = {
            "x-functions-key": string_key,
            "Content-Type": "application/json",
        }

        # Build the payload in the same shape as the existing send activity
        summary = (
            step_result.get("summary_json")
            or step_result.get("final_summary_json")
            or step_result
        )
        task_result = json.dumps(summary)

        payload = {
            "task_id": context.message_id,
            "task_name": "update_result_for_uw_documents",
            "task_result": task_result,
        }

        logger.info("Sending result to %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload
            ) as response:
                response_text = await response.text()
                logger.info(
                    "Response status: %s  body: %s",
                    response.status,
                    response_text[:200],
                )

        context.step_results["send"] = {
            "status": "sent",
            "message_id": context.message_id,
        }
        logger.info("Result delivered successfully")
        return context

    def _resolve_config(self, key: str, default: Any) -> Any:
        """Resolve a config value, expanding ``${ENV_VAR}`` placeholders."""
        value = self.config.get(key)
        if value is None:
            return default
        if (
            isinstance(value, str)
            and value.startswith("${")
            and value.endswith("}")
        ):
            env_var = value[2:-1]
            return os.environ.get(env_var, default)
        return value
