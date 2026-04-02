"""Shared fixtures for orchestrator tests."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Pre-create mock modules for packages not installed in the test environment.
# This lets step code do ``from azure.identity import ...`` without crashing.
# ---------------------------------------------------------------------------

def _passthrough_decorator(*args, **kwargs):
    """Decorator mock that returns the original function unchanged."""
    def decorator(fn):
        return fn
    return decorator

# Build mock azure.functions module with passthrough decorators
_mock_func = MagicMock()
_mock_bp = MagicMock()
_mock_bp.queue_trigger = _passthrough_decorator
_mock_bp.durable_client_input = _passthrough_decorator
_mock_bp.orchestration_trigger = _passthrough_decorator
_mock_bp.activity_trigger = _passthrough_decorator
_mock_func.Blueprint.return_value = _mock_bp

for _mod in (
    "azure",
    "azure.identity",
    "azure.keyvault",
    "azure.keyvault.secrets",
    "azure.functions.durable_functions",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Override azure.functions with our properly configured mock
sys.modules["azure.functions"] = _mock_func

# Pre-create config_settings so the durable adapter can import it at module level
import src.config.settings as _settings_mod
if not hasattr(_settings_mod, "config_settings"):
    _settings_mod.config_settings = MagicMock()
    _settings_mod.config_settings.queneu_name_in_doc = "test-queue-"

from src.orchestrator.context import PipelineContext
from src.orchestrator.registry import StepRegistry


@pytest.fixture(autouse=True)
def _clean_registry():
    """Clear the step registry before each test so registrations don't leak."""
    saved = dict(StepRegistry._steps)
    yield
    StepRegistry._steps = saved


@pytest.fixture()
def sample_message() -> dict:
    """A minimal DocumentSummary queue message."""
    return {
        "requestType": "DocumentSummary",
        "messageId": "msg-001",
        "timestamp": "2026-03-26T10:00:00Z",
        "recordId": "rec-123",
        "payload": [
            {
                "attachmentId": "att-456",
                "urlOfContainer": "https://storage.blob.core.windows.net/incoming/doc.pdf",
            }
        ],
    }


@pytest.fixture()
def case_message() -> dict:
    """A minimal CaseSummary queue message."""
    return {
        "requestType": "CaseSummary",
        "messageId": "msg-002",
        "timestamp": "2026-03-26T11:00:00Z",
        "recordId": "rec-456",
        "payload": [
            {
                "attachmentId": "att-100",
                "urlOfContainer": "https://storage.blob.core.windows.net/incoming/a.pdf",
            },
            {
                "attachmentId": "att-101",
                "urlOfContainer": "https://storage.blob.core.windows.net/incoming/b.pdf",
            },
        ],
    }


@pytest.fixture()
def sample_context(sample_message: dict) -> PipelineContext:
    """A PipelineContext built from the sample DocumentSummary message."""
    ctx = PipelineContext.from_message(sample_message)
    ctx.settings = TEST_SETTINGS.copy()
    return ctx


@pytest.fixture()
def case_context(case_message: dict) -> PipelineContext:
    """A PipelineContext built from the sample CaseSummary message."""
    ctx = PipelineContext.from_message(case_message)
    ctx.settings = TEST_SETTINGS.copy()
    return ctx


TEST_SETTINGS: dict = {
    "in_storage_blob_account_url": "https://account.blob.core.windows.net",
    "incoming_container": "incoming-doc",
    "src_raw_container": "src-raw-doc",
    "out_data_blob_container": "out-container",
    "ocr_output_folder": "output/",
    "front_end_url": "https://frontend.example.com/api",
    "key_vault_url": "https://vault.azure.net",
    "secret_name": "func-key",
}
