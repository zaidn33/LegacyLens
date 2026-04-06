Title: LegacyLens – Agentic Enterprise Code Modernization
Overview LegacyLens is an AI-powered modernization engine designed to transform legacy enterprise code (primarily COBOL and Java 8) into modular, cloud-native Python microservices. Large-scale financial institutions are often bottlenecked by decades-old "monolith" code that is expensive to maintain. LegacyLens uses a Multi-Agent Reflection Workflow to extract business logic and rebuild it using modern best practices rather than doing a literal line-by-line translation.
Success Metrics
Compilation Rate: >95% of generated Python code executes without syntax errors on the first pass.
Logic Parity: >80% of generated unit tests pass against the original legacy business rules.
Complexity Reduction: A measurable reduction in cyclomatic complexity compared to the source legacy code.
Messaging
For Engineers: "Stop manual refactoring. Let an agentic pipeline handle the legacy-to-modern bridge while you focus on architecture."
For Enterprise: "Safe, reliable, and documented modernization of your core systems using IBM Granite’s enterprise-grade reliability."
Timeline/Release Planning
Phase 1: Foundation & Extraction – Build the core LangGraph backend. Establish the Analyst Agent to map legacy logic and the Coder Agent for initial Python generation.
Phase 2: The Reflection Engine – Integrate the Reviewer Agent. Implement the "self-correction" loop where the agent analyzes its own code against the original logic map to fix errors.
Phase 3: Interface & Experience – Develop the Next.js 15 dashboard. Focus on the side-by-side diff viewer and the "Agent Thought Stream" so users can see the reasoning process.
Phase 4: Optimization & Scaling – Fine-tune prompt engineering for complex COBOL patterns and add support for running Granite 4.0 Nano locally via Ollama.
Personas
Modernization Mark (Key Persona): A Lead Software Engineer at a bank tasked with moving a 20-year-old billing module to a cloud environment. He needs code that is readable, documented, and proven to work.
User Scenarios Mark uploads a 500-line COBOL file. The Analyst Agent identifies that the code calculates interest rates. The Coder Agent generates a Python FastAPI endpoint. The Reviewer Agent notices a missing edge case for leap years present in the COBOL and triggers a rewrite. Mark receives a final package with the Python code, a README, and a Pytest file.
User Stories / Features / Requirements | Feature | Importance | Explanation | | :--- | :--- | :--- | | Analyst Agent (LangGraph) | Critical | Maps business intent before coding starts to prevent literal translation errors. | | Reflection Loop | High | Vital for reliability; allows the agent to check its own work before presenting it. | | Side-by-Side Diff View | High | Allows the user to quickly compare the legacy logic with the modern result. | | Granite 4.0 Integration | Critical | Uses IBM-native models optimized for enterprise code and instruction following. | | Turso Integration | High | Cloud-native LibSQL database for persistent storage of conversion logs on Vercel. | | Exportable Test Suite | Medium | Ensures the modernization is "trustworthy" by providing automated verification. |
Features Out
Direct Database Migration: We focus on code transformation, not the physical migration of data from mainframes.
Non-Enterprise Languages: We are ignoring niche languages to perfect the COBOL-to-Python pipeline.
Designs
Visuals: Dark-mode "Terminal" aesthetic.
Layout: A three-pane view showing Source Code (Left), Agent Process/Logs (Center), and Modernized Output (Right).
Open Issues
Large File Handling: How will the agent handle COBOL files that exceed 2,000 lines (context window limits)?
Local vs Cloud: Balancing the speed of cloud APIs with the privacy requirements of running Granite locally.
Q&A
Q: Why Python? A: It's the standard for cloud microservices and the easiest language for AI to generate reliably.
Q: Why Turso? A: It provides a "permanent" SQLite-like experience for serverless environments like Vercel.
Other Considerations
Privacy: We should eventually add a "Privacy Mode" that scrubs sensitive variable names before sending them to an LLM.
Agent Handoff Contract
Each agent must produce output in a format directly consumable by the next agent.
Analyst Agent → Coder Agent
business objective
data inputs and outputs
normalized variable dictionary
ordered logic flow
edge cases
critical constraints
assumptions and unresolved ambiguity list
Coder Agent → Reviewer Agent
generated code
explanation of implementation choices
mapping back to logic steps
list of intentionally deferred items
generated tests
Reviewer Agent → Final Output
logic parity findings
defects found
suggested corrections
pass/fail decision
confidence score
Without this, agents may all do “good work” individually but still fail as a system.

Acceptance Criteria by Stage
Analysis Stage passes only if:
the business purpose is identified
core inputs and outputs are named
major branches and calculations are captured
legacy variables are translated into understandable names
edge cases and dependencies are listed
uncertainty is explicitly labeled
Code Generation Stage passes only if:
produced code is syntactically valid Python
logic maps back to the Analyst output
major business rules are implemented
tests are included
no unsupported assumptions are silently introduced
Review Stage passes only if:
generated code is compared against the logic map, not just itself
missing edge cases are identified
logic mismatches are clearly described
final output includes known limitations
This builds on your current success-metric section, which is good but still too high-level for stage-by-stage execution.

Non-Goals and Guardrails
The system must not:
invent missing business rules
silently remove edge-case logic because it looks outdated
assume cryptic variable names without evidence
modernize external systems that are not present in the source
claim full logic parity when dependencies are missing
treat compilation success as proof of behavioral correctness
This matters because the current PRD says the system rebuilds logic rather than doing literal translation, which is good, but that freedom needs boundaries.

Ambiguity and Failure Handling
If the source code is incomplete, ambiguous, or dependent on unavailable artifacts, the system must:
proceed with partial extraction where possible
clearly label inferred vs observed logic
output unresolved questions
reduce confidence score accordingly
avoid presenting uncertain behavior as fact
If the system cannot safely produce modernized code, it should still return:
a partial logic map
dependency gaps
blocked areas
recommended manual follow-up

Confidence Scoring
Each run should produce a confidence score with rationale:
High: core logic, inputs, outputs, and edge cases are directly supported by source
Medium: most logic is supported, but some naming or dependency assumptions exist
Low: major external dependencies, missing modules, or unclear branches limit reliability
This gives users a better sense of whether the result is safe to use.

Open Issues to Add
Your current open issues mention large-file handling and local vs cloud tradeoffs. Add these too:
Cross-file dependency resolution: how to reconstruct logic when core behavior is split across multiple files or subprograms
Copybook / shared schema support: how COBOL copybooks or shared Java DTOs will be parsed and linked
Deterministic artifact formatting: how to ensure every agent outputs predictable structured artifacts
Traceability: how users can trace each generated function back to original business logic
PII handling: define when privacy scrubbing is optional vs mandatory
