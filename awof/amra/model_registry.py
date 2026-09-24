"""The deterministic, versioned catalogue used by AMRA."""

from __future__ import annotations

from importlib.util import find_spec
from typing import Any


TOP_K_CLASSIFICATION = 3
TOP_K_REGRESSION = 3
TOP_K_CLUSTERING = 2


def _model(
    model_id: str,
    label: str,
    problem_type: str,
    family: str,
    *,
    requires_scaling: bool,
    supports_non_linear: bool,
    handles_high_dimension: bool,
    handles_large_dataset: bool,
    handles_imbalance: bool,
    interpretable: bool,
    training_complexity: str,
    available: bool = True,
) -> dict[str, Any]:
    return {
        "id": model_id,
        "label": label,
        "problem_type": problem_type,
        "family": family,
        "requires_scaling": requires_scaling,
        "supports_non_linear": supports_non_linear,
        "handles_high_dimension": handles_high_dimension,
        "handles_large_dataset": handles_large_dataset,
        "handles_imbalance": handles_imbalance,
        "interpretable": interpretable,
        "training_complexity": training_complexity,
        "available": available,
    }


XGBOOST_AVAILABLE = find_spec("xgboost") is not None

# Order is intentional: it is AMRA's deterministic tie-breaker.
MODEL_REGISTRY: list[dict[str, Any]] = [
    _model("logistic_regression", "Logistic Regression", "classification", "linear", requires_scaling=True, supports_non_linear=False, handles_high_dimension=True, handles_large_dataset=True, handles_imbalance=False, interpretable=True, training_complexity="low"),
    _model("random_forest_classifier", "Random Forest Classifier", "classification", "random_forest", requires_scaling=False, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=True, handles_imbalance=True, interpretable=False, training_complexity="medium"),
    _model("gradient_boosting_classifier", "Gradient Boosting Classifier", "classification", "gradient_boosting", requires_scaling=False, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=False, handles_imbalance=False, interpretable=False, training_complexity="medium"),
    _model("xgboost_classifier", "XGBoost Classifier", "classification", "xgboost", requires_scaling=False, supports_non_linear=True, handles_high_dimension=True, handles_large_dataset=True, handles_imbalance=True, interpretable=False, training_complexity="medium", available=XGBOOST_AVAILABLE),
    _model("linear_regression", "Linear Regression", "regression", "linear", requires_scaling=False, supports_non_linear=False, handles_high_dimension=False, handles_large_dataset=True, handles_imbalance=False, interpretable=True, training_complexity="low"),
    _model("ridge_regression", "Ridge Regression", "regression", "linear", requires_scaling=True, supports_non_linear=False, handles_high_dimension=True, handles_large_dataset=True, handles_imbalance=False, interpretable=True, training_complexity="low"),
    _model("random_forest_regressor", "Random Forest Regressor", "regression", "random_forest", requires_scaling=False, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=True, handles_imbalance=False, interpretable=False, training_complexity="medium"),
    _model("gradient_boosting_regressor", "Gradient Boosting Regressor", "regression", "gradient_boosting", requires_scaling=False, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=False, handles_imbalance=False, interpretable=False, training_complexity="medium"),
    _model("xgboost_regressor", "XGBoost Regressor", "regression", "xgboost", requires_scaling=False, supports_non_linear=True, handles_high_dimension=True, handles_large_dataset=True, handles_imbalance=False, interpretable=False, training_complexity="medium", available=XGBOOST_AVAILABLE),
    _model("kmeans", "K-Means", "clustering", "centroid", requires_scaling=True, supports_non_linear=False, handles_high_dimension=False, handles_large_dataset=True, handles_imbalance=False, interpretable=True, training_complexity="low"),
    _model("dbscan", "DBSCAN", "clustering", "density", requires_scaling=True, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=False, handles_imbalance=False, interpretable=True, training_complexity="medium"),
    _model("agglomerative_clustering", "Agglomerative Clustering", "clustering", "hierarchical", requires_scaling=True, supports_non_linear=True, handles_high_dimension=False, handles_large_dataset=False, handles_imbalance=False, interpretable=True, training_complexity="high"),
]


def models_for(problem_type: str) -> list[dict[str, Any]]:
    return [model.copy() for model in MODEL_REGISTRY if model["problem_type"] == problem_type]


def top_k_for(problem_type: str) -> int:
    return {
        "classification": TOP_K_CLASSIFICATION,
        "regression": TOP_K_REGRESSION,
        "clustering": TOP_K_CLUSTERING,
    }[problem_type]
