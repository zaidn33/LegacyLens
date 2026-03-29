"""
LangGraph orchestration for the Analyst -> Coder -> Reviewer pipeline.
"""

from typing import Any
from langgraph.graph import StateGraph, START, END

from backend.state import PipelineState
from backend.analyst import AnalystAgent
from backend.coder import CoderAgent
from backend.reviewer import ReviewerAgent
from backend.scoring import aggregate_confidence
from backend.contracts import PipelineResult


def build_pipeline_graph(
    analyst: AnalystAgent,
    coder: CoderAgent,
    reviewer: ReviewerAgent,
):
    """Builds and compiles the StateGraph for the modernization pipeline."""

    def run_analyst(state: PipelineState) -> dict[str, Any]:
        """Node for Analyst Agent."""
        try:
            logic_map = analyst.analyze_source(
                state["source_code"], 
                state.get("file_name", "source.cbl")
            )
            return {"logic_map": logic_map}
        except Exception as e:
            return {"error": f"Analyst failed: {str(e)}"}

    def run_coder(state: PipelineState) -> dict[str, Any]:
        """Node for Coder Agent."""
        try:
            iteration = state.get("iterations", 0) + 1
            coder_output = coder.generate(
                logic_map=state["logic_map"],
                reviewer_feedback=state.get("reviewer_output"),
                iteration=iteration
            )
            return {"coder_output": coder_output, "iterations": iteration}
        except Exception as e:
            return {"error": f"Coder failed: {str(e)}"}

    def run_reviewer(state: PipelineState) -> dict[str, Any]:
        """Node for Reviewer Agent."""
        try:
            reviewer_output = reviewer.review(
                logic_map=state["logic_map"],
                coder_output=state["coder_output"],
            )
            
            result = None
            iterations = state.get("iterations", 0)
            
            # If passed or reached max iterations, finalize pipeline result
            if reviewer_output.passed or iterations >= 3:
                final_conf = aggregate_confidence(
                    logic_map=state["logic_map"], 
                    reviewer_output=reviewer_output, 
                    iterations=iterations,
                )
                result = PipelineResult(
                    logic_map=state["logic_map"],
                    coder_output=state["coder_output"],
                    reviewer_output=reviewer_output,
                    iterations=iterations,
                    final_confidence=final_conf,
                )
            
            return {
                "reviewer_output": reviewer_output,
                "result": result
            }
        except Exception as e:
            return {"error": f"Reviewer failed: {str(e)}"}

    # Routing definitions
    def route_after_analyst(state: PipelineState) -> str:
        if state.get("error"):
            return END
        return "coder"

    def route_after_coder(state: PipelineState) -> str:
        if state.get("error"):
            return END
        return "reviewer"

    def route_after_reviewer(state: PipelineState) -> str:
        if state.get("error"):
            return END
        if state.get("result"):
            return END
        return "coder"

    # Build the graph
    builder = StateGraph(PipelineState)
    
    builder.add_node("analyst_node", run_analyst)
    builder.add_node("coder_node", run_coder)
    builder.add_node("reviewer_node", run_reviewer)
    
    builder.add_edge(START, "analyst_node")
    
    # Conditional routing determines transitions
    builder.add_conditional_edges(
        "analyst_node", 
        route_after_analyst, 
        {"coder": "coder_node", END: END}
    )
    builder.add_conditional_edges(
        "coder_node", 
        route_after_coder, 
        {"reviewer": "reviewer_node", END: END}
    )
    builder.add_conditional_edges(
        "reviewer_node", 
        route_after_reviewer, 
        {"coder": "coder_node", END: END}
    )
    
    return builder.compile()
