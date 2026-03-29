"""
Coder Agent — generates Python code + Pytest tests from a Logic Map.

Consumes the structured ``LogicMap`` produced by the Analyst Agent and
outputs a ``CoderOutput`` containing implementation code, tests,
design-choice explanations, and logic-step mapping.
"""

from __future__ import annotations

from .contracts import CoderOutput, LogicMap, ReviewerOutput
from .provider import LLMProvider


CODER_SYSTEM_PROMPT = """\
You are the Coder Agent in an enterprise code-modernization pipeline. \
You receive a structured Logic Map extracted from legacy source code \
and produce a modern Python implementation.

## Rules
1. Implement every business rule and critical constraint from the Logic Map.
2. Generate a standalone Python module — no external dependencies beyond \
the standard library unless the logic requires it.
3. Write clean, documented, idiomatic Python 3.11+ code.
4. Generate a Pytest test file that covers:
   - Every critical constraint (these tests MUST pass — they gate the pipeline)
   - Major business rules
   - Edge cases listed in the Logic Map
5. For each generated function, provide a mapping back to the Logic Map step \
it implements.
6. If you intentionally defer any Logic Map item, list it explicitly with \
rationale.
7. Do NOT invent behavior not in the Logic Map. If the Logic Map marks \
something as unknown/ambiguous, either skip it or implement a conservative \
default and flag it as deferred.

## Output — JSON Schema
Return a single JSON object with exactly these fields:

- "generated_code" (string): complete Python source code
- "generated_tests" (string): complete Pytest test file
- "implementation_choices" (string): explanation of key design decisions
- "logic_step_mapping" (array of objects):
    - "function_name" (string)
    - "logic_step" (string)
    - "notes" (string, optional)
- "deferred_items" (array of strings): items intentionally not implemented

Return ONLY the JSON object. No markdown fences, no commentary.\
"""


CODER_REWRITE_ADDENDUM = """\

## Reviewer Feedback (Iteration {iteration})
The Reviewer Agent found defects in your previous implementation. \
Fix the issues listed below while preserving all correct behavior.

### Defects
{defects}

### Suggested Corrections
{corrections}

Do NOT discard working code. Apply targeted fixes only.\
"""


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
        schema = CoderOutput.model_json_schema()

        raw = self.provider.generate(
            system_prompt=CODER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
        )

        return CoderOutput.model_validate(raw)
