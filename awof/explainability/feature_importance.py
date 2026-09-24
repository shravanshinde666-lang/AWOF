"""Feature-name recovery and transparent non-SHAP importance methods."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def _json_value(value: Any) -> Any:
    return value.item() if isinstance(value, np.generic) else value


def transformed_feature_names(pipeline: Any) -> list[str]:
    """Recover names emitted by the fitted ColumnTransformer, never x0/x1."""
    preprocessor = pipeline.named_steps["preprocessor"]
    try:
        return [str(name).replace("categorical__", "").replace("numeric__", "") for name in preprocessor.get_feature_names_out()]
    except (AttributeError, ValueError):
        return [str(name) for name in getattr(pipeline, "feature_names_in_", [])]


def _original_feature(feature: str, source_names: list[str] | None) -> str:
    if source_names:
        for source in sorted(source_names, key=len, reverse=True):
            if feature == source or feature.startswith(f"{source}_"):
                return source
    return feature


def _ranked_items(names: list[str], values: np.ndarray, directions: np.ndarray | None = None, top_n: int = 20, source_names: list[str] | None = None) -> list[dict[str, Any]]:
    values = np.asarray(values, dtype=float).ravel()
    items = []
    for index, value in enumerate(values[:len(names)]):
        direction = None
        if directions is not None and index < len(directions):
            direction = "positive" if directions[index] > 0 else "negative" if directions[index] < 0 else "neutral"
        feature = names[index]
        items.append({"feature": feature, "original_feature": _original_feature(feature, source_names), "importance": round(float(abs(value)), 8), "direction": direction})
    items.sort(key=lambda item: (-item["importance"], item["feature"]))
    for rank, item in enumerate(items[:top_n], start=1):
        item["rank"] = rank
    return items[:top_n]


def global_importance(pipeline: Any, features: pd.DataFrame, target: pd.Series | None = None, top_n: int = 20) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Return a global explanation using the most reliable supported method."""
    model = pipeline.named_steps["model"]
    names = transformed_feature_names(pipeline)
    source_names = [str(name) for name in getattr(pipeline, "feature_names_in_", [])]
    warnings: list[str] = []
    if hasattr(model, "feature_importances_"):
        return "native_feature_importance", _ranked_items(names, np.asarray(model.feature_importances_), top_n=top_n, source_names=source_names), warnings
    if hasattr(model, "coef_"):
        coefficients = np.asarray(model.coef_)
        signed = coefficients if coefficients.ndim == 1 else coefficients.mean(axis=0)
        absolute = np.abs(coefficients) if coefficients.ndim == 1 else np.mean(np.abs(coefficients), axis=0)
        return "linear_coefficients", _ranked_items(names, absolute, np.asarray(signed), top_n, source_names), warnings
    if target is not None and len(features) >= 3:
        result = permutation_importance(pipeline, features, target, n_repeats=5, random_state=42, n_jobs=1)
        raw_names = [str(name) for name in features.columns]
        return "permutation_importance", _ranked_items(raw_names, result.importances_mean, top_n=top_n), warnings
    warnings.append("No supported global importance method is available for this estimator.")
    return "unavailable", [], warnings


def clustering_importance(pipeline: Any, features: pd.DataFrame, top_n: int = 20) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Describe which transformed features distinguish observed clusters."""
    model = pipeline.named_steps["model"]
    transformed = np.asarray(pipeline.named_steps["preprocessor"].transform(features))
    labels = np.asarray(getattr(model, "labels_", []))
    names = transformed_feature_names(pipeline)
    if len(labels) != len(transformed) or len(np.unique(labels)) < 2:
        return "cluster_centroid_differences", [], ["Cluster differences require at least two fitted clusters."]
    centroids = np.vstack([transformed[labels == label].mean(axis=0) for label in np.unique(labels) if label != -1])
    if len(centroids) < 2:
        return "cluster_centroid_differences", [], ["Only one non-noise cluster is available for interpretation."]
    return "cluster_centroid_differences", _ranked_items(names, np.ptp(centroids, axis=0), top_n=top_n, source_names=[str(name) for name in getattr(pipeline, "feature_names_in_", [])]), []


def local_explanation(pipeline: Any, row: pd.DataFrame, problem_type: str, top_n: int = 10) -> tuple[dict[str, Any], list[str]]:
    """Explain one supervised prediction without claiming proxy values are SHAP."""
    model = pipeline.named_steps["model"]
    transformed = np.asarray(pipeline.named_steps["preprocessor"].transform(row))[0]
    names = transformed_feature_names(pipeline)
    prediction = _json_value(pipeline.predict(row)[0])
    response: dict[str, Any] = {"prediction": prediction, "baseline_value": None}
    warnings: list[str] = []
    if problem_type == "classification":
        if hasattr(pipeline, "predict_proba"):
            probabilities = np.asarray(pipeline.predict_proba(row))[0]
            classes = [_json_value(value) for value in model.classes_]
            by_class = {str(label): round(float(probability), 8) for label, probability in zip(classes, probabilities)}
            response["prediction_probability"] = by_class.get(str(prediction))
            response["probabilities_by_class"] = by_class
        else:
            response["prediction_probability"] = None
            response["probabilities_by_class"] = {}
            warnings.append("This classifier does not provide probabilities.")
    else:
        response["predicted_value"] = prediction

    if hasattr(model, "coef_"):
        coefficients = np.asarray(model.coef_)
        if coefficients.ndim == 1:
            selected = coefficients
        elif problem_type == "classification" and len(coefficients) == 1:
            selected = coefficients[0]
            if prediction == _json_value(model.classes_[0]):
                selected = -selected
        elif problem_type == "classification":
            selected = coefficients[list(model.classes_).index(prediction)]
        else:
            selected = coefficients[0]
        contributions = transformed * selected
        response["method"] = "linear_coefficients"
        response["baseline_value"] = round(float(np.ravel(getattr(model, "intercept_", [0]))[0]), 8)
    elif hasattr(model, "feature_importances_"):
        contributions = transformed * np.asarray(model.feature_importances_)
        response["method"] = "native_importance_proxy"
        warnings.append("Local factors are an input-weighted native-importance proxy, not SHAP values.")
    else:
        contributions = np.zeros(len(names))
        response["method"] = "unavailable"
        warnings.append("No reliable local contribution method is available for this estimator.")
    factors = []
    for index, contribution in enumerate(np.asarray(contributions)[:len(names)]):
        factors.append({
            "feature": names[index], "original_feature": _original_feature(names[index], [str(name) for name in getattr(pipeline, "feature_names_in_", [])]),
            "importance": round(float(abs(contribution)), 8), "contribution": round(float(contribution), 8),
            "direction": "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral",
        })
    factors.sort(key=lambda item: (-item["importance"], item["feature"]))
    for rank, item in enumerate(factors[:top_n], start=1):
        item["rank"] = rank
    factors = factors[:top_n]
    response["feature_contributions"] = factors
    response["top_positive_factors"] = [item for item in factors if item["contribution"] > 0][:top_n]
    response["top_negative_factors"] = [item for item in factors if item["contribution"] < 0][:top_n]
    return response, warnings
