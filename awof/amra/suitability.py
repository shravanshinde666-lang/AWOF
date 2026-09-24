"""Deterministic, explainable AMRA suitability rules."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def build_signals(
    profile: dict[str, Any],
    configuration: dict[str, Any],
    execution: dict[str, Any],
    dataframe: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Summarise actual project inputs without inferring unknown properties."""
    summary = profile.get("summary", {})
    types = profile.get("column_types", [])
    target = (configuration.get("target") or {}).get("column")
    features = [column for column in types if column.get("column") != target]
    row_count = int(summary.get("rows", len(dataframe) if dataframe is not None else 0))
    feature_count = len(features)
    numeric_count = sum(item.get("broad_type") == "numerical" for item in features)
    categorical_count = sum(item.get("broad_type") in {"categorical", "boolean"} for item in features)
    identifier_count = sum(bool(item.get("is_identifier_candidate")) for item in features)
    correlations = profile.get("correlations", {}).get("pairs", [])
    strong_correlations = sum(abs(float(pair.get("correlation", 0))) >= 0.7 for pair in correlations)
    imbalance_ratio: float | None = None
    if dataframe is not None and target and target in dataframe:
        values = dataframe[target].dropna().value_counts()
        if len(values) > 1 and int(values.max()) > 0:
            imbalance_ratio = round(float(values.min() / values.max()), 4)
    node_results = execution.get("node_results", [])
    completed_nodes = {item.get("node_id") for item in node_results if item.get("status") == "completed"}
    return {
        "row_count": row_count,
        "feature_count": feature_count,
        "numeric_feature_count": numeric_count,
        "categorical_origin_feature_count": categorical_count,
        "numeric_feature_ratio": round(numeric_count / max(feature_count, 1), 4),
        "categorical_origin_feature_ratio": round(categorical_count / max(feature_count, 1), 4),
        "identifier_candidate_count": identifier_count,
        "strong_correlation_count": strong_correlations,
        "high_dimensional": feature_count >= 50,
        "large_dataset": row_count >= 10_000,
        "moderate_dataset": 100 <= row_count < 10_000,
        "possible_non_linear_structure": categorical_count > 0 or strong_correlations == 0,
        "class_imbalance_ratio": imbalance_ratio,
        "scaling_completed": "scaling" in completed_nodes,
        "prepared_rows": execution.get("summary", {}).get("final_rows"),
        "problem_type": configuration.get("problem_type"),
    }


def score_model(model: dict[str, Any], signals: dict[str, Any]) -> tuple[float, list[str]]:
    """Return a normalized heuristic score and evidence for one compatible model."""
    rows = signals["row_count"]
    features = signals["feature_count"]
    task = model["problem_type"]
    family = model["family"]
    score = 0.48
    reasons = [f"{task.title()} task with {rows:,} rows and {features} candidate features."]

    if model["interpretable"]:
        score += 0.08
        reasons.append("Provides an interpretable model family for comparison.")
    if model["supports_non_linear"] and signals["possible_non_linear_structure"]:
        score += 0.12
        reasons.append("Structured feature signals make a non-linear model family useful to evaluate.")
    if model["handles_large_dataset"] and signals["large_dataset"]:
        score += 0.08
        reasons.append(f"Designed to remain practical for the observed {rows:,}-row dataset.")
    if not model["handles_large_dataset"] and rows > 50_000:
        score -= 0.18
        reasons.append("Training cost is less suitable for this very large dataset.")
    if signals["high_dimensional"]:
        if model["handles_high_dimension"]:
            score += 0.10
            reasons.append(f"Supports the observed high-dimensional feature set ({features} features).")
        else:
            score -= 0.12
            reasons.append(f"May be less efficient with the observed {features} features.")
    if signals["class_imbalance_ratio"] is not None and signals["class_imbalance_ratio"] < 0.5 and task == "classification":
        if model["handles_imbalance"]:
            score += 0.06
            reasons.append("Class imbalance signal favors a model with robust class handling options.")
        else:
            score -= 0.06
            reasons.append("Class imbalance should be monitored during evaluation.")
    if family == "linear" and signals["strong_correlation_count"]:
        if model["id"] == "ridge_regression":
            score += 0.13
            reasons.append("Strong feature correlations favor ridge regularization.")
        elif model["id"] == "linear_regression":
            score -= 0.05
            reasons.append("Feature correlations may make an unregularized linear fit less stable.")
    if task == "classification" and model["id"] == "logistic_regression":
        if features <= 100 and rows <= 200_000:
            score += 0.10
            reasons.append("Moderate feature width and dataset size suit logistic regression.")
        if signals["high_dimensional"]:
            score -= 0.04
    if task == "clustering":
        if model["id"] == "kmeans":
            if signals["numeric_feature_ratio"] >= 0.5:
                score += 0.14
                reasons.append("Predominantly numeric prepared features suit centroid-based clustering.")
            if signals["scaling_completed"]:
                score += 0.05
                reasons.append("Workflow execution recorded feature scaling.")
            if rows < 4 or signals["high_dimensional"]:
                score -= 0.14
        elif model["id"] == "dbscan":
            if rows <= 20_000:
                score += 0.08
                reasons.append("Dataset size keeps density-based clustering bounded.")
            if signals["high_dimensional"]:
                score -= 0.18
                reasons.append("Density distance becomes less reliable in high dimensions.")
        elif model["id"] == "agglomerative_clustering":
            if rows <= 5_000:
                score += 0.10
                reasons.append("Small-to-medium dataset makes hierarchical clustering practical.")
            else:
                score -= 0.22
                reasons.append("Hierarchical clustering becomes costly for this row count.")
    if model["requires_scaling"] and not signals["scaling_completed"]:
        score -= 0.02
        reasons.append("Training pipeline will fit scaling inside each training fold when required.")
    return _bounded(score), reasons
