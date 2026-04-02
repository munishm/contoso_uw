"""PipelineContext: carries data through every step of a pipeline."""

from __future__ import annotations

import uuid as uuid_mod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineContext:
    """Mutable context that flows through every pipeline step.

    All fields use primitive and dict types only so the context remains
    JSON-serializable across Durable Functions activity boundaries.
    """

    request_type: str = ""
    message_id: str = ""
    timestamp: str = ""
    record_id: str = ""
    payload: list[dict[str, Any]] = field(default_factory=list)
    step_results: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    correlation_id: str = ""
    raw_message: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.correlation_id:
            self.correlation_id = self.message_id or str(uuid_mod.uuid4())

    # -- serialization helpers ------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize the context to a plain dictionary."""
        return {
            "request_type": self.request_type,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "record_id": self.record_id,
            "payload": self.payload,
            "step_results": self.step_results,
            "errors": self.errors,
            "correlation_id": self.correlation_id,
            "raw_message": self.raw_message,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineContext:
        """Reconstruct a context from a dictionary."""
        return cls(**data)

    @classmethod
    def from_message(cls, message: dict[str, Any]) -> PipelineContext:
        """Create a context from an incoming queue message."""
        return cls(
            request_type=message.get("requestType", ""),
            message_id=message.get("messageId", ""),
            timestamp=message.get("timestamp", ""),
            record_id=message.get("recordId", ""),
            payload=message.get("payload", []),
            correlation_id=message.get("messageId", str(uuid_mod.uuid4())),
            raw_message=message,
        )
