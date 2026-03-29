"""
Renders a validated LogicMap (JSON) into ANALYST.md-compliant Markdown.

The Markdown output matches the exact section headers specified in ANALYST.md
so that human reviewers see the familiar format while agents work with the
structured JSON.
"""

from __future__ import annotations

from .contracts import LogicMap


def render_logic_map(logic_map: LogicMap) -> str:
    """Convert a validated ``LogicMap`` to human-readable Markdown."""
    lines: list[str] = []

    def heading(level: int, text: str) -> None:
        lines.append(f"{'#' * level} {text}")
        lines.append("")

    def bullets(items: list[str]) -> None:
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    # ------------------------------------------------------------------
    heading(1, "Logic Map")

    # Executive Summary
    heading(2, "Executive Summary")
    lines.append(logic_map.executive_summary)
    lines.append("")

    # Business Objective
    heading(2, "Business Objective")
    lines.append(logic_map.business_objective)
    lines.append("")

    # Inputs and Outputs
    heading(2, "Inputs and Outputs")

    heading(3, "Inputs")
    bullets(logic_map.inputs_and_outputs.inputs)

    heading(3, "Outputs")
    bullets(logic_map.inputs_and_outputs.outputs)

    heading(3, "External Touchpoints")
    bullets(logic_map.inputs_and_outputs.external_touchpoints)

    # Logic Dictionary
    heading(2, "Logic Dictionary")
    lines.append(
        "| Legacy Name | Proposed Modern Name | Meaning | Confidence |"
    )
    lines.append("|:---|:---|:---|:---|")
    for entry in logic_map.logic_dictionary:
        lines.append(
            f"| {entry.legacy_name} "
            f"| {entry.proposed_modern_name} "
            f"| {entry.meaning} "
            f"| {entry.confidence.value} |"
        )
    lines.append("")

    # Step-by-Step Logic Flow
    heading(2, "Step-by-Step Logic Flow")
    for step in logic_map.step_by_step_logic_flow:
        lines.append(step)
    lines.append("")

    # Business Rules
    heading(2, "Business Rules")
    bullets(logic_map.business_rules)

    # Edge Cases
    heading(2, "Edge Cases")
    bullets(logic_map.edge_cases)

    # Dependencies
    heading(2, "Dependencies")
    bullets(logic_map.dependencies)

    # Critical Constraints
    heading(2, "Critical Constraints")
    bullets(logic_map.critical_constraints)

    # Assumptions and Ambiguities
    heading(2, "Assumptions and Ambiguities")

    heading(3, "Observed")
    bullets(logic_map.assumptions_and_ambiguities.observed)

    heading(3, "Inferred")
    bullets(logic_map.assumptions_and_ambiguities.inferred)

    heading(3, "Unknown")
    bullets(logic_map.assumptions_and_ambiguities.unknown)

    # Test-Relevant Scenarios
    heading(2, "Test-Relevant Scenarios")
    bullets(logic_map.test_relevant_scenarios)

    # Confidence Assessment
    heading(2, "Confidence Assessment")
    lines.append(f"**{logic_map.confidence_assessment.level.value}**")
    lines.append("")
    lines.append(logic_map.confidence_assessment.rationale)
    lines.append("")

    return "\n".join(lines)
