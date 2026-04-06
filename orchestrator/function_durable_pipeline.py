import json
import logging

import azure.functions as func

from src.config.settings import config_settings
from src.orchestrator.durable_adapter import (
    decode_queue_message,
    execute_step_activity,
    run_orchestrator,
)

logger = logging.getLogger(__name__)

bp = func.Blueprint()

_queue_name = config_settings.queneu_name_in_doc + "durable"


@bp.queue_trigger(
    arg_name="msg",
    queue_name=_queue_name,
    connection="INStorage",
)
@bp.durable_client_input(client_name="df_client")
async def pipeline_queue_trigger(
    msg: func.QueueMessage,
    df_client,
) -> None:
    """Queue trigger — decode message and start the durable orchestration."""
    try:
        message = decode_queue_message(msg.get_body())
        logger.info(
            "Starting pipeline orchestration  requestType=%s  messageId=%s",
            message.get("requestType"),
            message.get("messageId"),
        )
        instance_id = await df_client.start_new(
            orchestration_function_name="pipeline_orchestrator",
            instance_id=None,
            client_input=message,
        )
        logger.info("Started orchestration ID='%s'", instance_id)
    except Exception as e:
        logger.error("Error processing pipeline queue message: %s", e)
        raise


@bp.orchestration_trigger(context_name="context")
def pipeline_orchestrator(context):
    """Orchestrator — deterministic generator delegating to run_orchestrator."""
    return run_orchestrator(context)


@bp.activity_trigger(input_name="activity_input")
async def pipeline_step_activity(activity_input: dict) -> dict:
    """Activity — execute a single pipeline step."""
    return await execute_step_activity(activity_input)


@bp.route(
    route="pipeline/test",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)

@bp.durable_client_input(client_name="df_client")
async def pipeline_http_test_trigger(
    req: func.HttpRequest,
    df_client,
) -> func.HttpResponse:
    """HTTP POST — E2E test trigger (same payload as queue, no queue needed)."""
    try:
        message = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    request_type = message.get("requestType", "")
    message_id = message.get("messageId", "")

    if not request_type:
        return func.HttpResponse(
            json.dumps({"error": "Missing required field: requestType"}),
            status_code=400,
            mimetype="application/json",
        )

    logger.info(
        "HTTP test trigger  requestType=%s  messageId=%s",
        request_type,
        message_id,
    )

    instance_id = await df_client.start_new(
        orchestration_function_name="pipeline_orchestrator",
        instance_id=None,
        client_input=message,
    )

    status_uri = df_client.create_http_management_payload(instance_id)

    return func.HttpResponse(
        json.dumps(
            {
                "instanceId": instance_id,
                "statusQueryGetUri": status_uri.get("statusQueryGetUri", ""),
            }
        ),
        status_code=202,
        mimetype="application/json",
    )
