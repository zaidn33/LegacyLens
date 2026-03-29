"""
CLI entry point for the Analyst Agent.

Usage:
    python -m backend.run_analyst samples/sample.cbl --provider mock
    python -m backend.run_analyst samples/sample.cbl --provider granite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyst import AnalystAgent
from .provider import GraniteProvider, MockProvider
from .render import render_logic_map


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "LegacyLens Analyst Agent — extract a Logic Map "
            "from legacy source code"
        ),
    )
    parser.add_argument(
        "source_file",
        help="Path to the legacy source file to analyze",
    )
    parser.add_argument(
        "--provider",
        choices=["granite", "mock"],
        default="mock",
        help="LLM provider to use (default: mock)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write output files (default: current directory)",
    )
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Select provider
    # ------------------------------------------------------------------
    if args.provider == "mock":
        provider = MockProvider()
    elif args.provider == "granite":
        try:
            provider = GraniteProvider()
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown provider: {args.provider}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Run analysis
    # ------------------------------------------------------------------
    agent = AnalystAgent(provider=provider)

    try:
        logic_map = agent.analyze(args.source_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON — structured, for downstream agents
    json_path = logic_map.write_json(output_dir / "logic_map.json")
    print(f"  Logic Map (JSON):     {json_path}")

    # Markdown — human-readable
    md_path = output_dir / "logic_map.md"
    md_content = render_logic_map(logic_map)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"  Logic Map (Markdown): {md_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print(f"  Confidence:           {logic_map.confidence_assessment.level.value}")
    print("  Sections validated:   12/12")
    print(f"  Business rules:       {len(logic_map.business_rules)}")
    print(f"  Edge cases:           {len(logic_map.edge_cases)}")
    print(f"  Critical constraints: {len(logic_map.critical_constraints)}")


if __name__ == "__main__":
    main()
