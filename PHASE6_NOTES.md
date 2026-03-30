# Phase 6 Notes: Multi-File Project Analysis

This document outlines the architectural decisions, trade-offs, and behavioral changes made during Phase 6 (graduating LegacyLens from single-file execution to multi-file scope resolution).

## Logic Map Linking Strategy

We evaluated two distinct implementation paradigms for integrating dependencies:
1.  **Linked Logic Maps**: Generating a separate Logic Map for every provided file and passing a nested dictionary of graphs down the pipeline.
2.  **Unified Logic Map**: Bundling the entire file array upstream into the Analyst so it natively parses the parent alongside its copies/sub-modules, generating a single, cohesive Logic Map.

**Decision: Unified Logic Map**
We adopted the Unified approach strictly because the Coder and Reviewer agents are required to output a "single coherent Python module". If the LLM generates separated Logic Maps, the code generation tier struggles significantly with cross-referencing state graphs, leading to orchestration hallucination. By shifting the complexity up to the Analyst—having it read the injected `definitions.cpy` context natively when assessing the `main_routine.cbl` execution flow—the resulting architecture map perfectly reflects the *compiled* logic path. The Coder cleanly maps this into Python without needing structural orchestration algorithms.

## Database Additive Migration

To prevent resetting `legacylens.db` completely and destroying the Phase 4/5 historical run logs, the Phase 6 `submitted_files` column was integrated additively.
We updated `init_db()` to explicitly execute:
```sql
ALTER TABLE jobs ADD COLUMN submitted_files TEXT
```
This is wrapped within a `try/except sqlite3.OperationalError` guard. When the backend launches, it injects the new schema safely gracefully skipping dropping logic if the application re-runs on an already-migrated dataset. This satisfies Turso compatibility directly avoiding any schema-loss friction. 

## Dependency Tracking Schema (Contracts)
The string list `dependencies` was heavily expanded into a Pydantic `DependencyResolution` struct array to eliminate guesswork during the UI and Reviewer phases natively. The UI natively uses `dep.reference_name` alongside `dep.status` to immediately map unresolved references with explicit badges instead of relying on frontend text-parsing.

## Known Limitations

-   **Massive Projects**: Because the Unified strategy concats all code strings natively inside the Analyst `user_prompt` payload, this application continues relying on context-window ceilings. If an end-user drags 300 massive COBOL subprograms alongside their entry file, it will physically exceed standard Enterprise model token limits. Resolving this constraint effectively requires graduating iteration pipelines toward RAG vectorization chunking (out-of-scope for Phase 6).
