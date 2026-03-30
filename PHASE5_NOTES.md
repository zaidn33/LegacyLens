# LegacyLens Phase 5 Notes

This document formalizes the validation process and prompt tuning results following the deployment of the production LLM provider and integration of the Granite/OpenAI-compatible logic layers.

## 1. COBOL Sample Testing

Three distinct COBOL samples were parsed through the Analyst Agent E2E to test the prompt's ability to extract logic without hallucinating or resolving ambiguity silently.

### A. `samples/simple_batch.cbl` (New Sample)
*   **Profile:** Simple batch processing module containing sequential reads and basic Math logic, devoid of `PERFORM` loops.
*   **Insights Identified:**
    *   Found zero `PERFORM` loops, confirming the file maps simply top-to-bottom.
    *   **Prompt impact:** The previous prompts assumed complex nesting, leading to artificial grouping of basic `IF/ELSE` blocks. The tightened prompt prevents the model from injecting non-existent business rules, forcing it to stick precisely to the `EMP-YEARS-SERVICE` logic.

### B. `samples/sample.cbl` (Existing Sample)
*   **Profile:** A larger, file-processing program handling active customer records via tiered calculations.
*   **Insights Identified:**
    *   Contained complex loop dependencies with `PERFORM UNTIL END-OF-FILE`.
    *   **Prompt impact:** This verified that missing parameters from the `COPY CUSTOMER-RECORD` file were correctly flagged as `unknown` unresolvable ambiguities instead of guessed schemas.

### C. `samples/messy_billing.cbl` (Existing Sample)
*   **Profile:** Contains messy code with nested conditionals, dead branches, and missing copybooks (`MSGMACRO`).
*   **Insights Identified:**
    *   The `DUMMY-YR` unused blocks were explicitly noted in the extraction.
    *   **Prompt impact:** Tested the Agent's resilience against unstructured flows. Strict guidelines ensured the Reviewer correctly evaluated the resulting output missing the MSGMACRO fields as an unsupported assumption defect.

## 2. Prompt Tuning Iteration Summary

1.  **Analyst Prompt:** Added explicit directives `"STRICTLY FORBIDDEN: Do not invent or hallucinate missing business rules"` and ordered the labeling of ambiguity (`observed logic, reasonable inference, unknown/unresolved`). This successfully stopped the LLM from trying to pre-solve undefined edge cases (like the handling of negative values in `sample.cbl`).
2.  **Coder Prompt:** Added the requirement: `"Create AT LEAST ONE specific Pytest test for each Critical Constraint".` Ensures pipeline gates are mathematically protected via unit tests. Re-worded traceability mappings to enforce pasting the EXACT Logic Map string rather than summary labels.
3.  **Reviewer Prompt:** Upgraded minor constraints so that a failure in *any* Critical Constraint auto-fails the job, and made lack of edge-case coverage a mandatory `MAJOR` defect severity.

## 3. Confidence Calibration Results

Based on E2E testing with the updated metrics:

*   **Signals Used:** Output was initially clustering entirely at `HIGH` confidence regardless of unresolved items, simply because generated tests passed. 
*   **Lever Adjustments in `scoring.py`:**
    *   **Strict Penalty:** We updated `scoring.py` so that a single `major` defect permanently deducts from the score (previously it required 2 major defects).
    *   **Ambiguity Cap:** An intentional ceiling was added: if the Analyst `assumptions_and_ambiguities` contain items correctly flagged as `unknown` or `unresolved`, the final pipeline confidence score applies a hard cap at `MEDIUM`, preventing over-confidence in code derived from incomplete legacy specs.

## 4. Known Limitations

*   Without explicit context files (like JCL streams or parsed Copybooks), `LegacyLens` remains bound by file-scoped analysis. 
*   Current implementation relies on `tenacity` retry logic to gracefully fail 429 rate-limit errors from the LLM, but prolonged enterprise rate-limiting will timeout the `LanguageGraph` threadpool if retries exhaust beyond typical maximum window length (currently 10 seconds).
*   **Python Target Limitation:** The LangChain/Pydantic v1 vs v2 compatibility warning has been explicitly suppressed via `warnings.filterwarnings()` in `backend/server.py` and `backend/pipeline.py`. However, due to the testing environment natively running Python 3.14.3, actual binary compatibility on Python 3.11/3.12 has not been physically validated through automated suites, necessitating environmental profiling if downgraded natively.
