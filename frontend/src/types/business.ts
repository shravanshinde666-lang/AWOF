export interface CIPSResultItem {
  row_index: number;
  entity_id: string | null;
  prediction: string | number | boolean | null;
  risk_probability: number | null;
  cips_score: number;
  priority_level: "immediate" | "high" | "medium" | "monitor";
  signals: Record<string, number>;
  effective_weights: Record<string, number>;
  top_reasons: string[];
  recommended_action: string;
}

export interface BusinessPriorityResult {
  dataset_id: string;
  model_id: string | null;
  problem_type: string;
  applicability: "applicable" | "partially_applicable" | "not_applicable";
  risk_direction: string | null;
  risk_direction_warning: string | null;
  signal_mapping: Array<{ signal: string; source_column: string }>;
  effective_weights: Record<string, number>;
  summary: { entities_scored: number; immediate_count: number; high_count: number; medium_count: number; monitor_count: number; signals_used: string[]; signals_missing: string[] };
  items: CIPSResultItem[];
  warnings: string[];
}
