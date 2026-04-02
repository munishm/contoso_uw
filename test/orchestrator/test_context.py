"""Tests for PipelineContext."""

from __future__ import annotations

import json

from src.orchestrator.context import PipelineContext


class TestPipelineContextCreation:
    def test_from_message(self, sample_message: dict) -> None:
        ctx = PipelineContext.from_message(sample_message)

        assert ctx.request_type == "DocumentSummary"
        assert ctx.message_id == "msg-001"
        assert ctx.timestamp == "2026-03-26T10:00:00Z"
        assert ctx.record_id == "rec-123"
        assert len(ctx.payload) == 1
        assert ctx.payload[0]["attachmentId"] == "att-456"
        assert ctx.correlation_id == "msg-001"
        assert ctx.raw_message == sample_message
        assert ctx.step_results == {}
        assert ctx.errors == []

    def test_default_correlation_id(self) -> None:
        ctx = PipelineContext()
        assert ctx.correlation_id  # auto-generated UUID

    def test_correlation_id_falls_back_to_uuid(self) -> None:
        ctx = PipelineContext.from_message({})
        assert len(ctx.correlation_id) == 36  # UUID format


class TestPipelineContextSerialization:
    def test_round_trip(self, sample_message: dict) -> None:
        original = PipelineContext.from_message(sample_message)
        original.step_results["classification"] = {"doc_type": "ACORD"}
        original.errors.append({"step": "x", "error": "boom"})

        data = original.to_dict()
        restored = PipelineContext.from_dict(data)

        assert restored.request_type == original.request_type
        assert restored.message_id == original.message_id
        assert restored.step_results == original.step_results
        assert restored.errors == original.errors
        assert restored.payload == original.payload
        assert restored.correlation_id == original.correlation_id

    def test_json_serializable(self, sample_message: dict) -> None:
        ctx = PipelineContext.from_message(sample_message)
        ctx.step_results["ocr"] = {"summary_json": {"pages": 3}}

        serialized = json.dumps(ctx.to_dict())
        deserialized = json.loads(serialized)
        restored = PipelineContext.from_dict(deserialized)

        assert restored.step_results["ocr"]["summary_json"]["pages"] == 3
