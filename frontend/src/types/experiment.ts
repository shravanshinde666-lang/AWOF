export type ExperimentProblemType = "classification" | "regression" | "clustering";

/** A single value or the mean and standard deviation across benchmark runs. */
export interface BenchmarkStatistic {
  mean: number;
  std: number;
}

export type MeasuredValue = number | BenchmarkStatistic;

export interface WorkflowModuleMetrics {
  considered: number;
  selected?: number;
  executed: number;
  pruned?: number;
  ids?: string[];
}

export interface ModelExperimentMetrics {
  considered: number;
  selected: number;
  trained: number;
  failed: number;
  considered_ids?: string[];
  selected_ids?: string[];
  trained_ids?: string[];
  failed_ids?: string[];
}

export interface PipelineTimingMetrics {
  profiling?: MeasuredValue;
  configuration_acsa_awga?: MeasuredValue;
  preprocessing?: MeasuredValue;
  pruning?: MeasuredValue;
  execution?: MeasuredValue;
  model_recommendation?: MeasuredValue;
  model_training?: MeasuredValue;
  evaluation?: MeasuredValue;
  overall: MeasuredValue;
}

export interface PipelineResourceMetrics {
  peak_python_memory_mb: MeasuredValue;
  cpu_process_time_ms?: MeasuredValue;
}

export interface SplitMetadata {
  strategy: string;
  random_state: number;
  test_size?: number;
  train_rows?: number;
  test_rows?: number;
}

export interface PipelineExperimentResult {
  run_index?: number;
  pipeline: string;
  problem_type: ExperimentProblemType;
  workflow_modules: WorkflowModuleMetrics;
  models: ModelExperimentMetrics;
  timings_ms: PipelineTimingMetrics;
  resources: PipelineResourceMetrics;
  best_model: BestModelSummary | null;
  best_metrics: Record<string, number | null>;
  split: SplitMetadata | null;
  reproducibility: Record<string, string | number | boolean | null>;
  warnings: string[];
  run_statistics?: {
    timings_ms?: Record<string, BenchmarkStatistic>;
    resources?: Record<string, BenchmarkStatistic>;
  };
}

export interface BestModelSummary {
  model_id: string;
  label?: string;
  test_metrics?: Record<string, number | null>;
}

export interface PerformanceComparison {
  metric: string;
  baseline: number | null;
  awof: number | null;
  difference: number | null;
  direction: string;
}

export interface ExperimentComparison {
  module_reduction_count: number;
  module_reduction_percentage: number | null;
  model_reduction_count: number;
  model_reduction_percentage: number | null;
  execution_time_difference_ms: number;
  execution_time_reduction_percentage: number | null;
  memory_difference_mb: number;
  memory_reduction_percentage: number | null;
  performance: PerformanceComparison;
  factual_statements: string[];
}

export interface ExperimentMetadata {
  runs: number;
  random_state: number;
  [key: string]: string | number | boolean | null;
}

export interface ExperimentRunResults {
  baseline: PipelineExperimentResult[];
  awof: PipelineExperimentResult[];
}

export interface ResearchExperimentResult {
  experiment_id: string;
  dataset_id: string;
  dataset_name: string;
  problem_type: ExperimentProblemType;
  objective: string;
  target: string | null;
  timestamp: string;
  metadata: ExperimentMetadata;
  baseline: PipelineExperimentResult;
  awof: PipelineExperimentResult;
  comparison: ExperimentComparison;
  run_results?: ExperimentRunResults;
  warnings: string[];
}

export interface ExperimentSummary {
  experiment_id: string;
  dataset_id: string;
  dataset_name: string;
  problem_type: ExperimentProblemType;
  objective: string;
  timestamp: string;
  runs: number;
}

export interface ExperimentRequest {
  runs: number;
  experiment_name?: string;
}
