# Adaptive Capability Scoring Algorithm (ACSA)

## Purpose and inputs

ACSA-1.0 converts a Dataset Intelligence profile and validated analysis
configuration into deterministic, explainable capability decisions. Inputs are
the profile, business objective, problem type, target configuration, and target
values only when classification imbalance is evaluated.

## Decisions

- Run: score >= 0.70
- Optional: 0.40 <= score < 0.70
- Skip: score < 0.40

Scores are clamped to the normalized range 0 to 1.

## Scoring signals

Missing-value handling combines overall missingness (55%), affected-cell signal
(25%), and maximum column missingness (20%). Duplicate handling normalizes the
duplicate-row percentage against a 20% reference. Outlier analysis combines the
share of numerical columns with IQR outliers (55%) and maximum outlier rate
(45%). Encoding uses categorical feature share and task relevance.

Scaling combines numerical-feature share, task sensitivity, and heterogeneous
numeric ranges. Feature selection combines width (30%), constant/identifier/
high-cardinality signals (35%), and strong correlations (35%). Dimensionality
reduction combines numerical width (45%), correlation redundancy (35%), and
clustering relevance (20%).

Text and temporal analysis use their detected feature shares. Classification,
regression, and clustering use the configured technical problem or segmentation
objective. Explainability and business prioritization use problem type and
business objective. Imbalance handling is classification-only and uses
1 - minority/majority class count after missing targets are excluded.

## Why this differs from simple preprocessing conditionals

Multiple dataset and business signals contribute to normalized capability
scores. Scores are generated before execution, determine Run/Optional/Skip
status, and store reasons and signals for inspection. ACSA does not execute
preprocessing, ML, or business prioritization.

## Limitations

The rules are intentionally interpretable heuristics, not proof that a future
module must run. ACSA does not select a model, infer causal relationships, or
replace user review. Results remain in memory for the current server lifecycle.
