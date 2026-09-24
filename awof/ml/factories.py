"""Create estimators only for AMRA registry model IDs."""

from __future__ import annotations

from typing import Any


def build_estimator(model_id: str, *, n_clusters: int = 2) -> Any:
    if model_id == "logistic_regression":
        from .classification.logistic import build
    elif model_id == "random_forest_classifier":
        from .classification.random_forest import build
    elif model_id == "gradient_boosting_classifier":
        from .classification.gradient_boosting import build
    elif model_id == "xgboost_classifier":
        from .classification.xgboost import build
    elif model_id == "linear_regression":
        from .regression.linear import build
    elif model_id == "ridge_regression":
        from .regression.ridge import build
    elif model_id == "random_forest_regressor":
        from .regression.random_forest import build
    elif model_id == "gradient_boosting_regressor":
        from .regression.gradient_boosting import build
    elif model_id == "xgboost_regressor":
        from .regression.xgboost import build
    elif model_id == "kmeans":
        from .clustering.kmeans import build
        return build(n_clusters)
    elif model_id == "dbscan":
        from .clustering.dbscan import build
    elif model_id == "agglomerative_clustering":
        from .clustering.agglomerative import build
        return build(n_clusters)
    else:
        raise ValueError(f"Unsupported model ID: {model_id}")
    return build()
