export interface CapabilityResult {
  id: string; label: string; description: string; category: string; score: number;
  decision: "run" | "optional" | "skip"; reasons: string[]; signals: Record<string, string | number | boolean | null>;
}
export interface ACSAResult {
  dataset_id: string; algorithm: string; algorithm_version: string;
  generated_at: string; business_objective: { id: string; label: string };
  problem_type: string; thresholds: Record<string, number>;
  capabilities: CapabilityResult[];
  summary: { total_capabilities: number; run_count: number; optional_count: number; skip_count: number };
}
