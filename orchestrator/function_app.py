import os
import sys
import azure.functions as func
import json
import logging

logger = logging.getLogger(__name__)

from function_warmup import bp as warmup_bp
from function_http import bp as http_bp
from function_queue import bp as queue_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

app.register_functions(warmup_bp)
app.register_functions(http_bp)


if os.environ.get("USE_PIPELINE_ORCHESTRATOR", "false").lower() == "true":
    from function_durable_pipeline import bp as durable_bp
    app.register_functions(durable_bp)
else:
    app.register_functions(queue_bp)
