# Phase 7 Notes: Re-runs, Diff, and Versioning

## Lineage & Hierarchy Model
- **Root-based Parentship**: Lineage is explicitly tracked using the `parent_job_id` column. Rather than forming deep chains (`A -> B -> C`), all descendant jobs resolve to the master parent (`B -> A`, `C -> A`). This significantly simplifies DB operations since grouping by COALESCE(parent_job_id, id) efficiently retrieves every run version in one pass.
- **Run Versions**: Run versions are globally sequential per lineage `(MAX(run_version) + 1)` rather than random UUIDs.

## Diff Endpoint
- **Stateless Diffs**: The diff logic (`CodeDelta`, `LogicMapDelta`, `ConfidenceDelta`, `DefectDelta`) is generated dynamically upon the `GET /api/v1/jobs/{id}/diff/{other_job_id}` request. These payloads are built synchronously from SQLite's pipeline result storage.
- **Code Delta Processing**: `difflib.SequenceMatcher` captures additions, deletions, and line offsets without needing AST parsing. The `CodeDelta` model strictly exposes raw lines before/after counts alongside precise lists of modified line numbers.

## Mock Provider Determinism
- **Context Handling**: Diffs can only be robustly tested via integration tests if the underlying `LLMProvider` produces a different output. We chose to securely pass `run_version` through the agentic System Contexts.
- **Mock Overrides**: When `MockProvider` detects `run_version > 1`, it intentionally manipulates outputs (via artificially altering defects or appending comments) to let diff responses populate natively. Existing tests simulating single-run queries remain insulated since default parameter mapping locks `run_version=1`.
