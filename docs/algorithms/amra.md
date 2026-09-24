# AMRA — Adaptive Model Recommendation Algorithm

## Purpose

AMRA ranks models that are worthwhile to evaluate for the configured task before
any model is trained. It deliberately separates a pre-training suitability
estimate from observed model performance.

## Inputs

AMRA consumes the stored dataset profile, validated analysis configuration,
completed workflow-execution record, and the uploaded dataframe. It derives
deterministic signals: row and feature counts, numerical and categorical-origin
feature ratios, identifier candidates, strong-correlation count, class balance,
high-dimensional and large-dataset flags, and whether workflow scaling ran.

## Registry

The `AMRA-1.0` registry contains classification (logistic regression, random
forest, gradient boosting, optional XGBoost), regression (linear, ridge, random
forest, gradient boosting, optional XGBoost), and clustering (K-Means, DBSCAN,
agglomerative) models. Registry metadata specifies scaling, non-linear,
dimensionality, dataset-size, imbalance, interpretability, and complexity
characteristics. XGBoost is displayed as unavailable when its optional package
is absent; it is never replaced with a different model.

## Scoring and ranking

Each compatible available model starts from a bounded baseline and receives
deterministic adjustments for its registry capabilities and the observed
signals. Examples include a logistic-regression bonus for a moderate feature
set, a ridge bonus for correlated high-dimensional features, penalties for
hierarchical clustering on large data, and K-Means bonuses for predominantly
numeric prepared features. Scores are clamped to `[0.00, 1.00]`.

Models are sorted by score descending, then registry order. The first three
classification/regression models or first two clustering models are marked
`recommended`; other available models are `candidate` or `not_selected`.
Every result carries the signals and human-readable reasons that produced it.

## Limitations

AMRA uses evidence-based heuristics, not an assertion that data is truly linear
or that one model will outperform another. Its score only determines which
models to train. Held-out and cross-validation metrics decide the best trained
model.
