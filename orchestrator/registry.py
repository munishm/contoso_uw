"""StepRegistry: singleton mapping (step_name, version) tuples to step classes."""

from __future__ import annotations

import logging
from typing import Type

logger = logging.getLogger(__name__)


class StepRegistry:
    """Maps ``(step_name, version)`` tuples to step classes.

    Steps self-register at import time via the :func:`register_step` decorator.
    """

    _steps: dict[tuple[str, str], type] = {}

    @classmethod
    def register(cls, name: str, version: str):
        """Class-method decorator that registers a step class."""

        def decorator(step_cls: type) -> type:
            key = (name, version)
            if key in cls._steps:
                logger.warning("Overwriting step registration: %s", key)
            cls._steps[key] = step_cls
            step_cls.step_name = name
            step_cls.step_version = version
            return step_cls

        return decorator

    @classmethod
    def get(cls, name: str, version: str) -> type:
        """Retrieve a registered step class by name and version."""
        key = (name, version)
        if key not in cls._steps:
            available = sorted(cls._steps.keys())
            raise KeyError(
                f"Step ({name!r}, {version!r}) not found. "
                f"Available: {available}"
            )
        return cls._steps[key]

    @classmethod
    def list_steps(cls) -> list[tuple[str, str]]:
        """Return all registered ``(name, version)`` pairs."""
        return sorted(cls._steps.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove all registrations.  **For testing only.**"""
        cls._steps.clear()


def register_step(name: str, version: str):
    """Convenience decorator — alias for ``StepRegistry.register``."""
    return StepRegistry.register(name, version)
