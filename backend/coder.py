"""
Coder Agent — generates Python code + Pytest tests from a Logic Map.

Supports two execution modes:
  1. ``generate()``      — original single-shot mode (backward compat).
  2. ``generate_chunked()`` — iterative mode processing PROCEDURE DIVISION
     chunks with Global State from the Mapper Agent.

Consumes the structured ``LogicMap`` produced by the Analyst Agent and
outputs a ``CoderOutput`` containing implementation code, tests,
design-choice explanations, and logic-step mapping.
"""

from __future__ import annotations

import time

from .contracts import CoderOutput, LogicMap, MapperOutput, ReviewerOutput
from .provider import LLMProvider
from .prompts import CODER_SYSTEM_PROMPT, CODER_CHUNK_SYSTEM_PROMPT, CODER_REWRITE_ADDENDUM


def _serialize_global_state(mapper_output: MapperOutput) -> str:
    """Serialize MapperOutput variables into a compact prompt-friendly string."""
    lines = ["Global State (Variable Mappings):"]
    for v in mapper_output.variables:
        lines.append(
            f"  {v.cobol_name} -> {v.python_name}: "
            f"type={v.python_type}, initial={v.initial_value}, "
            f"pic={v.pic_clause}, level={v.level}"
        )
    return "\n".join(lines)


