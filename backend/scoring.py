"""
Confidence scoring — aggregates confidence across pipeline stages.

Produces a final ``ConfidenceAssessment`` based on the Analyst and
Reviewer confidence levels plus defect severity counts.
"""

from __future__ import annotations

from .contracts import (
    ConfidenceAssessment,
    ConfidenceLevel,
    LogicMap,
    ReviewerOutput,
)


def aggregate_confidence(
    logic_map: LogicMap,
    reviewer_output: ReviewerOutput,
    iterations: int,
) -> ConfidenceAssessment:
    """
    Compute a final confidence score from the pipeline stages.

    Logic:
    - Start from the reviewer's confidence level.
    - Downgrade if the analyst confidence was lower.
    - Downgrade if multiple iterations were needed.
    - Downgrade if critical/major defects remain.
    """
    _order = {ConfidenceLevel.HIGH: 3, ConfidenceLevel.MEDIUM: 2, ConfidenceLevel.LOW: 1}
    _reverse = {3: ConfidenceLevel.HIGH, 2: ConfidenceLevel.MEDIUM, 1: ConfidenceLevel.LOW}

    # Start with the reviewer's assessment
    level_score = _order[reviewer_output.confidence.level]

    # Cap at analyst confidence (can't be more confident than the source analysis)
    analyst_score = _order[logic_map.confidence_assessment.level]
    level_score = min(level_score, analyst_score)

    # Penalize for needing rewrites
    if iterations >= 3:
        level_score = max(1, level_score - 1)

    # Penalize for remaining defects
    critical_remaining = sum(
        1 for d in reviewer_output.defects if d.severity == "critical"
    )
    major_remaining = sum(
        1 for d in reviewer_output.defects if d.severity == "major"
    )

    if critical_remaining > 0:
        level_score = 1  # Force Low
    elif major_remaining >= 2:
        level_score = max(1, level_score - 1)

    final_level = _reverse[level_score]

    # Build rationale
    rationale_parts = [
        f"Analyst confidence: {logic_map.confidence_assessment.level.value}.",
        f"Reviewer confidence: {reviewer_output.confidence.level.value}.",
        f"Pipeline completed in {iterations} iteration(s).",
    ]
    if critical_remaining:
        rationale_parts.append(
            f"{critical_remaining} critical defect(s) remain unresolved."
        )
    if major_remaining:
        rationale_parts.append(
            f"{major_remaining} major defect(s) remain."
        )
    if reviewer_output.known_limitations:
        rationale_parts.append(
            f"{len(reviewer_output.known_limitations)} known limitation(s) documented."
        )

    return ConfidenceAssessment(
        level=final_level,
        rationale=" ".join(rationale_parts),
    )
