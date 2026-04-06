"""
Reviewer Agent — compares generated code against the Logic Map.

Produces a ``ReviewerOutput`` with logic-parity findings, defects,
suggested corrections, pass/fail decision, and confidence score.

When a ``MapperOutput`` is provided, the reviewer also performs a
variable alignment check to ensure the Coder respected the Global State.
"""

from __future__ import annotations

from .contracts import CoderOutput, LogicMap, MapperOutput, ReviewerOutput
from .provider import LLMProvider
from .prompts import REVIEWER_SYSTEM_PROMPT


def _build_reviewer_user_prompt(
    logic_map: LogicMap,
    coder_output: CoderOutput,
    mapper_output: MapperOutput | None = None,
) -> str:
    """Build the reviewer prompt with Logic Map, generated code, and optional Global State."""
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

    # --- Variable Alignment Check (Global State) ---
    if mapper_output is not None:
        parts.append("\n## Global State (Variable Alignment Check)\n\n")
        parts.append(
            "The following variables were extracted from the COBOL DATA DIVISION. "
            "Verify that the generated code initializes and uses these variables "
            "exactly as defined. Flag any mismatches, missing variables, or "
            "invented placeholder names as defects.\n\n"
        )
        for v in mapper_output.variables:
            parts.append(
                f"  {v.cobol_name} -> {v.python_name}: "
                f"type={v.python_type}, initial={v.initial_value}, "
                f"pic={v.pic_clause}\n"
            )

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
        mapper_output: MapperOutput | None = None,
        run_version: int = 1,
    ) -> ReviewerOutput:
        """
        Review generated code against the Logic Map.

        When *mapper_output* is provided, the review prompt includes the
        Global State so the Reviewer can flag variable alignment issues.

        Raises
        ------
        pydantic.ValidationError
            If the LLM response doesn't match the ReviewerOutput schema.
        """
        user_prompt = _build_reviewer_user_prompt(
            logic_map, coder_output, mapper_output
        )
        if run_version > 1:
            user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"
        schema = ReviewerOutput.model_json_schema()

        raw = self.provider.generate(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=1000,
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
