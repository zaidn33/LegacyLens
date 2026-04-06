"""
Mapper Agent — extracts Global State (variable mappings) from COBOL DATA DIVISION.

Receives the Global Context string (DATA DIVISION through WORKING-STORAGE)
produced by the Chunker and returns a validated ``MapperOutput`` containing
structured variable mappings that serve as the single source of truth
for the Coder Agent.
"""

from __future__ import annotations

from .contracts import MapperOutput
from .provider import LLMProvider
from .prompts import MAPPER_SYSTEM_PROMPT


class MapperAgent:
    """Consumes COBOL Global Context and produces structured variable mappings."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def extract_global_state(
        self,
        global_context: str,
        run_version: int = 1,
    ) -> MapperOutput:
        """
        Extract variable mappings from the DATA DIVISION / WORKING-STORAGE.

        Parameters
        ----------
        global_context : str
            The Global Context string extracted by the Chunker
            (DATA DIVISION through end of WORKING-STORAGE SECTION).
        run_version : int
            Pipeline run version for tracking.

        Returns
        -------
        MapperOutput
            Validated variable mappings (Global State).

        Raises
        ------
        pydantic.ValidationError
            If the LLM response doesn't match the MapperOutput schema.
        """
        user_prompt = (
            "Extract all COBOL variables from this DATA DIVISION / "
            "WORKING-STORAGE SECTION:\n\n"
            f"{global_context}"
        )
        if run_version > 1:
            user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"

        schema = MapperOutput.model_json_schema()

        raw = self.provider.generate(
            system_prompt=MAPPER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=2000,
        )

        return MapperOutput.model_validate(raw)
