"""
Pipeline orchestrator — Analyst → Coder → Reviewer reflection loop.

Runs the full 3-agent pipeline with up to 3 Coder→Reviewer iterations.
Writes all outputs (logic_map, code, tests, review, confidence) to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python backend/pipeline.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.analyst import AnalystAgent
from backend.coder import CoderAgent
from backend.contracts import PipelineResult
from backend.provider import GraniteProvider, MockProvider
from backend.render import render_logic_map
from backend.reviewer import ReviewerAgent
from backend.scoring import aggregate_confidence
from backend.state import PipelineState
from backend.graph import build_pipeline_graph

MAX_ITERATIONS = 3


def save_run_history(result: PipelineResult, base_dir: str | Path = "runs", job_id: str | None = None) -> Path:
    """Save all artifacts from a successful pipeline run to a timestamped directory."""
    import uuid
    from datetime import datetime
    
    base_dir = Path(base_dir)
    job_id = job_id or str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"{timestamp}_{job_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    result.logic_map.write_json(run_dir / "logic_map.json")
    (run_dir / "logic_map.md").write_text(render_logic_map(result.logic_map), encoding="utf-8")
    
    (run_dir / "modernized.py").write_text(result.coder_output.generated_code, encoding="utf-8")
    (run_dir / "test_modernized.py").write_text(result.coder_output.generated_tests, encoding="utf-8")
    result.reviewer_output.write_json(run_dir / "review_report.json")
    
    with open(run_dir / "confidence.json", "w", encoding="utf-8") as f:
        json.dump(result.final_confidence.model_dump(), f, indent=2)
        
    with open(run_dir / "pipeline_result.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
        
    return run_dir


def run_pipeline(
    source_path: str | Path,
    provider_name: str = "mock",
    output_dir: str | Path = "output",
) -> PipelineResult:
    """
    Run the full Analyst → Coder → Reviewer pipeline.

    Returns the validated ``PipelineResult``.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Select provider ---
    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "granite":
        provider = GraniteProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    # --- Stage 1: Analyst ---
    print("[Stage 1/3] Analyst Agent — extracting Logic Map...")
    analyst = AnalystAgent(provider=provider)
    logic_map = analyst.analyze(source_path)

    # Immediately log high-level Analyst stats
    print(f"  Logic Map: {len(logic_map.business_rules)} business rules, "
          f"{len(logic_map.critical_constraints)} critical constraints")

    # --- Stage 2 & 3: Coder → Reviewer loop ---
    coder = CoderAgent(provider=provider)
    reviewer = ReviewerAgent(provider=provider)

    reviewer_output = None
    coder_output = None
    iteration = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n[Stage 2/3] Coder Agent — iteration {iteration}/{MAX_ITERATIONS}...")
        coder_output = coder.generate(
            logic_map=logic_map,
            reviewer_feedback=reviewer_output,
            iteration=iteration,
        )
        print(f"  Generated code: {len(coder_output.generated_code)} chars")
        print(f"  Generated tests: {len(coder_output.generated_tests)} chars")
        print(f"  Logic step mappings: {len(coder_output.logic_step_mapping)}")
        if coder_output.deferred_items:
            print(f"  Deferred items: {len(coder_output.deferred_items)}")

        print(f"\n[Stage 3/3] Reviewer Agent — iteration {iteration}/{MAX_ITERATIONS}...")
        reviewer_output = reviewer.review(
            logic_map=logic_map,
            coder_output=coder_output,
        )

        defect_counts = {}
        for d in reviewer_output.defects:
            defect_counts[d.severity] = defect_counts.get(d.severity, 0) + 1

        print(f"  Passed: {reviewer_output.passed}")
        print(f"  Confidence: {reviewer_output.confidence.level.value}")
        if defect_counts:
            print(f"  Defects: {defect_counts}")
        if reviewer_output.known_limitations:
            print(f"  Known limitations: {len(reviewer_output.known_limitations)}")

        if reviewer_output.passed:
            print(f"\n  Reviewer approved on iteration {iteration}.")
            break
        else:
            print(f"\n  Reviewer rejected — will retry ({iteration}/{MAX_ITERATIONS}).")

    # --- Aggregate confidence ---
    final_confidence = aggregate_confidence(
        logic_map=logic_map,
        reviewer_output=reviewer_output,
        iterations=iteration,
    )

    # --- Build result ---
    result = PipelineResult(
        logic_map=logic_map,
        coder_output=coder_output,
        reviewer_output=reviewer_output,
        iterations=iteration,
        final_confidence=final_confidence,
    )

    # --- Write outputs ---
    run_dir = save_run_history(result, base_dir=output_dir)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("Pipeline Complete")
    print("=" * 60)
    print(f"  Iterations:           {iteration}")
    print(f"  Final confidence:     {final_confidence.level.value}")
    print(f"  Reviewer passed:      {reviewer_output.passed}")
    print(f"  Output directory:     {run_dir}")
    print()
    print("  Artifacts successfully written to run history.")

    return result


def run_pipeline_graph(
    source_path: str | Path,
    provider_name: str = "mock",
    output_dir: str | Path = "output",
) -> PipelineResult:
    """Run the pipeline via LangGraph to ensure behavioral parity."""
    print("[Graph] Starting LangGraph pipeline execution...")
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    source_code = source_path.read_text(encoding="utf-8")
    
    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "granite":
        provider = GraniteProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
        
    analyst = AnalystAgent(provider)
    coder = CoderAgent(provider)
    reviewer = ReviewerAgent(provider)
    graph = build_pipeline_graph(analyst, coder, reviewer)
    
    initial_state = PipelineState(
        source_code=source_code,
        file_name=source_path.name,
        logic_map=None, coder_output=None, reviewer_output=None,
        result=None, iterations=0, error=None
    )
    
    final_state = graph.invoke(initial_state)
    if final_state.get("error"):
        raise RuntimeError(f"Graph failed: {final_state['error']}")
        
    result = final_state.get("result")
    if result:
        print(f"[Graph] Pass achieved on iteration {final_state.get('iterations', 0)}.")
        run_dir = save_run_history(result, base_dir=output_dir)
        print(f"[Graph] Artifacts successfully written to run history: {run_dir}")
        return result
    raise RuntimeError("Graph completed but returned no result.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="LegacyLens Pipeline — full Analyst → Coder → Reviewer loop",
    )
    parser.add_argument(
        "source_file",
        help="Path to the legacy source file",
    )
    parser.add_argument(
        "--provider",
        choices=["granite", "mock"],
        default="mock",
        help="LLM provider to use (default: mock)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to write output files (default: output)",
    )
    parser.add_argument(
        "--use-graph",
        action="store_true",
        help="Invoke the replacement LangGraph execution path instead of the procedural loop.",
    )
    args = parser.parse_args(argv)

    try:
        if args.use_graph:
            run_pipeline_graph(
                source_path=args.source_file,
                provider_name=args.provider,
                output_dir=args.output_dir,
            )
        else:
            run_pipeline(
                source_path=args.source_file,
                provider_name=args.provider,
                output_dir=args.output_dir,
            )
    except Exception as exc:
        print(f"\nPipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
