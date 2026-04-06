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

    def analyze(self, source_path: str | Path, dependencies_dict: dict[str, str] | None = None) -> LogicMap:
        """
        Analyze a legacy source file from disk.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        source_code = source_path.read_text(encoding="utf-8")
        return self.analyze_source(source_code, source_path.name, dependencies_dict=dependencies_dict)

    def analyze_source(
        self, 
        source_code: str, 
        file_name: str = "source.cbl", 
        dependencies_dict: dict[str, str] | None = None,
        run_version: int = 1
    ) -> LogicMap:
        """
        Analyze a raw legacy source string.
        """
        # --- Pre-processing: Comment Stripping ---
        source_code = self._strip_cobol_comments(source_code)

        user_prompt = build_user_prompt(source_code, file_name, dependencies_dict=dependencies_dict)
        if run_version > 1:
            user_prompt += f"\n\n[System Runtime Context: run_version={run_version}]"
        schema = LogicMap.model_json_schema()

        raw_response = self.provider.generate(
            system_prompt=ANALYST_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=2000,
        )

        # Validate against the Pydantic contract — raises on any
        # missing / malformed section with the exact field name.
        logic_map = LogicMap.model_validate(raw_response)
        return logic_map

    def _strip_cobol_comments(self, code: str) -> str:
        """
        Strip lines featuring an asterisk in column 7.
        Returns the stripped code and logs the count.
        """
        lines = code.splitlines()
        stripped = []
        comment_count = 0
        for line in lines:
            # COBOL comment: index 6 (7th column) is '*'
            if len(line) > 6 and line[6] == "*":
                comment_count += 1
                continue
            stripped.append(line)
        
        if comment_count > 0:
            print(f"  [ANALYST] Stripped {comment_count} COBOL comment lines.")
        
        return "\n".join(stripped)
