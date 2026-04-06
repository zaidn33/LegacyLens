"""
Chunker — COBOL source pre-processor for semantic chunking.

Splits a raw COBOL file into:
  1. Global Context: DATA DIVISION through end of WORKING-STORAGE SECTION.
  2. Logic Chunks:  PROCEDURE DIVISION split by paragraph headers.

This is a pure-Python parser — no LLM calls.
"""

from __future__ import annotations

import re


# Regex matching a COBOL paragraph header in area A (columns 8–11).
# Paragraph headers are identifiers beginning in area A, followed by a period.
# Examples: "       0000-MAIN.", "       4100-CALC-BASE."
_PARAGRAPH_RE = re.compile(
    r"^[ ]{7}[A-Z0-9][A-Z0-9a-z\-]*\.\s*$"
)


def extract_global_context(source_code: str) -> str:
    """Extract from DATA DIVISION through end of WORKING-STORAGE SECTION.

    Returns the matched text block as a single string.
    If the expected divisions are not found, returns an empty string.
    """
    lines = source_code.splitlines()
    start_idx: int | None = None
    end_idx: int | None = None

    for i, line in enumerate(lines):
        upper = line.upper().strip()

        # Look for DATA DIVISION start
        if start_idx is None and "DATA DIVISION" in upper:
            start_idx = i
            continue

        # Stop at PROCEDURE DIVISION (exclusive)
        if start_idx is not None and "PROCEDURE DIVISION" in upper:
            end_idx = i
            break

    if start_idx is None:
        return ""

    # If PROCEDURE DIVISION was never found, take everything after DATA DIVISION
    if end_idx is None:
        end_idx = len(lines)

    return "\n".join(lines[start_idx:end_idx])


def extract_logic_chunks(
    source_code: str,
    target_size: int = 75,
) -> list[str]:
    """Extract the PROCEDURE DIVISION and split into paragraph-level chunks.

    Parameters
    ----------
    source_code : str
        Full COBOL source text.
    target_size : int
        Advisory target lines per chunk (50-100 range).
        Paragraphs are never split mid-body; if a single paragraph
        exceeds *target_size* it is kept as one chunk.

    Returns
    -------
    list[str]
        Ordered list of text chunks, each starting with its
        paragraph header line.
    """
    lines = source_code.splitlines()

    # Find PROCEDURE DIVISION start
    proc_start: int | None = None
    for i, line in enumerate(lines):
        if "PROCEDURE DIVISION" in line.upper():
            proc_start = i
            break

    if proc_start is None:
        return []

    proc_lines = lines[proc_start:]

    # Split into paragraphs by detecting headers
    paragraphs: list[list[str]] = []
    current: list[str] = []

    for line in proc_lines:
        if _PARAGRAPH_RE.match(line) and current:
            # New paragraph header found — flush the current paragraph
            paragraphs.append(current)
            current = [line]
        else:
            current.append(line)

    # Flush the last paragraph
    if current:
        paragraphs.append(current)

    # Merge small adjacent paragraphs if they'd fit within target_size
    chunks: list[str] = []
    buffer: list[str] = []

    for para in paragraphs:
        if buffer and (len(buffer) + len(para)) > target_size:
            # Flush buffer as a chunk
            chunks.append("\n".join(buffer))
            buffer = para[:]
        else:
            buffer.extend(para)

    # Flush remaining buffer
    if buffer:
        chunks.append("\n".join(buffer))

    return chunks
