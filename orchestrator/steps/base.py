"""Abstract base class for pipeline steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..context import PipelineContext


class Step(ABC):
    """A single unit of work in a pipeline.

    Subclasses implement :meth:`execute` which receives the shared
    :class:`PipelineContext`, performs work, writes results into
    ``context.step_results``, and returns the context.
    """

    step_name: str = ""
    step_version: str = ""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute this step and return the updated context."""
        ...

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(name={self.step_name!r}, version={self.step_version!r})"
        )
