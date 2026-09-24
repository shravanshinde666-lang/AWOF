# Machine Learning Engine

## Leakage-safe supervised evaluation

Phase 5 preprocessing execution is workflow demonstration. Final supervised
model evaluation uses separately fitted, training-only preprocessing pipelines
to avoid data leakage.

The engine removes rows with a missing target, removes target, identifier, and
constant features, then performs a deterministic 80/20 split (`random_state=42`).
Classification uses stratification when the class distribution allows it. A
scikit-learn `Pipeline` contains a `ColumnTransformer` and the estimator:

- numerical columns: median imputation and `StandardScaler` only for models
  that require scaling;
- categorical columns: most-frequent imputation and
  `OneHotEncoder(handle_unknown="ignore")`.

The pipeline is fitted on the training partition only; the test partition is
transformed only through that fitted pipeline. Cross-validation clones the same
pipeline for each fold, using up to five stratified folds for classification or
five K-fold splits for regression, reducing folds when necessary.

## Evaluation and failures

Classification records accuracy, weighted precision/recall/F1, valid ROC-AUC,
and confusion matrix. Regression records MAE, MSE, RMSE, R², and valid MAPE.
Clustering records silhouette, Davies-Bouldin, Calinski-Harabasz, cluster count,
and DBSCAN noise statistics only when the metric is mathematically valid.

One model failure is returned as a safe failed result and does not interrupt
other recommended models. Best-model choice is highest F1 (then ROC-AUC) for
classification, lowest RMSE for regression, and highest valid silhouette for
clustering.

## Artifacts

Only the selected best fitted pipeline is serialized with joblib to
`storage/models/`. API responses expose its filename, never an absolute path,
so preprocessing and estimator stay coupled for later use.
