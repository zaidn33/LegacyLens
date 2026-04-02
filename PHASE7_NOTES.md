# Phase 7 Notes: Re-runs, Diff, and Versioning

## Lineage Edge Cases
Lineage is explicitly tracked using the `parent_job_id` column. We enforce a flatten-to-root hierarchy: when re-running a child job, the new job points to the master root `parent_job_id` rather than chaining sequentially to the child. This ensures SQL grouping efficiently retrieves every run version without recursive CTEs.

## Diff Structure Design
The diff payload avoids heavy caching and is explicitly generated dynamically upon the `GET /api/v1/jobs/{id}/diff/{other_job_id}` request. The response returns structured JSON adhering tightly to the nested `DiffResponse` model contract (`CodeDelta`, `LogicMapDelta`, `ConfidenceDelta`, `DefectDelta`). It does not return raw unifying diff strings. For example, `CodeDelta` precisely holds `lines_before`, `lines_after`, and an array of `changed_line_numbers` computed via `difflib.SequenceMatcher`.

## Dependency Re-run Limitation
**Important Gap**: As designed in Phase 6, multi-file dependency blobs (i.e. uploaded .cbl artifacts supporting the primary source) are not permanently synced to disk or recorded persistently in the SQLite DB blobs. Because of this architectural inheritance, job re-runs strictly process off the primary parsed legacy code strings available locally or injected directly through memory state. Support for full blob retrieval of child dependent files is a known limitation that must be addressed if re-runs eventually require swapped include maps.

## Known Remaining Issues
- **Graph Storage Limits:** Extremely large logic hierarchies might run slowly when parsed purely dynamically during the diff phase, hinting maybe a background worker queue for diff aggregation might be required later.
- **Provider Mock Scaling:** Passing `run_version` through LLM contexts securely triggers local mock variations, but real LLMs might misinterpret large `System Runtime Context` injected footprints as part of the domain prompt if not fenced properly. We maintain this approach for now to preserve test statelessness.
