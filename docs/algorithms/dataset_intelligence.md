# Dataset Intelligence Engine

## Purpose

The Dataset Intelligence Engine produces a JSON-serializable descriptive profile
of an uploaded tabular dataset. It is the factual input for later AWOF stages and
does not alter the source data. In particular, it does not impute missing values,
remove duplicate rows or outliers, encode or scale features, select features, or
train machine-learning models.

## Input and output

The profiler accepts one Pandas `DataFrame` loaded by the dataset service. It
returns an aggregated profile containing:

- dataset dimensions, memory usage, missing cells, and duplicate rows;
- a detected type and cardinality record for every column;
- per-column missingness, constant-column, and identifier-candidate signals;
- numerical or categorical descriptive statistics as applicable;
- IQR outlier information and bounded histogram data for suitable numerical
  columns;
- Pearson numerical-correlation pairs; and
- a factual data-quality summary.

The profile contains metadata and aggregates only. It does not return the complete
uploaded dataset, and categorical top values are limited so high-cardinality
columns cannot produce an unbounded response.

## Type-detection heuristics

Type detection is intentionally heuristic rather than a claim about a column's
business meaning. It combines the Pandas dtype, non-null values, value patterns,
column cardinality, and limited column-name clues. A column may be classified as
one of `boolean`, `binary`, `nominal`, `ordinal_candidate`, `integer`,
`continuous_numeric`, `datetime`, `text`, `identifier_candidate`, or `unknown`.

- Boolean and binary candidates include boolean dtypes and constrained values such
  as true/false, yes/no, y/n, or 0/1.
- Numeric columns are separated into integer-valued and continuous numeric data.
- Object/string columns are safely tested for datetime-like values without
  mutating the original DataFrame. String detection requires at least 80% of
  values to look date-shaped and at least 90% to parse safely; native datetime
  dtypes and date-like objects are recognized directly.
- Short, repeating strings are normally nominal; long, free-form, multiword
  strings are text candidates. The current text heuristic requires an average
  length of at least 20 characters plus either at least three words on average
  or at least 50% unique non-null values.
- Ordered labels are marked `ordinal_candidate` only when a strongly recognizable
  ordered pattern exists. Ordinary strings are not assumed to be ordinal.
- Near-unique values and identifier-like names (for example `id` or
  `customer_id`) are signals for an identifier candidate, not proof that the
  attribute should be removed. A matching identifier-like name needs at least
  50% unique non-null values; otherwise, only short nominal/binary codes with
  at least 10 non-null values and at least 98% uniqueness qualify. Numeric
  uniqueness alone is not treated as an identifier.
- Empty or all-null columns can remain `unknown` and are profiled safely.

Cardinality is calculated for every column as a unique count and percentage of
rows. The profiler assigns the descriptive labels `constant`, `low`, `medium`,
`high`, and `near_unique` through centralized, row-relative thresholds. Keeping
those thresholds in one place makes the labels consistent and allows later AWOF
modules to reuse them. The current thresholds are:

- `constant`: at most 1 unique value;
- `near_unique`: at least 90% unique values (evaluated before other labels);
- `low`: at most 10 unique values;
- `medium`: at most 50 unique values or at most 20% unique values; and
- `high`: any remaining non-constant, non-near-unique case.

## Statistical measures

For usable numerical columns, the profile reports count, mean, median, mode,
minimum, maximum, range, variance, standard deviation, first/second/third
quartiles, interquartile range, and skewness where these measures are meaningful.
Constant, all-null, and very small samples are handled without emitting invalid
JSON values.

For categorical, binary, and boolean columns, the profile reports non-null count,
unique count, mode, mode frequency, mode percentage, and a bounded list of top
values. These values are descriptive; they do not establish an ordering or a
causal relationship.

## Missing values and duplicates

At column level, the profiler records missing count, non-missing count, missing
percentage, and a descriptive severity (`none`, `low`, `moderate`, `high`, or
`critical`). At dataset level it records total missing cells and overall missing
percentage. Duplicate analysis reports the number and percentage of duplicate
rows without deleting them. Missingness uses centralized inclusive thresholds:
`none` for 0%, `low` through 5%, `moderate` through 20%, `high` through 50%, and
`critical` above 50%.

## IQR outlier detection

Outliers are detected for appropriate numerical columns using the interquartile
range (IQR) method:

```text
IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 × IQR

Upper Bound = Q3 + 1.5 × IQR
```

Values below the lower bound or above the upper bound are counted as outliers.
The profile reports the bounds, count, and percentage; it never removes or changes
the values. Constant columns and cases where the method is not meaningful are
handled gracefully. Optional Z-score information, when present, is supplementary;
IQR remains the primary detection method.

## Distribution analysis

For suitable numerical columns, bounded histogram bin counts and bin edges are
computed from the column's finite non-null values. Histograms use no more than
30 bins. The profile may also include a
conservative descriptive shape label such as `symmetric_candidate`,
`right_skewed`, `left_skewed`, or `constant`. These labels are exploratory aids,
not formal normality tests.

## Correlation analysis

The profiler calculates Pearson correlation for suitable pairs of numerical
columns. It returns each unordered pair once, without self-correlations. Columns
with too few usable observations, constant values, non-finite values, or an
unavailable correlation are skipped or represented safely rather than causing a
profiling failure.

When a correlation-strength label is returned, it is based on the absolute
coefficient: `very_weak` through 0.19, `weak` through 0.39, `moderate` through
0.59, `strong` through 0.79, and `very_strong` above 0.79.

Correlation measures linear association only. Correlation does **not** imply
causation, and a strong correlation must not be interpreted as evidence that one
attribute causes another.

## Limitations

- Type detection cannot reliably infer domain semantics from values alone.
- Datetime parsing and ordered-category recognition can be ambiguous.
- IQR is a univariate detector and can miss multivariate anomalies.
- Pearson correlation is sensitive to linearity, outliers, and sample size.
- The generated profile is stored in memory for this phase, so it is not durable
  across a backend restart.
