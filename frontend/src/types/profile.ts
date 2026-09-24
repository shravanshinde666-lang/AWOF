/**
 * API contracts for the Dataset Intelligence profile endpoints.
 * Values are already aggregated by the backend; no dataset rows are included.
 */

export type ProfileValue = string | number | boolean | null;

export interface DatasetSummary {
  rows: number;
  columns: number;
  total_cells: number;
  missing_cells: number;
  missing_percentage: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  memory_usage_bytes: number;
  numerical_columns: number;
  categorical_columns: number;
  boolean_columns: number;
  datetime_columns: number;
  text_columns: number;
}

export interface ColumnTypeInfo {
  column: string;
  pandas_dtype: string;
  detected_type: string;
  broad_type?: string;
  nullable: boolean;
  unique_count: number;
  unique_percentage: number;
  cardinality: string;
  is_constant: boolean;
  is_identifier_candidate: boolean;
}

export interface MissingValueInfo {
  missing_count: number;
  missing_percentage: number;
  non_missing_count: number;
  severity: string;
}

export interface NumericStatistics {
  count: number;
  mean: number | null;
  median: number | null;
  mode: ProfileValue;
  minimum: number | null;
  maximum: number | null;
  range: number | null;
  variance: number | null;
  standard_deviation: number | null;
  q1: number | null;
  q2: number | null;
  q3: number | null;
  iqr: number | null;
  skewness: number | null;
  kurtosis?: number | null;
}

export interface TopCategory {
  value: ProfileValue;
  count: number;
  percentage: number;
}

export interface CategoricalStatistics {
  count: number;
  unique_count: number;
  mode: ProfileValue;
  mode_frequency: number;
  mode_percentage: number;
  top_values: TopCategory[];
}

export interface OutlierInfo {
  method?: string;
  analyzed_count?: number;
  outlier_count: number;
  outlier_percentage: number;
  lower_bound: number | null;
  upper_bound: number | null;
  q1?: number | null;
  q3?: number | null;
  iqr?: number | null;
  z_score_outlier_count?: number | null;
  z_score_outlier_percentage?: number | null;
}

export interface HistogramData {
  counts: number[];
  bin_edges: number[];
}

export interface DistributionInfo {
  sample_size?: number;
  histogram: HistogramData | null;
  distribution_shape: string;
}

export interface ColumnProfile {
  column?: string;
  type_info: ColumnTypeInfo;
  cardinality?: {
    unique_count: number;
    unique_percentage: number;
    category: string;
  };
  missing: MissingValueInfo;
  is_constant?: boolean;
  numeric_statistics: NumericStatistics | null;
  categorical_statistics: CategoricalStatistics | null;
  outliers: OutlierInfo | null;
  distribution: DistributionInfo | null;
}

export interface CorrelationPair {
  feature_1: string;
  feature_2: string;
  correlation: number | null;
  strength?: string | null;
}

export interface CorrelationAnalysis {
  method: string;
  pairs: CorrelationPair[];
}

export interface DataQualitySummary {
  missing_values: {
    total_missing: number;
    overall_missing_percentage: number;
    by_column: Record<string, MissingValueInfo>;
  };
  duplicates: {
    duplicate_rows: number;
    duplicate_percentage: number;
    has_duplicates: boolean;
  };
  summary: {
    columns_with_missing_values: number;
    constant_columns: number;
    high_cardinality_columns: number;
    columns_with_outliers: number;
  };
}

export interface DatasetProfile {
  dataset_id: string;
  summary: DatasetSummary;
  column_types: ColumnTypeInfo[];
  columns: Record<string, ColumnProfile>;
  quality: DataQualitySummary;
  correlations: CorrelationAnalysis;
  generated_at: string;
}
