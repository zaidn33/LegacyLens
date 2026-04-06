"""
LangGraph orchestration for the Chunker → Analyst → Mapper → Coder → Reviewer pipeline.

Uses a dedicated ``finalize`` node as the single assembly point for
PipelineResult — whether the run succeeded fully or partially.
"""

from typing import Any

from pydantic import ValidationError
from langgraph.graph import StateGraph, START, END

from backend.state import PipelineState
from backend.analyst import AnalystAgent
from backend.chunker import extract_global_context, extract_logic_chunks
from backend.coder import CoderAgent
from backend.mapper import MapperAgent
from backend.reviewer import ReviewerAgent
from backend.scoring import aggregate_confidence
from backend.config import MAX_ITERATIONS
from backend.contracts import (
    ConfidenceAssessment,
    ConfidenceLevel,
    PipelineError,
    PipelineResult,
)


def _make_error(
    stage: str,
    exc: Exception,
    *,
    recoverable: bool,
    iteration: int | None = None,
) -> PipelineError:
    """Build a ``PipelineError`` from a caught exception."""
    return PipelineError(
        stage=stage,
        error_type=type(exc).__name__,
        message=str(exc),
        recoverable=recoverable,
        iteration=iteration,
    )


def build_pipeline_graph(
    analyst: AnalystAgent,
    coder: CoderAgent,
    reviewer: ReviewerAgent,
    mapper: MapperAgent | None = None,
):
    """Builds and compiles the StateGraph for the modernization pipeline.

    Nodes: analyst_node → chunker_node → mapper_node → coder_node → reviewer_node → finalize_node
                                                            ↑_______________|  (retry loop)

    The ``finalize_node`` is the single place where ``PipelineResult``
    is assembled — both for success and partial-failure cases.
    """

    # ------------------------------------------------------------------
    # Node: Analyst
    # ------------------------------------------------------------------
    def run_analyst(state: PipelineState) -> dict[str, Any]:
        try:
            logic_map = analyst.analyze_source(
                state["source_code"],
                state.get("file_name", "source.cbl"),
                dependencies_dict=state.get("dependencies_dict"),
                run_version=state.get("run_version", 1)
            )
            return {"logic_map": logic_map}
        except Exception as e:
            # Analyst failure is NOT recoverable — no logic_map
            return {"error": f"Analyst failed: {str(e)}"}

    # ------------------------------------------------------------------
    # Node: Chunker (pure Python, no LLM call)
    # ------------------------------------------------------------------
    def run_chunker(state: PipelineState) -> dict[str, Any]:
        source_code = state["source_code"]
        global_context = extract_global_context(source_code)
        logic_chunks = extract_logic_chunks(source_code)
        print(f"  [CHUNKER] Global Context: {len(global_context)} chars, "
              f"Logic Chunks: {len(logic_chunks)}")
        return {
            "global_context": global_context,
            "logic_chunks": logic_chunks,
        }

    # ------------------------------------------------------------------
    # Node: Mapper
    # ------------------------------------------------------------------
    def run_mapper(state: PipelineState) -> dict[str, Any]:
        if mapper is None:
            return {}  # Skip if no mapper provided
        global_context = state.get("global_context", "")
        if not global_context:
            return {}  # Nothing to map
        try:
            mapper_output = mapper.extract_global_state(
                global_context,
                run_version=state.get("run_version", 1),
            )
            print(f"  [MAPPER] Variables mapped: {len(mapper_output.variables)}")
            return {"mapper_output": mapper_output}
        except ValidationError as e:
            pe = _make_error("mapper", e, recoverable=True)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"errors": prev_errors}
        except Exception as e:
            pe = _make_error("mapper", e, recoverable=True)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"errors": prev_errors}

    # ------------------------------------------------------------------
    # Node: Coder (iterative over chunks when available)
    # ------------------------------------------------------------------
    def run_coder(state: PipelineState) -> dict[str, Any]:
        iteration = state.get("iterations", 0) + 1
        try:
            mapper_output = state.get("mapper_output")
            logic_chunks = state.get("logic_chunks")

            if mapper_output is not None and logic_chunks:
                coder_output = coder.generate_chunked(
                    logic_map=state["logic_map"],
                    mapper_output=mapper_output,
                    chunks=logic_chunks,
                    reviewer_feedback=state.get("reviewer_output"),
                    iteration=iteration,
                    run_version=state.get("run_version", 1),
                )
            else:
                coder_output = coder.generate(
                    logic_map=state["logic_map"],
                    reviewer_feedback=state.get("reviewer_output"),
                    iteration=iteration,
                    run_version=state.get("run_version", 1),
                )
            return {"coder_output": coder_output, "iterations": iteration}
        except ValidationError as e:
            pe = _make_error("coder", e, recoverable=True, iteration=iteration)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"iterations": iteration, "errors": prev_errors}
        except Exception as e:
            pe = _make_error("coder", e, recoverable=False, iteration=iteration)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"iterations": iteration, "errors": prev_errors}

    # ------------------------------------------------------------------
    # Node: Reviewer (includes mapper_output for alignment checking)
    # ------------------------------------------------------------------
    def run_reviewer(state: PipelineState) -> dict[str, Any]:
        iteration = state.get("iterations", 0)
        try:
            reviewer_output = reviewer.review(
                logic_map=state["logic_map"],
                coder_output=state["coder_output"],
                mapper_output=state.get("mapper_output"),
                run_version=state.get("run_version", 1),
            )
            return {"reviewer_output": reviewer_output}
        except ValidationError as e:
            pe = _make_error("reviewer", e, recoverable=True, iteration=iteration)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"errors": prev_errors}
        except Exception as e:
            pe = _make_error("reviewer", e, recoverable=False, iteration=iteration)
            prev_errors = list(state.get("errors") or [])
            prev_errors.append(pe)
            return {"errors": prev_errors}

    # ------------------------------------------------------------------
    # Node: Finalize (single assembly point for PipelineResult)
    # ------------------------------------------------------------------
    def run_finalize(state: PipelineState) -> dict[str, Any]:
        logic_map = state.get("logic_map")
        if logic_map is None:
            # Analyst failed — no PipelineResult possible
            return {"error": state.get("error", "No logic map produced")}

        iterations = state.get("iterations", 0)
        reviewer_output = state.get("reviewer_output")
        coder_output = state.get("coder_output")
        mapper_output = state.get("mapper_output")
        errors = list(state.get("errors") or [])

        # Aggregate confidence (with fallback on failure)
        try:
            final_confidence = aggregate_confidence(
                logic_map=logic_map,
                reviewer_output=reviewer_output,
                iterations=iterations,
            )
        except Exception as e:
            pe = _make_error("scoring", e, recoverable=True)
            errors.append(pe)
            final_confidence = ConfidenceAssessment(
                level=ConfidenceLevel.LOW,
                rationale=f"Scoring failed: {e}",
            )

        result = PipelineResult(
            logic_map=logic_map,
            mapper_output=mapper_output,
            coder_output=coder_output,
            reviewer_output=reviewer_output,
            iterations=iterations,
            final_confidence=final_confidence,
            errors=errors,
        )

        return {"result": result, "errors": errors}

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def route_after_analyst(state: PipelineState) -> str:
        if state.get("error"):
            return "finalize"  # analyst failed → finalize handles "no result"
        return "chunker"

    def route_after_mapper(state: PipelineState) -> str:
        # Always proceed to coder, even if mapper failed
        return "coder"

    def route_after_coder(state: PipelineState) -> str:
        # If coder produced output, proceed to reviewer
        if state.get("coder_output") is not None:
            return "reviewer"
        # Coder failed — check if we can retry
        errors = state.get("errors") or []
        latest = errors[-1] if errors else None
        iterations = state.get("iterations", 0)
        if latest and latest.recoverable and iterations < MAX_ITERATIONS:
            return "coder"  # retry
        return "finalize"  # exhausted or non-recoverable

    def route_after_reviewer(state: PipelineState) -> str:
        reviewer_output = state.get("reviewer_output")
        # Reviewer failed (no output produced)
        if reviewer_output is None:
            return "finalize"
        # Reviewer passed
        if reviewer_output.passed:
            return "finalize"
        # Reviewer rejected — check if retries remain
        iterations = state.get("iterations", 0)
        if iterations < MAX_ITERATIONS:
            return "coder"
        return "finalize"

    # ------------------------------------------------------------------
    # Build graph
    # ------------------------------------------------------------------
    builder = StateGraph(PipelineState)

    builder.add_node("analyst_node", run_analyst)
    builder.add_node("chunker_node", run_chunker)
    builder.add_node("mapper_node", run_mapper)
    builder.add_node("coder_node", run_coder)
    builder.add_node("reviewer_node", run_reviewer)
    builder.add_node("finalize_node", run_finalize)

    builder.add_edge(START, "analyst_node")

    builder.add_conditional_edges(
        "analyst_node",
        route_after_analyst,
        {"chunker": "chunker_node", "finalize": "finalize_node"},
    )
    builder.add_edge("chunker_node", "mapper_node")
    builder.add_conditional_edges(
        "mapper_node",
        route_after_mapper,
        {"coder": "coder_node"},
    )
    builder.add_conditional_edges(
        "coder_node",
        route_after_coder,
        {"reviewer": "reviewer_node", "coder": "coder_node", "finalize": "finalize_node"},
    )
    builder.add_conditional_edges(
        "reviewer_node",
        route_after_reviewer,
        {"coder": "coder_node", "finalize": "finalize_node"},
    )
    builder.add_edge("finalize_node", END)

    return builder.compile()
