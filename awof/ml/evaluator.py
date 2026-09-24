"""Metric calculation with validity checks and JSON-safe results."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    calinski_harabasz_score,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)


def _rounded(value: float | np.floating[Any] | None) -> float | None:
    return None if value is None or not np.isfinite(value) else round(float(value), 6)


def classification_metrics(y_true: Any, predictions: Any, probabilities: Any | None = None) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    metrics: dict[str, Any] = {
        "accuracy": _rounded(accuracy_score(y_true, predictions)),
        "precision": _rounded(precision_score(y_true, predictions, average="weighted", zero_division=0)),
        "recall": _rounded(recall_score(y_true, predictions, average="weighted", zero_division=0)),
        "f1": _rounded(f1_score(y_true, predictions, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
        "roc_auc": None,
        "roc_auc_explanation": None,
    }
    if probabilities is None:
        metrics["roc_auc_explanation"] = "The selected model does not provide probability estimates."
        return metrics, warnings
    try:
        labels = np.unique(y_true)
        if len(labels) < 2:
            raise ValueError("ROC-AUC requires at least two test classes.")
        if len(labels) == 2:
            metrics["roc_auc"] = _rounded(roc_auc_score(y_true, probabilities[:, 1]))
        else:
            metrics["roc_auc"] = _rounded(roc_auc_score(y_true, probabilities, multi_class="ovr", average="weighted"))
    except (ValueError, IndexError) as exc:
        metrics["roc_auc_explanation"] = str(exc)
        warnings.append("ROC-AUC was unavailable for this test split.")
    return metrics, warnings


def regression_metrics(y_true: Any, predictions: Any) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    mse = mean_squared_error(y_true, predictions)
    metrics: dict[str, Any] = {
        "mae": _rounded(mean_absolute_error(y_true, predictions)),
        "mse": _rounded(mse),
        "rmse": _rounded(np.sqrt(mse)),
        "r2": _rounded(r2_score(y_true, predictions)),
        "mape": None,
    }
    values = np.asarray(y_true, dtype=float)
    if np.any(values == 0):
        warnings.append("MAPE is unavailable because the test target contains zero values.")
    else:
        metrics["mape"] = _rounded(np.mean(np.abs((values - np.asarray(predictions)) / values)) * 100)
    return metrics, warnings


def clustering_metrics(features: Any, labels: Any) -> tuple[dict[str, Any], list[str]]:
    labels_array = np.asarray(labels)
    noise_mask = labels_array == -1
    valid_features = np.asarray(features)[~noise_mask]
    valid_labels = labels_array[~noise_mask]
    unique = np.unique(valid_labels)
    metrics: dict[str, Any] = {
        "cluster_count": int(len(unique)),
        "noise_count": int(noise_mask.sum()),
        "noise_percentage": _rounded(float(noise_mask.mean() * 100) if len(labels_array) else 0.0),
        "silhouette_score": None,
        "davies_bouldin_score": None,
        "calinski_harabasz_score": None,
    }
    warnings: list[str] = []
    if len(unique) < 2 or len(valid_features) <= len(unique):
        warnings.append("Cluster quality metrics require at least two non-noise clusters with sufficient samples.")
        return metrics, warnings
    try:
        metrics["silhouette_score"] = _rounded(silhouette_score(valid_features, valid_labels))
        metrics["davies_bouldin_score"] = _rounded(davies_bouldin_score(valid_features, valid_labels))
        metrics["calinski_harabasz_score"] = _rounded(calinski_harabasz_score(valid_features, valid_labels))
    except ValueError as exc:
        warnings.append(f"Cluster quality metrics were unavailable: {exc}")
    return metrics, warnings
