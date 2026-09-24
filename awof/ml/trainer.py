"""Leakage-safe model training and evaluation for AMRA-selected models."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from awof.amra.model_registry import MODEL_REGISTRY

from .cross_validation import evaluate_cross_validation
from .evaluator import classification_metrics, clustering_metrics, regression_metrics
from .factories import build_estimator


RANDOM_STATE = 42
TEST_SIZE = 0.20
MODEL_METADATA = {item["id"]: item for item in MODEL_REGISTRY}


def _feature_frame(dataframe: pd.DataFrame, target_column: str | None, profile: dict[str, Any] | None) -> tuple[pd.DataFrame, pd.Series | None, dict[str, Any]]:
    data = dataframe.copy(deep=True)
    rows_removed_missing_target = 0
    if target_column:
        if target_column not in data.columns:
            raise ValueError("The configured target column is not present in the dataset.")
        rows_removed_missing_target = int(data[target_column].isna().sum())
        data = data.dropna(subset=[target_column])
        target = data[target_column].copy()
    else:
        target = None
    identifier_candidates = set()
    if profile:
        identifier_candidates = {item["column"] for item in profile.get("column_types", []) if item.get("is_identifier_candidate")}
    source_features = [column for column in data.columns if column != target_column]
    identifier_features = [
        column for column in source_features
        if column in identifier_candidates or column.lower() == "id" or column.lower().endswith("_id")
    ]
    usable = [column for column in source_features if column not in identifier_features]
    constant_features = [column for column in usable if data[column].nunique(dropna=False) <= 1]
    usable = [column for column in usable if column not in constant_features]
    if not usable:
        raise ValueError("No usable non-identifier, non-constant features remain for model training.")
    return data[usable].copy(), target, {
        "rows_removed_missing_target": rows_removed_missing_target,
        "removed_identifier_features": identifier_features,
        "removed_constant_features": constant_features,
    }


def build_preprocessor(features: pd.DataFrame, requires_scaling: bool) -> ColumnTransformer:
    numerical = list(features.select_dtypes(include=[np.number]).columns)
    categorical = [column for column in features.columns if column not in numerical]
    transformers: list[tuple[str, Pipeline, list[str]]] = []
    if numerical:
        numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
        if requires_scaling:
            numeric_steps.append(("scaler", StandardScaler()))
        transformers.append(("numeric", Pipeline(numeric_steps), numerical))
    if categorical:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def build_supervised_pipeline(features: pd.DataFrame, model_id: str) -> Pipeline:
    metadata = MODEL_METADATA[model_id]
    return Pipeline([
        ("preprocessor", build_preprocessor(features, metadata["requires_scaling"])),
        ("model", build_estimator(model_id)),
    ])


def _supervised_result(
    model_id: str,
    dataframe: pd.DataFrame,
    target_column: str,
    problem_type: str,
    profile: dict[str, Any] | None,
) -> tuple[dict[str, Any], Pipeline | None]:
    warnings: list[str] = []
    started = time.perf_counter()
    try:
        features, target, preparation = _feature_frame(dataframe, target_column, profile)
        assert target is not None
        if len(target) < 3 or target.nunique(dropna=True) < (2 if problem_type == "classification" else 1):
            raise ValueError("The dataset has too few usable target values for supervised training.")
        stratify = None
        if problem_type == "classification" and target.value_counts().min() >= 2:
            stratify = target
        try:
            x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify)
        except ValueError:
            x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=None)
            warnings.append("Stratified split was not feasible; a deterministic unstratified split was used.")
        pipeline = build_supervised_pipeline(features, model_id)
        cv_metrics, cv_warnings = evaluate_cross_validation(clone(pipeline), x_train, y_train, problem_type)
        warnings.extend(cv_warnings)
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        if problem_type == "classification":
            probabilities = pipeline.predict_proba(x_test) if hasattr(pipeline, "predict_proba") else None
            test_metrics, metric_warnings = classification_metrics(y_test, predictions, probabilities)
        else:
            test_metrics, metric_warnings = regression_metrics(y_test, predictions)
        warnings.extend(metric_warnings)
        return {
            "model_id": model_id, "status": "completed", "training_duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "cross_validation_metrics": cv_metrics, "test_metrics": test_metrics, "feature_count": int(features.shape[1]),
            "train_rows": int(len(x_train)), "test_rows": int(len(x_test)), "warnings": warnings, **preparation,
        }, pipeline
    except Exception as exc:
        return {
            "model_id": model_id, "status": "failed", "training_duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "cross_validation_metrics": {}, "test_metrics": {}, "feature_count": 0, "train_rows": 0, "test_rows": 0,
            "warnings": warnings + [f"Model training failed safely: {str(exc)}"],
        }, None


def _clustering_result(model_id: str, dataframe: pd.DataFrame, profile: dict[str, Any] | None) -> tuple[dict[str, Any], Pipeline | None]:
    started = time.perf_counter()
    try:
        features, _, preparation = _feature_frame(dataframe, None, profile)
        if len(features) < 3:
            raise ValueError("Clustering requires at least three usable rows.")
        metadata = MODEL_METADATA[model_id]
        preprocessor = build_preprocessor(features, metadata["requires_scaling"])
        transformed = preprocessor.fit_transform(features)
        evaluated_k: list[dict[str, Any]] = []
        selected_k = 2
        if model_id == "kmeans":
            for candidate_k in range(2, min(10, len(features) - 1) + 1):
                candidate = build_estimator(model_id, n_clusters=candidate_k)
                labels = candidate.fit_predict(transformed)
                score = silhouette_score(transformed, labels) if len(np.unique(labels)) > 1 else None
                evaluated_k.append({"k": candidate_k, "silhouette_score": round(float(score), 6) if score is not None else None})
            valid = [item for item in evaluated_k if item["silhouette_score"] is not None]
            if valid:
                selected_k = max(valid, key=lambda item: (item["silhouette_score"], -item["k"]))["k"]
        estimator = build_estimator(model_id, n_clusters=selected_k)
        pipeline = Pipeline([("preprocessor", build_preprocessor(features, metadata["requires_scaling"])), ("model", estimator)])
        pipeline.fit(features)
        model = pipeline.named_steps["model"]
        labels = model.labels_ if hasattr(model, "labels_") else model.predict(pipeline.named_steps["preprocessor"].transform(features))
        transformed_final = pipeline.named_steps["preprocessor"].transform(features)
        metrics, warnings = clustering_metrics(transformed_final, labels)
        extra: dict[str, Any] = {"cluster_labels": [int(label) for label in labels]}
        if model_id == "kmeans":
            extra.update({"selected_k": selected_k, "evaluated_k": evaluated_k})
        if model_id == "dbscan":
            extra.update({"eps": 0.5, "min_samples": 5})
        return {
            "model_id": model_id, "status": "completed", "training_duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "cross_validation_metrics": {"applicable": False, "reason": "Cross-validation is not applied to unsupervised clustering."},
            "test_metrics": metrics, "feature_count": int(features.shape[1]), "train_rows": int(len(features)), "test_rows": 0,
            "warnings": warnings, **preparation, **extra,
        }, pipeline
    except Exception as exc:
        return {
            "model_id": model_id, "status": "failed", "training_duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "cross_validation_metrics": {}, "test_metrics": {}, "feature_count": 0, "train_rows": 0, "test_rows": 0,
            "warnings": [f"Model training failed safely: {str(exc)}"],
        }, None


def select_best_model(results: list[dict[str, Any]], problem_type: str) -> dict[str, Any] | None:
    completed = [result for result in results if result["status"] == "completed"]
    if not completed:
        return None
    if problem_type == "classification":
        best = max(completed, key=lambda item: (item["test_metrics"].get("f1") or -1.0, item["test_metrics"].get("roc_auc") or -1.0))
        reason = "Highest F1 among successfully trained recommended models."
    elif problem_type == "regression":
        best = min(completed, key=lambda item: (item["test_metrics"].get("rmse") if item["test_metrics"].get("rmse") is not None else float("inf"), -(item["test_metrics"].get("r2") or -float("inf"))))
        reason = "Lowest RMSE among successfully trained recommended models."
    else:
        valid = [item for item in completed if item["test_metrics"].get("silhouette_score") is not None]
        if not valid:
            return None
        best = max(valid, key=lambda item: item["test_metrics"]["silhouette_score"])
        reason = "Highest valid silhouette score among successfully trained recommended models."
    return {"model_id": best["model_id"], "why_selected": reason, "test_metrics": best["test_metrics"]}


def train_recommended_models(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    recommendation: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Pipeline]]:
    problem_type = configuration["problem_type"]
    target_column = (configuration.get("target") or {}).get("column")
    selected = [item["model_id"] for item in recommendation["models"] if item["decision"] == "recommended" and item.get("available", True)]
    results: list[dict[str, Any]] = []
    pipelines: dict[str, Pipeline] = {}
    for model_id in selected:
        if problem_type in {"classification", "regression"}:
            if not target_column:
                result, pipeline = ({"model_id": model_id, "status": "failed", "training_duration_ms": 0.0, "cross_validation_metrics": {}, "test_metrics": {}, "feature_count": 0, "train_rows": 0, "test_rows": 0, "warnings": ["A target column is required for supervised training."]}, None)
            else:
                result, pipeline = _supervised_result(model_id, dataframe, target_column, problem_type, profile)
        else:
            result, pipeline = _clustering_result(model_id, dataframe, profile)
        results.append(result)
        if pipeline is not None:
            pipelines[model_id] = pipeline
    best_model = select_best_model(results, problem_type)
    comparison = [{"model_id": item["model_id"], "status": item["status"], "metrics": item["test_metrics"]} for item in results]
    return {"problem_type": problem_type, "results": results, "best_model": best_model, "comparison": comparison}, pipelines
