"""
Analyst Agent — reads legacy source code and produces a validated Logic Map.

This is the core of Phase 1: one legacy file in, one validated Logic Map out.
"""

from __future__ import annotations

from pathlib import Path

from .contracts import LogicMap
from .prompts import ANALYST_SYSTEM_PROMPT, build_user_prompt
from .provider import LLMProvider


class AnalystAgent:
    """Consumes a legacy source file and returns a validated ``LogicMap``."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def analyze(self, source_path: str | Path) -> LogicMap:
        """
        Analyze a legacy source file.

        1. Read the file from disk.
        2. Build system + user prompts.
        3. Call the LLM provider.
        4. Validate the response against the Pydantic schema.

        Raises
        ------
        FileNotFoundError
            If *source_path* does not exist.
        pydantic.ValidationError
            If the LLM response is missing or has malformed fields.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        source_code = source_path.read_text(encoding="utf-8")
        user_prompt = build_user_prompt(source_code, source_path.name)
        schema = LogicMap.model_json_schema()

        raw_response = self.provider.generate(
            system_prompt=ANALYST_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
        )

        # Validate against the Pydantic contract — raises on any
        # missing / malformed section with the exact field name.
        logic_map = LogicMap.model_validate(raw_response)
        return logic_map
