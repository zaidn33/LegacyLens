"""
Pipeline orchestrator — Analyst → Coder → Reviewer reflection loop.

Runs the full 3-agent pipeline with up to 3 Coder→Reviewer iterations.
Writes all outputs (logic_map, code, tests, review, confidence, errors) to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from pydantic import ValidationError

# Suppress known upstream warning: langchain-core internally imports pydantic.v1
# shims which emit a UserWarning on Python 3.14+.  This is a third-party issue.
warnings.filterwarnings(
    "ignore",
    message=r".*Pydantic V1.*isn't compatible with Python 3\.14.*",
    category=UserWarning,
)

# Allow running as `python backend/pipeline.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.analyst import AnalystAgent
from backend.coder import CoderAgent
from backend.contracts import (
    ConfidenceAssessment,
    ConfidenceLevel,
    PipelineError,
    PipelineResult,
)
from backend.provider import GraniteProvider, GroqProvider, MockProvider
from backend.render import render_logic_map
from backend.reviewer import ReviewerAgent
from backend.scoring import aggregate_confidence
from backend.state import PipelineState
from backend.graph import build_pipeline_graph

MAX_ITERATIONS = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Run history persistence
# ---------------------------------------------------------------------------

def save_run_history(
    result: PipelineResult,
    base_dir: str | Path = "runs",
    job_id: str | None = None,
) -> Path:
    """Save all artifacts from a pipeline run to a timestamped directory.

    Handles partial results gracefully — only writes artifacts for stages
    that completed.  Always writes ``errors.json`` (empty list on success).
    """
    import uuid
    from datetime import datetime

    base_dir = Path(base_dir)
    job_id = job_id or str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"{timestamp}_{job_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Logic map — always present on PipelineResult
    result.logic_map.write_json(run_dir / "logic_map.json")
    (run_dir / "logic_map.md").write_text(
        render_logic_map(result.logic_map), encoding="utf-8"
    )

    # Coder artifacts — only if coder completed
    if result.coder_output is not None:
        (run_dir / "modernized.py").write_text(
            result.coder_output.generated_code, encoding="utf-8"
        )
        (run_dir / "test_modernized.py").write_text(
            result.coder_output.generated_tests, encoding="utf-8"
        )

    # Reviewer artifacts — only if reviewer completed
    if result.reviewer_output is not None:
        result.reviewer_output.write_json(run_dir / "review_report.json")

    # Confidence — always
    with open(run_dir / "confidence.json", "w", encoding="utf-8") as f:
        json.dump(result.final_confidence.model_dump(), f, indent=2)

    # Errors — always (empty list on clean run)
    with open(run_dir / "errors.json", "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in result.errors], f, indent=2)

    # Full pipeline result
    with open(run_dir / "pipeline_result.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)

    return run_dir


# ---------------------------------------------------------------------------
# Procedural pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    source_path: str | Path,
    provider_name: str = "mock",
    output_dir: str | Path = "output",
    dependencies_dict: dict[str, str] | None = None,
) -> PipelineResult:
    """
    Run the full Analyst → Coder → Reviewer pipeline.

    - Analyst failure: raises immediately (no PipelineResult possible).
    - Coder/Reviewer failure: returns a partial PipelineResult with errors.
    - Scoring failure: uses a fallback Low confidence and logs the error.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Select provider ---
    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "granite":
        provider = GraniteProvider()
    elif provider_name == "groq":
        provider = GroqProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    errors: list[PipelineError] = []

    # --- Stage 1: Analyst ---
    # Analyst failure is NOT recoverable — no logic_map means nothing
    # downstream can run.  We let the exception propagate.
    print("[Stage 1/3] Analyst Agent — extracting Logic Map...")
    analyst = AnalystAgent(provider=provider)
    logic_map = analyst.analyze(source_path, dependencies_dict=dependencies_dict)

    print(f"  Logic Map: {len(logic_map.business_rules)} business rules, "
          f"{len(logic_map.critical_constraints)} critical constraints")

    # --- Stage 2 & 3: Coder → Reviewer loop ---
    coder = CoderAgent(provider=provider)
    reviewer = ReviewerAgent(provider=provider)

    reviewer_output = None
    coder_output = None
    iteration = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        # --- Coder ---
        try:
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
        except ValidationError as exc:
            pe = _make_error("coder", exc, recoverable=True, iteration=iteration)
            errors.append(pe)
            print(f"  Coder ValidationError on iteration {iteration}: {exc}",
                  file=sys.stderr)
            if iteration < MAX_ITERATIONS:
                continue  # retry
            else:
                break  # exhausted — fall through to partial result
        except Exception as exc:
            pe = _make_error("coder", exc, recoverable=False, iteration=iteration)
            errors.append(pe)
            print(f"  Coder crashed on iteration {iteration}: {exc}",
                  file=sys.stderr)
            break  # non-recoverable — stop immediately

        # --- Reviewer ---
        try:
            print(f"\n[Stage 3/3] Reviewer Agent — iteration {iteration}/{MAX_ITERATIONS}...")
            reviewer_output = reviewer.review(
                logic_map=logic_map,
                coder_output=coder_output,
            )

            defect_counts: dict[str, int] = {}
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
        except ValidationError as exc:
            pe = _make_error("reviewer", exc, recoverable=True, iteration=iteration)
            errors.append(pe)
            print(f"  Reviewer ValidationError on iteration {iteration}: {exc}",
                  file=sys.stderr)
            reviewer_output = None
            break  # can't retry reviewer independently
        except Exception as exc:
            pe = _make_error("reviewer", exc, recoverable=False, iteration=iteration)
            errors.append(pe)
            print(f"  Reviewer crashed on iteration {iteration}: {exc}",
                  file=sys.stderr)
            reviewer_output = None
            break

    # --- Aggregate confidence ---
    try:
        final_confidence = aggregate_confidence(
            logic_map=logic_map,
            reviewer_output=reviewer_output,
            iterations=iteration,
        )
    except Exception as exc:
        pe = _make_error("scoring", exc, recoverable=True)
        errors.append(pe)
        print(f"  Scoring failed: {exc}", file=sys.stderr)
        final_confidence = ConfidenceAssessment(
            level=ConfidenceLevel.LOW,
            rationale=f"Scoring failed: {exc}",
        )

    # --- Build result ---
    result = PipelineResult(
        logic_map=logic_map,
        coder_output=coder_output,
        reviewer_output=reviewer_output,
        iterations=iteration,
        final_confidence=final_confidence,
        errors=errors,
    )

    # --- Write outputs ---
    run_dir = save_run_history(result, base_dir=output_dir)

    # --- Summary ---
    print("\n" + "=" * 60)
    if errors:
        print("Pipeline Completed With Errors")
    else:
        print("Pipeline Complete")
    print("=" * 60)
    print(f"  Iterations:           {iteration}")
    print(f"  Final confidence:     {final_confidence.level.value}")
    print(f"  Reviewer passed:      {reviewer_output.passed if reviewer_output else 'N/A'}")
    print(f"  Errors:               {len(errors)}")
    print(f"  Output directory:     {run_dir}")
    print()
    if errors:
        for e in errors:
            print(f"  [{e.stage}] {e.error_type}: {e.message[:120]}")
    else:
        print("  Artifacts successfully written to run history.")

    return result


