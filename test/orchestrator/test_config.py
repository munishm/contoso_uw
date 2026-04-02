"""Tests for pipeline configuration loading and validation."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.orchestrator.config import (
    DEFAULT_PIPELINE_MAP,
    _validate_pipeline,
    get_pipeline_for_request,
    get_pipeline_map,
    load_pipeline,
    validate_all_pipelines,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(directory: Path, name: str, content: dict) -> Path:
    path = directory / f"{name}.yaml"
    path.write_text(yaml.dump(content))
    return path


VALID_PIPELINE = {
    "pipeline": {
        "name": "test",
        "version": "1.0",
        "stages": [
            {
                "name": "stage1",
                "steps": [{"name": "step1", "version": "v1"}],
            }
        ],
    }
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadPipeline:
    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path, "my_pipe", VALID_PIPELINE)
        result = load_pipeline("my_pipe", pipelines_dir=tmp_path)
        assert result["pipeline"]["name"] == "test"

    def test_load_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="nope"):
            load_pipeline("nope", pipelines_dir=tmp_path)

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "bad.yaml").write_text("not_a_pipeline: true")
        with pytest.raises(ValueError, match="pipeline"):
            load_pipeline("bad", pipelines_dir=tmp_path)


class TestValidation:
    def test_missing_pipeline_key(self) -> None:
        with pytest.raises(ValueError, match="Missing 'pipeline'"):
            _validate_pipeline({"stages": []})

    def test_missing_name(self) -> None:
        with pytest.raises(ValueError, match="pipeline.name"):
            _validate_pipeline({"pipeline": {"stages": []}})

    def test_missing_stages(self) -> None:
        with pytest.raises(ValueError, match="pipeline.stages"):
            _validate_pipeline({"pipeline": {"name": "x"}})

    def test_stage_missing_name(self) -> None:
        with pytest.raises(ValueError, match="Stage 0 missing 'name'"):
            _validate_pipeline(
                {"pipeline": {"name": "x", "stages": [{"steps": [{"name": "s"}]}]}}
            )

    def test_stage_empty_steps(self) -> None:
        with pytest.raises(ValueError, match="no steps"):
            _validate_pipeline(
                {"pipeline": {"name": "x", "stages": [{"name": "s", "steps": []}]}}
            )

    def test_step_missing_name(self) -> None:
        with pytest.raises(ValueError, match="missing 'name'"):
            _validate_pipeline(
                {
                    "pipeline": {
                        "name": "x",
                        "stages": [{"name": "s", "steps": [{"version": "v1"}]}],
                    }
                }
            )

    def test_valid_pipeline_passes(self) -> None:
        _validate_pipeline(VALID_PIPELINE)  # should not raise


class TestPipelineMap:
    def test_default_map(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PIPELINE_MAP", raising=False)
        result = get_pipeline_map()
        assert result == DEFAULT_PIPELINE_MAP

    def test_custom_map_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        custom = {"DocSum": "custom_doc"}
        monkeypatch.setenv("PIPELINE_MAP", json.dumps(custom))
        result = get_pipeline_map()
        assert result == custom

    def test_invalid_json_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PIPELINE_MAP", "not json")
        result = get_pipeline_map()
        assert result == DEFAULT_PIPELINE_MAP


class TestGetPipelineForRequest:
    def test_document_summary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PIPELINE_MAP", raising=False)
        pipelines_dir = Path(__file__).resolve().parent.parent.parent / "src" / "orchestrator" / "pipelines"
        result = get_pipeline_for_request("DocumentSummary", pipelines_dir=pipelines_dir)
        assert result["pipeline"]["name"] == "document_summary"

    def test_case_summary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PIPELINE_MAP", raising=False)
        pipelines_dir = Path(__file__).resolve().parent.parent.parent / "src" / "orchestrator" / "pipelines"
        result = get_pipeline_for_request("CaseSummary", pipelines_dir=pipelines_dir)
        assert result["pipeline"]["name"] == "case_summary"

    def test_unknown_request_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PIPELINE_MAP", raising=False)
        with pytest.raises(ValueError, match="UnknownType"):
            get_pipeline_for_request("UnknownType")


class TestValidateAllPipelines:
    def test_all_bundled_pipelines_valid(self) -> None:
        pipelines_dir = Path(__file__).resolve().parent.parent.parent / "src" / "orchestrator" / "pipelines"
        errors = validate_all_pipelines(pipelines_dir=pipelines_dir)
        assert errors == [], f"Pipeline validation errors: {errors}"

    def test_reports_errors(self, tmp_path: Path) -> None:
        (tmp_path / "broken.yaml").write_text("broken: true")
        errors = validate_all_pipelines(pipelines_dir=tmp_path)
        assert len(errors) == 1
        assert "broken.yaml" in errors[0]
