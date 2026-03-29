"""
Pydantic models enforcing the Logic Map schema.

All 12 sections required by ANALYST.md are represented as typed fields.
The LLM returns JSON conforming to this schema; downstream agents consume
the validated model, not raw Markdown.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    """Confidence rating for variable mappings and overall assessment."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class DictEntry(BaseModel):
    """Single row in the Logic Dictionary table."""
    legacy_name: str = Field(..., description="Original variable/field name from legacy code")
    proposed_modern_name: str = Field(..., description="Clear modern descriptor")
    meaning: str = Field(..., description="What this variable represents")
    confidence: ConfidenceLevel = Field(..., description="Mapping confidence")


class InputsAndOutputs(BaseModel):
    """Structured inputs, outputs, and external touchpoints."""
    inputs: list[str] = Field(..., min_length=1)
    outputs: list[str] = Field(..., min_length=1)
    external_touchpoints: list[str] = Field(default_factory=list)


class AssumptionsAndAmbiguities(BaseModel):
    """Three-way split: observed, inferred, unknown."""
    observed: list[str] = Field(default_factory=list)
    inferred: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    """Overall confidence with 2-3 sentence rationale."""
    level: ConfidenceLevel
    rationale: str = Field(..., min_length=10)


# ---------------------------------------------------------------------------
# Root model — the Logic Map
# ---------------------------------------------------------------------------

class LogicMap(BaseModel):
    """
    Complete Logic Map artifact.

    Every field maps 1:1 to a required section header in ANALYST.md.
    A missing or malformed field raises a ``ValidationError`` naming the
    exact problem.
    """

    executive_summary: str = Field(
        ..., min_length=20,
        description="2-4 sentences: what the module does and why it matters",
    )
    business_objective: str = Field(
        ..., min_length=10,
        description="Concise real-world business purpose",
    )
    inputs_and_outputs: InputsAndOutputs
    logic_dictionary: list[DictEntry] = Field(..., min_length=1)
    step_by_step_logic_flow: list[str] = Field(..., min_length=1)
    business_rules: list[str] = Field(..., min_length=1)
    edge_cases: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    critical_constraints: list[str] = Field(default_factory=list)
    assumptions_and_ambiguities: AssumptionsAndAmbiguities
    test_relevant_scenarios: list[str] = Field(..., min_length=1)
    confidence_assessment: ConfidenceAssessment

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @classmethod
    def validate_file(cls, path: str | Path) -> Self:
        """Load and validate a Logic Map from a JSON file on disk."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Logic Map file not found: {path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def write_json(self, path: str | Path) -> Path:
        """Serialize to a pretty-printed JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
        return file_path


# ---------------------------------------------------------------------------
# Phase 2 — Coder Agent → Reviewer Agent handoff
# ---------------------------------------------------------------------------

class LogicStepMapping(BaseModel):
    """Maps a generated function/section back to a Logic Map step."""
    function_name: str = Field(..., description="Name of the generated function or class")
    logic_step: str = Field(..., description="The logic-flow step this implements")
    notes: str = Field(default="", description="Implementation notes or deviations")


class CoderOutput(BaseModel):
    """
    Output contract for the Coder Agent.

    Consumed by the Reviewer Agent for logic-parity checking.
    """
    generated_code: str = Field(
        ..., min_length=10,
        description="Complete Python source code implementing the Logic Map",
    )
    generated_tests: str = Field(
        ..., min_length=10,
        description="Pytest test file covering business rules and critical constraints",
    )
    implementation_choices: str = Field(
        ..., min_length=10,
        description="Explanation of key design decisions made during code generation",
    )
    logic_step_mapping: list[LogicStepMapping] = Field(
        ..., min_length=1,
        description="How each generated function maps back to Logic Map steps",
    )
    deferred_items: list[str] = Field(
        default_factory=list,
        description="Items intentionally not implemented, with rationale",
    )

    def write_json(self, path: str | Path) -> Path:
        """Serialize to a pretty-printed JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
        return file_path


# ---------------------------------------------------------------------------
# Phase 2 — Reviewer Agent → Final Output
# ---------------------------------------------------------------------------

class Defect(BaseModel):
    """A specific defect found during review."""
    description: str = Field(..., description="What is wrong")
    severity: str = Field(..., description="critical | major | minor")
    logic_step: str = Field(default="", description="Which logic step is affected")
    suggested_fix: str = Field(default="", description="How to fix it")


class ReviewerOutput(BaseModel):
    """
    Output contract for the Reviewer Agent.

    Compares generated code against the Logic Map to find mismatches.
    """
    logic_parity_findings: str = Field(
        ..., min_length=10,
        description="Summary of how well the code matches the Logic Map",
    )
    defects: list[Defect] = Field(
        default_factory=list,
        description="List of specific defects found",
    )
    suggested_corrections: list[str] = Field(
        default_factory=list,
        description="Actionable corrections for the Coder Agent",
    )
    passed: bool = Field(
        ...,
        description="True if the code is acceptable, False if rewrite needed",
    )
    confidence: ConfidenceAssessment
    known_limitations: list[str] = Field(
        default_factory=list,
        description="Limitations that cannot be resolved from the available source",
    )

    def write_json(self, path: str | Path) -> Path:
        """Serialize to a pretty-printed JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
        return file_path


# ---------------------------------------------------------------------------
# Phase 2 — Pipeline result (aggregated final output)
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    """Final output of the full Analyst → Coder → Reviewer pipeline."""
    logic_map: LogicMap
    coder_output: CoderOutput
    reviewer_output: ReviewerOutput
    iterations: int = Field(..., ge=1, le=3, description="Number of Coder→Reviewer iterations")
    final_confidence: ConfidenceAssessment