def _build_coder_user_prompt(
    logic_map: LogicMap,
    reviewer_feedback: ReviewerOutput | None = None,
    iteration: int = 1,
) -> str:
    """
    Build the user prompt containing the Logic Map and optional feedback.
    
    Context Optimization: We strip high-level metadata (executive_summary, 
    business_objective, inputs_and_outputs) to save tokens, as the Coder 
    Agent primarily needs the granular logic dictionary and step-by-step flow.
    """
    parts = [
        "Generate a Python implementation from this Logic Map:\n\n",
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


def _build_chunk_user_prompt(
    global_state_str: str,
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    logic_map: LogicMap,
) -> str:
    """Build the user prompt for a single PROCEDURE DIVISION chunk."""
    parts = [
        f"Chunk {chunk_index + 1} of {total_chunks}.\n\n",
        f"{global_state_str}\n\n",
        "Business Rules (for context):\n",
    ]
    for rule in logic_map.business_rules:
        parts.append(f"  - {rule}\n")

    parts.append("\nCritical Constraints:\n")
    for constraint in logic_map.critical_constraints:
        parts.append(f"  - {constraint}\n")

    parts.append(f"\n--- PROCEDURE DIVISION CHUNK ---\n{chunk}\n--- END CHUNK ---\n")

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
        Generate Python code from the Logic Map (single-shot mode).

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
            max_tokens=3000,
        )

        return CoderOutput.model_validate(raw)

    def generate_chunked(
        self,
        logic_map: LogicMap,
        mapper_output: MapperOutput,
        chunks: list[str],
        reviewer_feedback: ReviewerOutput | None = None,
        iteration: int = 1,
        run_version: int = 1,
    ) -> CoderOutput:
        """
        Generate Python code iteratively over PROCEDURE DIVISION chunks.

        For each chunk, sends the Global State (from the Mapper Agent)
        plus the chunk text to the LLM. Concatenates all generated code
        fragments into a single ``CoderOutput``.

        Parameters
        ----------
        logic_map : LogicMap
            The Analyst's Logic Map (used for business rules / constraints context).
        mapper_output : MapperOutput
            The Mapper Agent's Global State (variable mappings).
        chunks : list[str]
            Ordered PROCEDURE DIVISION chunks from the Chunker.
        reviewer_feedback : ReviewerOutput | None
            Optional feedback from a previous Reviewer iteration.
        iteration : int
            Current Coder→Reviewer iteration number.
        run_version : int
            Pipeline run version.

        Returns
        -------
        CoderOutput
            Consolidated output with concatenated generated_code.
        """
        global_state_str = _serialize_global_state(mapper_output)

        code_fragments: list[str] = []
        all_step_mappings = []
        all_deferred = []
        all_choices: list[str] = []

        for i, chunk in enumerate(chunks):
            print(f"    [CODER] Processing chunk {i + 1}/{len(chunks)}...")

            user_prompt = _build_chunk_user_prompt(
                global_state_str, chunk, i, len(chunks), logic_map
            )

            if reviewer_feedback is not None and iteration > 1:
                defect_lines = "\n".join(
                    f"  - [{d.severity}] {d.description}"
                    for d in reviewer_feedback.defects
                )
                user_prompt += (
                    f"\n\nIteration {iteration} Feedback:\n"
                    f"Defects:\n{defect_lines or '  (none)'}\n"
                    "Apply fixes only.\n"
                )

            if run_version > 1:
                user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"

            # Per-chunk schema is a subset — no generated_tests field
            chunk_schema = {
                "type": "object",
                "properties": {
                    "generated_code": {"type": "string"},
                    "implementation_choices": {"type": "string"},
                    "logic_step_mapping": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "function_or_test_name": {"type": "string"},
                                "logic_step": {"type": "string"},
                                "notes": {"type": "string"},
                            },
                        },
                    },
                    "deferred_items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["generated_code"],
            }

            raw = self.provider.generate(
                system_prompt=CODER_CHUNK_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=chunk_schema,
                max_tokens=2000,
            )

            code_fragments.append(raw.get("generated_code", ""))
            all_choices.append(raw.get("implementation_choices", ""))

            for mapping in raw.get("logic_step_mapping", []):
                all_step_mappings.append(mapping)

            for item in raw.get("deferred_items", []):
                all_deferred.append(item)

            # Rate limiting: Gemini free tier allows 15 RPM
            # Sleep 4.5 seconds between chunks to stay under 13 requests/minute (safe margin)
            if i < len(chunks) - 1:  # Don't sleep after last chunk
                time.sleep(4.5)

        # --- Programmatically inject Global State ---
        global_inits = ["# --- Global State Initializations ---"]
        needs_decimal = False

        for var in mapper_output.variables:
            val = var.initial_value
            if val == "None":
                pass
            elif var.python_type == "str":
                if val == "SPACES":
                    val = '""'
                elif not (val.startswith('"') or val.startswith("'")):
                    val = f'"{val}"'
            elif var.python_type == "Decimal":
                needs_decimal = True
                val = f'Decimal("{val}")'
            
            global_inits.append(f"{var.python_name} = {val}")
        
        if needs_decimal:
            global_inits.insert(0, "from decimal import Decimal\n")
        
        global_inits_str = "\n".join(global_inits)

        # Concatenate all code fragments
        final_python_code = f"{global_inits_str}\n\n" + "\n\n".join(code_fragments)

        # Now do a final single-shot call for tests against the full code
        test_prompt = (
            "Generate Pytest tests for the following Python code.\n"
            "Only output the test file content.\n\n"
            "STRICT TEST ALIGNMENT (CRITICAL): You must ONLY import and call functions/variables that actually exist in the final_python_code string provided below. Do not invent test scenarios for functions you did not write.\n\n"
            f"{global_state_str}\n\n"
            f"```python\n{final_python_code}\n```\n\n"
            "Output JSON: {{\"generated_tests\": \"...\"}}\n"
        )
        try:
            test_raw = self.provider.generate(
                system_prompt="Generate Pytest tests. Output JSON with a single field \"generated_tests\" containing the test file. No markdown.",
                user_prompt=test_prompt,
                schema={"type": "object", "properties": {"generated_tests": {"type": "string"}}, "required": ["generated_tests"]},
                max_tokens=2000,
            )
            generated_tests = test_raw.get("generated_tests", "# Tests not generated")
        except Exception:
            generated_tests = "# Test generation failed during chunked execution"

        # Build the LogicStepMapping models
        from .contracts import LogicStepMapping
        step_mapping_models = []
        for m in all_step_mappings:
            try:
                step_mapping_models.append(LogicStepMapping.model_validate(m))
            except Exception:
                pass  # skip malformed mappings

        # Fallback: ensure at least one mapping
        if not step_mapping_models:
            step_mapping_models = [
                LogicStepMapping(
                    function_or_test_name="main",
                    logic_step="Chunked code generation",
                    notes=f"Generated from {len(chunks)} chunks",
                )
            ]

        return CoderOutput(
            generated_code=final_python_code,
            generated_tests=generated_tests,
            implementation_choices="\n".join(filter(None, all_choices)),
            logic_step_mapping=step_mapping_models,
            deferred_items=all_deferred,
        )
