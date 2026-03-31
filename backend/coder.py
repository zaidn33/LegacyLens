"""
Coder Agent — generates Python code + Pytest tests from a Logic Map.

Consumes the structured ``LogicMap`` produced by the Analyst Agent and
outputs a ``CoderOutput`` containing implementation code, tests,
design-choice explanations, and logic-step mapping.
"""

from __future__ import annotations

from .contracts import CoderOutput, LogicMap, ReviewerOutput
from .provider import LLMProvider
from .prompts import CODER_SYSTEM_PROMPT, CODER_REWRITE_ADDENDUM


def _build_coder_user_prompt(
    logic_map: LogicMap,
    reviewer_feedback: ReviewerOutput | None = None,
    iteration: int = 1,
) -> str:
    """Build the user prompt containing the Logic Map and optional feedback."""
    parts = [
        "Generate a Python implementation from this Logic Map:\n\n",
        f"Business Objective: {logic_map.business_objective}\n\n",
        "Inputs and Outputs:\n",
        f"  Inputs: {', '.join(logic_map.inputs_and_outputs.inputs)}\n",
        f"  Outputs: {', '.join(logic_map.inputs_and_outputs.outputs)}\n\n",
        "Logic Flow:\n",
    ]
    for step in logic_map.step_by_step_logic_flow:
        parts.append(f"  {step}\n")

    parts.append("\nBusiness Rules:\n")
    for rule in logic_map.business_rules:
        parts.append(f"  - {rule}\n")

    parts.append("\nCritical Constraints (MUST implement and test):\n")
    for constraint in logic_map.critical_constraints:
        parts.append(f"  - {constraint}\n")

    parts.append("\nEdge Cases:\n")
    for case in logic_map.edge_cases:
        parts.append(f"  - {case}\n")

    parts.append("\nVariable Dictionary:\n")
    for entry in logic_map.logic_dictionary:
        parts.append(
            f"  {entry.legacy_name} -> {entry.proposed_modern_name}: "
            f"{entry.meaning} (confidence: {entry.confidence.value})\n"
        )

    if logic_map.assumptions_and_ambiguities.unknown:
        parts.append("\nUnresolved Ambiguities (handle conservatively):\n")
        for item in logic_map.assumptions_and_ambiguities.unknown:
            parts.append(f"  - {item}\n")

    # Append reviewer feedback for rewrite iterations
    if reviewer_feedback is not None and iteration > 1:
        defect_lines = "\n".join(
            f"  - [{d.severity}] {d.description}" +
            (f" (step: {d.logic_step})" if d.logic_step else "") +
            (f"\n    Suggested fix: {d.suggested_fix}" if d.suggested_fix else "")
            for d in reviewer_feedback.defects
        )
        correction_lines = "\n".join(
            f"  - {c}" for c in reviewer_feedback.suggested_corrections
        )
        parts.append(
            CODER_REWRITE_ADDENDUM.format(
                iteration=iteration,
                defects=defect_lines or "  (none listed)",
                corrections=correction_lines or "  (none listed)",
            )
        )

    return "".join(parts)


class CoderAgent:
    """Consumes a Logic Map and produces Python code + tests."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(
        self,
        logic_map: LogicMap,
        reviewer_feedback: ReviewerOutput | None = None,
        iteration: int = 1,
        run_version: int = 1,
    ) -> CoderOutput:
        """
        Generate Python code from the Logic Map.

        On iterations > 1, includes reviewer feedback so the agent can
        apply targeted fixes.

        Raises
        ------
        pydantic.ValidationError
            If the LLM response doesn't match the CoderOutput schema.
        """
        user_prompt = _build_coder_user_prompt(
            logic_map, reviewer_feedback, iteration
        )
        if run_version > 1:
            user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"
        schema = CoderOutput.model_json_schema()

        raw = self.provider.generate(
            system_prompt=CODER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
        )

        return CoderOutput.model_validate(raw)
