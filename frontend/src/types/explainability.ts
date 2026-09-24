export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  rank: number;
  direction: "positive" | "negative" | "neutral" | null;
  original_feature: string | null;
}

export interface FeatureContribution extends FeatureImportanceItem {
  contribution: number;
}

export interface LocalExplanation {
  row_index: number;
  entity_id: string | null;
  prediction: string | number | boolean | null;
  prediction_probability: number | null;
  predicted_value: number | string | null;
  probabilities_by_class: Record<string, number>;
  baseline_value: number | null;
  method: string;
  feature_contributions: FeatureContribution[];
  top_positive_factors: FeatureContribution[];
  top_negative_factors: FeatureContribution[];
  warnings: string[];
}

export interface ExplainabilityResult {
  dataset_id: string;
  model_id: string;
  problem_type: "classification" | "regression" | "clustering";
  explanation_method: string;
  model_artifact: string;
  generated_at: string;
  global_importance: FeatureImportanceItem[];
  local_explanations: LocalExplanation[];
  warnings: string[];
}
