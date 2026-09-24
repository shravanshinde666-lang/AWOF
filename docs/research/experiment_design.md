# Phase 8 research experiment design

## Research question

Phase 8 evaluates a narrow, testable question: whether AWOF can avoid
unnecessary workflow operations and model training while retaining comparable
model performance to a reasonable fixed pipeline. It does not claim that AWOF
is universally faster, more accurate, or statistically superior. Results are
measurements for the supplied dataset and configuration.

The research questions are whether adaptive capability selection avoids
unnecessary operations, whether AWGA/pruning reduce executed modules, whether
AMRA reduces trained models, how runtime and Python-tracked memory compare, how the
appropriate model performance compares, and whether applicable explainability
and business-priority outputs are retained.

## Compared workflows

### Fixed pipeline

The fixed baseline is a deterministic conventional tabular workflow. For a
supervised dataset it applies only compatible common preprocessing operations:
duplicate handling, missing-value handling, categorical encoding, scaling where
the selected estimator requires it, and feature filtering. It then trains every
available compatible baseline model:

- classification: logistic regression, random forest classifier, and gradient
  boosting classifier;
- regression: linear regression, ridge regression, random forest regressor,
  and gradient boosting regressor;
- clustering: K-Means, DBSCAN, and agglomerative clustering.

XGBoost is included only when it is actually available. Inapplicable operations
and unavailable models are not counted as executed or trained merely to make
the baseline look worse.

### AWOF adaptive pipeline

The adaptive runner invokes the real AWOF components, rather than reproducing
their decisions for the experiment:

```text
Profile -> Configuration -> ACSA -> AWGA -> Pruning -> Execution
        -> AMRA -> selected model training -> evaluation
        -> explainability/CIPS when applicable
```

Its result records the ACSA decisions, AWGA nodes, pruning decisions, executed
modules, AMRA candidate and selected models, completed models, and applicable
downstream outputs.

## Fair-comparison controls

For supervised experiments, both runners receive the same source rows, target,
problem type, split policy, and `random_state` (default `42`). Preprocessing
used for final predictive metrics is fitted on the training partition only.
Fresh estimator instances are created for every run; a trained model is never
reused across benchmarks.

The runners use the same model-engine family where possible. The intentional
difference is selection strategy: the fixed pipeline trains all compatible
available models, while AWOF trains only the AMRA-selected recommendations.

## What is measured

Each result records wall-clock time using `time.perf_counter`, CPU process time
when available, and peak Python-tracked allocation memory. Memory is explicitly
labelled as a Python allocation measurement; it is not a claim about total
machine RAM.
Timing stages include preprocessing, recommendation/configuration where
applicable, model training, evaluation, and overall execution.

The module count is intentionally coarse. It counts named workflow operations
such as `missing_values`, `duplicate_handling`, `encoding`, `scaling`,
`feature_selection`, `dimensionality_reduction`, the task node, explainability,
and business prioritization. Low-level helper calls are not modules.

Primary performance metrics are F1 for classification, RMSE for regression,
and silhouette score for clustering. The full applicable metric sets are also
retained: accuracy/precision/recall/ROC-AUC, MAE/RMSE/R2, or
silhouette/Davies-Bouldin/Calinski-Harabasz respectively.

## Repeated runs and reproducibility

The API accepts one to ten runs, with three as the normal benchmark default.
Individual run records are retained and mean plus standard deviation are
reported for runtime and memory. Alternating execution order can reduce simple
ordering bias, but filesystem and operating-system caches can still affect
wall-clock measurements.

Experiment metadata stores the random state, run count, relevant AWOF version
identifiers when available, and Python/package versions. Result JSON files do
not contain full uploaded datasets.

## Result interpretation and limitations

The experiment reports factual statements such as "AWOF executed three fewer
modules" or "mean F1 differed by -0.006." It does not infer statistical
significance from a small number of runs and does not automatically call a
performance difference "maintained" without an explicitly configured research
tolerance.

Important limitations are hardware and OS-cache sensitivity of runtime,
limited statistical power at low run counts, Python-allocation-only memory measurement,
heuristic ACSA and AMRA decisions, and dataset-specific benefits. A result is
research evidence for its data and configuration, not a general deployment
guarantee.
