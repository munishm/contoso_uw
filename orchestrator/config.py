"""Pipeline configuration loading, routing, and validation."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

PIPELINES_DIR = Path(__file__).parent / "pipelines"

DEFAULT_PIPELINE_MAP: dict[str, str] = {
    "DocumentSummary": "document_summary",
    "CaseSummary": "case_summary",
}


def load_pipeline(
    name: str,
    pipelines_dir: Path | None = None,
) -> dict[str, Any]:
    """Load and validate a pipeline definition from a YAML file."""
    base_dir = pipelines_dir or PIPELINES_DIR
    file_path = base_dir / f"{name}.yaml"

    if not file_path.exists():
        raise FileNotFoundError(f"Pipeline config not found: {file_path}")

    with open(file_path, "r") as fh:
        pipeline_def = yaml.safe_load(fh)

    _validate_pipeline(pipeline_def, file_path)
    return pipeline_def


def get_pipeline_map() -> dict[str, str]:
    """Return the ``requestType → pipeline_name`` mapping.

    Can be overridden per Function App via the ``PIPELINE_MAP`` environment
    variable (JSON string).
    """
    env_map = os.environ.get("PIPELINE_MAP")
    if env_map:
        try:
            return json.loads(env_map)
        except json.JSONDecodeError:
            logger.warning("Invalid PIPELINE_MAP env var, using defaults")
    return DEFAULT_PIPELINE_MAP.copy()


def get_pipeline_for_request(
    request_type: str,
    pipelines_dir: Path | None = None,
) -> dict[str, Any]:
    """Load the pipeline definition for a given request type."""
    pipeline_map = get_pipeline_map()
    pipeline_name = pipeline_map.get(request_type)
    if not pipeline_name:
        raise ValueError(
            f"No pipeline configured for request type: {request_type!r}. "
            f"Available: {sorted(pipeline_map.keys())}"
        )
    return load_pipeline(pipeline_name, pipelines_dir)


def validate_all_pipelines(
    pipelines_dir: Path | None = None,
) -> list[str]:
    """Validate every YAML pipeline on startup.  Returns a list of errors."""
    base_dir = pipelines_dir or PIPELINES_DIR
    errors: list[str] = []

    for yaml_file in sorted(base_dir.glob("*.yaml")):
        try:
            with open(yaml_file, "r") as fh:
                pipeline_def = yaml.safe_load(fh)
            _validate_pipeline(pipeline_def, yaml_file)
        except Exception as exc:
            errors.append(f"{yaml_file.name}: {exc}")

    return errors


# -- internal -----------------------------------------------------------------


def _validate_pipeline(
    pipeline_def: dict[str, Any] | None,
    source: Any = None,
) -> None:
    """Validate the structure of a pipeline definition."""
    if not pipeline_def or "pipeline" not in pipeline_def:
        raise ValueError(f"Missing 'pipeline' key in {source}")

    pipeline = pipeline_def["pipeline"]

    if "name" not in pipeline:
        raise ValueError(f"Missing 'pipeline.name' in {source}")

    if "stages" not in pipeline:
        raise ValueError(f"Missing 'pipeline.stages' in {source}")

    for idx, stage in enumerate(pipeline["stages"]):
        if "name" not in stage:
            raise ValueError(f"Stage {idx} missing 'name' in {source}")
        if "steps" not in stage or not stage["steps"]:
            raise ValueError(
                f"Stage '{stage.get('name', idx)}' has no steps in {source}"
            )
        for jdx, step in enumerate(stage["steps"]):
            if "name" not in step:
                raise ValueError(
                    f"Step {jdx} in stage '{stage['name']}' missing 'name' "
                    f"in {source}"
                )
