/**
 * TypeScript interfaces matching the backend Pydantic models.
 */

export interface PipelineError {
  stage: string;
  error_type: string;
  message: string;
  recoverable: boolean;
  iteration: number | null;
}

export interface ConfidenceAssessment {
  level: "High" | "Medium" | "Low";
  rationale: string;
}

export interface DictEntry {
  legacy_name: string;
  proposed_modern_name: string;
  meaning: string;
  confidence: "High" | "Medium" | "Low";
}

export interface InputsAndOutputs {
  inputs: string[];
  outputs: string[];
  external_touchpoints: string[];
}

export interface AssumptionsAndAmbiguities {
  observed: string[];
  inferred: string[];
  unknown: string[];
}

export interface LogicMap {
  executive_summary: string;
  business_objective: string;
  inputs_and_outputs: InputsAndOutputs;
  logic_dictionary: DictEntry[];
  step_by_step_logic_flow: string[];
  business_rules: string[];
  edge_cases: string[];
  dependencies: string[];
  critical_constraints: string[];
  assumptions_and_ambiguities: AssumptionsAndAmbiguities;
  test_relevant_scenarios: string[];
  confidence_assessment: ConfidenceAssessment;
}

export interface LogicStepMapping {
  function_or_test_name: string;
  logic_step: string;
  notes: string;
}

export interface CoderOutput {
  generated_code: string;
  generated_tests: string;
  implementation_choices: string;
  logic_step_mapping: LogicStepMapping[];
  deferred_items: string[];
}

export interface Defect {
  description: string;
  severity: "critical" | "major" | "minor";
  logic_step: string;
  suggested_fix: string;
}

export interface ReviewerOutput {
  logic_parity_findings: string;
  defects: Defect[];
  suggested_corrections: string[];
  passed: boolean;
  confidence: ConfidenceAssessment;
  known_limitations: string[];
}

export interface PipelineResult {
  logic_map: LogicMap;
  coder_output: CoderOutput | null;
  reviewer_output: ReviewerOutput | null;
  iterations: number;
  final_confidence: ConfidenceAssessment;
  errors: PipelineError[];
}

export interface JobStatusResponse {
  job_id: string;
  file_name: string;
  source_code: string;
  status: string;
  current_node: string | null;
  iteration: number;
  result: PipelineResult | null;
  error: string | null;
  errors: PipelineError[];
}

export interface JobSummary {
  job_id: string;
  file_name: string;
  status: string;
  confidence_level: string | null;
  iterations: number;
  has_errors: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: JobSummary[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
