export type TargetRequirement = "required" | "optional" | "none";
export type ProblemType = "classification" | "regression" | "clustering" | "business_analysis" | "unknown";

export interface BusinessObjective {
  id: string;
  label: string;
  description: string;
  target_requirement: TargetRequirement;
  supported_problem_types: ProblemType[];
}

export interface TargetCandidate {
  column: string;
  detected_type: string;
  unique_count: number;
  missing_percentage: number;
  identifier_candidate: boolean;
  constant: boolean;
  suggested_problem_type: ProblemType;
  target_suitability: "high" | "medium" | "low" | "unsuitable";
  reasons: string[];
  warnings: string[];
}

export interface ConfigurationPayload {
  business_objective: string;
  target_column: string | null;
}

export interface AnalysisConfiguration {
  dataset_id: string;
  business_objective: { id: string; label: string };
  target: { column: string; detected_type: string; suitability: string } | null;
  problem_type: ProblemType;
  valid: boolean;
  warnings: string[];
  errors: string[];
}
