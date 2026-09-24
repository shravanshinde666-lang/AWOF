export type ProblemType = "classification" | "regression" | "clustering";

export interface ModelRecommendation {
  model_id: string;
  label: string;
  score: number;
  rank: number | null;
  decision: "recommended" | "candidate" | "not_selected" | "incompatible";
  reasons: string[];
  signals: Record<string, unknown>;
  estimated_complexity: string;
  available: boolean;
}

export interface AMRAResult {
  dataset_id: string;
  algorithm: "AMRA";
  algorithm_version: string;
  problem_type: ProblemType;
  models: ModelRecommendation[];
  incompatible_models: Array<{ model_id: string; label: string; problem_type: string; score: number; rank: null; decision: "incompatible"; reasons: string[] }>;
  signals: Record<string, unknown>;
  summary: { models_evaluated: number; models_recommended: number; top_k: number; unavailable_models: string[] };
}

export interface ModelTrainingResult {
  model_id: string;
  status: "completed" | "failed";
  amra_score?: number;
  training_duration_ms: number;
  cross_validation_metrics: Record<string, unknown>;
  test_metrics: Record<string, unknown>;
  feature_count: number;
  train_rows: number;
  test_rows: number;
  warnings: string[];
  artifact_filename?: string;
}

export interface ModelEvaluationResult {
  dataset_id: string;
  problem_type: ProblemType;
  results: ModelTrainingResult[];
  best_model: { model_id: string; why_selected: string; test_metrics: Record<string, unknown>; artifact_filename?: string; amra_score?: number } | null;
  comparison: Array<{ model_id: string; status: string; metrics: Record<string, unknown> }>;
}
