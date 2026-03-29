"""
LangGraph state definitions for the LegacyLens pipeline.
"""

from typing import TypedDict
from backend.contracts import LogicMap, CoderOutput, ReviewerOutput, PipelineResult


class PipelineState(TypedDict):
    """
    Shared state mapping passed between LangGraph nodes.
    Tracks outputs, iterations, and terminal error states.
    """
    source_code: str
    file_name: str
    logic_map: LogicMap | None
    coder_output: CoderOutput | None
    reviewer_output: ReviewerOutput | None
    result: PipelineResult | None
    iterations: int
    error: str | None