# ---------------------------------------------------------------------------
# LangGraph pipeline
# ---------------------------------------------------------------------------

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
    elif provider_name == "groq":
        provider = GroqProvider()
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
        result=None, iterations=0, error=None, errors=[],
    )

    final_state = graph.invoke(initial_state)
    if final_state.get("error"):
        raise RuntimeError(f"Graph failed: {final_state['error']}")

    result = final_state.get("result")
    if result:
        status = "with errors" if result.errors else "successfully"
        print(f"[Graph] Pipeline completed {status} on iteration "
              f"{final_state.get('iterations', 0)}.")
        run_dir = save_run_history(result, base_dir=output_dir)
        print(f"[Graph] Artifacts written to: {run_dir}")
        return result
    raise RuntimeError("Graph completed but returned no result.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

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
        choices=["granite", "groq", "mock"],
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
            result = run_pipeline_graph(
                source_path=args.source_file,
                provider_name=args.provider,
                output_dir=args.output_dir,
            )
        else:
            result = run_pipeline(
                source_path=args.source_file,
                provider_name=args.provider,
                output_dir=args.output_dir,
            )

        # Exit code: 1 if any non-recoverable errors
        if any(not e.recoverable for e in result.errors):
            sys.exit(1)

    except Exception as exc:
        print(f"\nPipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
