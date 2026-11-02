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

export interface FeatureMetaSchema {
  name: string;
  type: "numeric" | "integer" | "categorical";
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  step: number | null;
  default_value: string | number | null;
  categories: string[] | null;
}

export interface SampleRowItem {
  row_index: number;
  label: string;
  values: Record<string, string | number | null>;
}

export interface InferenceSchemaResponse {
  dataset_id: string;
  model_id: string;
  problem_type: string;
  target_column: string | null;
  target_classes: string[];
  features: FeatureMetaSchema[];
  sample_rows: SampleRowItem[];
}

export interface LocalFactorItem {
  feature: string;
  importance: number;
  contribution: number | null;
  direction: string | null;
  original_feature: string | null;
}

export interface CounterfactualItem {
  feature: string;
  feature_type: string;
  current_value: string | number | null;
  proposed_value: string | number;
  delta: string;
  projected_prediction: string | number;
  projected_confidence: number | null;
  action_text: string;
  impact: string;
}

export interface PredictionResponse {
  prediction: string | number;
  prediction_label: string;
  probabilities: Record<string, number>;
  confidence: number | null;
  local_factors: LocalFactorItem[];
  counterfactuals: CounterfactualItem[];
}
