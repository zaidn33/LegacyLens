"""
Reviewer Agent — compares generated code against the Logic Map.

Produces a ``ReviewerOutput`` with logic-parity findings, defects,
suggested corrections, pass/fail decision, and confidence score.
"""

from __future__ import annotations

from .contracts import CoderOutput, LogicMap, ReviewerOutput
from .provider import LLMProvider
from .prompts import REVIEWER_SYSTEM_PROMPT


def _build_reviewer_user_prompt(
    logic_map: LogicMap,
    coder_output: CoderOutput,
) -> str:
    """Build the reviewer prompt with Logic Map and generated code."""
    parts = [
        "Review the following generated code against the Logic Map.\n\n",
        "## Logic Map (Source of Truth)\n\n",
        f"Business Objective: {logic_map.business_objective}\n\n",
        "Critical Constraints (MUST be implemented correctly):\n",
    ]
    for constraint in logic_map.critical_constraints:
        parts.append(f"  - {constraint}\n")

    parts.append("\nBusiness Rules:\n")
    for rule in logic_map.business_rules:
        parts.append(f"  - {rule}\n")

    parts.append("\nLogic Flow:\n")
    for step in logic_map.step_by_step_logic_flow:
        parts.append(f"  {step}\n")

    parts.append("\nEdge Cases:\n")
    for case in logic_map.edge_cases:
        parts.append(f"  - {case}\n")

    parts.append("\n## Generated Code\n\n```python\n")
    parts.append(coder_output.generated_code)
    parts.append("\n```\n\n## Generated Tests\n\n```python\n")
    parts.append(coder_output.generated_tests)
    parts.append("\n```\n\n## Implementation Choices\n\n")
    parts.append(coder_output.implementation_choices)

    parts.append("\n\n## Logic Step Mapping\n\n")
    for mapping in coder_output.logic_step_mapping:
        parts.append(
            f"  - {mapping.function_or_test_name} → {mapping.logic_step}"
        )
        if mapping.notes:
            parts.append(f" ({mapping.notes})")
        parts.append("\n")

    if coder_output.deferred_items:
        parts.append("\n## Deferred Items\n\n")
        for item in coder_output.deferred_items:
            parts.append(f"  - {item}\n")

    return "".join(parts)


class ReviewerAgent:
    """Compares generated code against the Logic Map for parity."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def review(
        self,
        logic_map: LogicMap,
        coder_output: CoderOutput,
        run_version: int = 1,
    ) -> ReviewerOutput:
        """
        Review generated code against the Logic Map.

        Raises
        ------
        pydantic.ValidationError
            If the LLM response doesn't match the ReviewerOutput schema.
        """
        user_prompt = _build_reviewer_user_prompt(logic_map, coder_output)
        if run_version > 1:
            user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"
        schema = ReviewerOutput.model_json_schema()

        raw = self.provider.generate(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
        )

        output = ReviewerOutput.model_validate(raw)

        # Enforce strict gating: gracefully override LLM hallucination
        # if it returns passed=True but lists blocking defects
        from .contracts import DefectSeverity
        has_blocking_defect = any(
            d.severity in (DefectSeverity.CRITICAL, DefectSeverity.MAJOR)
            for d in output.defects
        )
        if has_blocking_defect:
            output.passed = False

        return output
