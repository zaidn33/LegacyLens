"""
LangGraph state definitions for the LegacyLens pipeline.
"""

from typing import TypedDict
from backend.contracts import (
    CoderOutput,
    LogicMap,
    PipelineError,
    PipelineResult,
    ReviewerOutput,
)


class PipelineState(TypedDict):
    """
    Shared state mapping passed between LangGraph nodes.
    Tracks outputs, iterations, terminal error states, and accumulated errors.
    """
    source_code: str
    file_name: str
    logic_map: LogicMap | None
    coder_output: CoderOutput | None
    reviewer_output: ReviewerOutput | None
    result: PipelineResult | None
    iterations: int
    error: str | None
    errors: list[PipelineError]
    dependencies_dict: dict[str, str]
