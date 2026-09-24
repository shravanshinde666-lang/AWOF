"""Shared, research-only helpers for fixed and adaptive experiment runners.

The runners intentionally reuse the Phase 6 trainer.  It owns the fitted
``ColumnTransformer`` and splits before fitting learned preprocessing, so both
arms of a supervised comparison have identical, leakage-safe model evaluation
rules.  The helpers here only prepare an equal non-learned input (exact
duplicate removal) and report stable metadata around that work.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split

from awof.amra.model_registry import MODEL_REGISTRY, models_for
from awof.cips import calculate_cips, detect_business_signals, min_max_normalize
from awof.explainability import clustering_importance, global_importance, local_explanation
from awof.ml import train_recommended_models
from awof.execution.executor import execute

from .benchmarks.cpu import measure_process_cpu_time
from .benchmarks.memory import measure_peak_memory


DEFAULT_RANDOM_STATE = 42
TEST_SIZE = 0.20
CORE_WORKFLOW_NODES = {"dataset_input", "profile", "output"}


def json_safe(value: Any) -> Any:
    """Recursively normalize numpy/pandas values before an experiment is stored."""

    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [json_safe(item) for item in value.tolist()]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def objective_id(configuration: dict[str, Any]) -> str:
    objective = configuration.get("business_objective")
    if isinstance(objective, dict):
        return str(objective.get("id") or "")
    return str(objective or "")


def target_column(configuration: dict[str, Any]) -> str | None:
    target = configuration.get("target")
    if isinstance(target, dict) and target.get("column"):
        return str(target["column"])
    if isinstance(target, str) and target:
        return target
    return None


def dataset_identifier(configuration: dict[str, Any]) -> str:
    return str(configuration.get("dataset_id") or "experiment-dataset")


def validate_inputs(dataframe: pd.DataFrame, configuration: dict[str, Any]) -> None:
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Experiment runners require a pandas DataFrame.")
    if dataframe.empty:
        raise ValueError("Experiment runners require at least one dataset row.")
    problem_type = configuration.get("problem_type")
    if problem_type not in {"classification", "regression", "clustering"}:
        raise ValueError("A valid classification, regression, or clustering configuration is required.")
    target = target_column(configuration)
    if problem_type in {"classification", "regression"} and (not target or target not in dataframe.columns):
        raise ValueError("A configured target column is required for supervised experiments.")


def effective_random_state(random_state: int) -> tuple[int, list[str]]:
    """Align with the fixed Phase 6 split/model seeds without claiming otherwise."""

    if random_state == DEFAULT_RANDOM_STATE:
        return DEFAULT_RANDOM_STATE, []
    return DEFAULT_RANDOM_STATE, [
        "Phase 6 model builders and the leakage-safe trainer are fixed at random_state=42; "
        f"requested random_state={random_state} was recorded but 42 was used for a fair comparison."
    ]


def remove_exact_duplicates(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply the only shared non-learned preparation step to both experiment arms.

    Exact duplicate removal is deterministic and does not fit learned values.
    Missing value imputation, encoding, and scaling remain inside the Phase 6
    fitted pipelines, where they are trained only on each training split.
    """

    duplicate_mask = dataframe.duplicated(keep="first")
    duplicate_count = int(duplicate_mask.sum())
    prepared = dataframe.loc[~duplicate_mask].copy(deep=True) if duplicate_count else dataframe.copy(deep=True)
    return prepared, {
        "input_rows": int(len(dataframe)),
        "output_rows": int(len(prepared)),
        "duplicates_removed": duplicate_count,
        "duplicate_handling_executed": bool(duplicate_count),
    }


def baseline_module_ids(dataframe: pd.DataFrame, configuration: dict[str, Any], profile: dict[str, Any] | None, duplicate_info: dict[str, Any]) -> list[str]:
    """List meaningful conventional modules that were actually applicable."""

    target = target_column(configuration)
    feature_columns = [column for column in dataframe.columns if column != target]
    feature_frame = dataframe.loc[:, feature_columns]
    identifiers = {
        item.get("column")
        for item in (profile or {}).get("column_types", [])
        if item.get("is_identifier_candidate")
    }
    ids: list[str] = []
    if duplicate_info["duplicate_handling_executed"]:
        ids.append("duplicate_handling")
    if not feature_frame.empty and bool(feature_frame.isna().any().any()):
        ids.append("missing_values")
    if any(not pd.api.types.is_numeric_dtype(feature_frame[column]) for column in feature_columns):
        ids.append("encoding")
    if any(pd.api.types.is_numeric_dtype(feature_frame[column]) for column in feature_columns):
        ids.append("scaling")
    if any(column in identifiers or dataframe[column].nunique(dropna=False) <= 1 for column in feature_columns):
        ids.append("feature_selection")
    numeric_features = [column for column in feature_columns if pd.api.types.is_numeric_dtype(feature_frame[column])]
    profile_types = {item.get("column"): item.get("broad_type") for item in (profile or {}).get("column_types", [])}
    if len(numeric_features) >= 20:
        ids.append("dimensionality_reduction")
    if any(profile_types.get(column) in {"datetime", "date", "temporal"} for column in feature_columns):
        ids.append("temporal_analysis")
    if any(profile_types.get(column) == "text" for column in feature_columns):
        ids.append("text_analysis")
    ids.append(str(configuration["problem_type"]))
    return ids


def fixed_workflow_execution(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    profile: dict[str, Any] | None,
    duplicate_info: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Execute the baseline's static, applicable preprocessing workflow once.

    This is intentionally separate from Phase 6 final model evaluation. That
    evaluation fits learned transformations on the training split in both arms;
    this Phase 5 execution measures the actual conventional workflow in the
    same way the AWOF arm measures its generated/pruned workflow.
    """

    module_ids = baseline_module_ids(dataframe, configuration, profile, duplicate_info)
    nodes = [{"id": node_id} for node_id in ["dataset_input", "profile", *module_ids, "output"]]
    workflow = {
        "pruned_workflow_id": f"fixed-baseline-{uuid4()}",
        "nodes": nodes,
        "pruned_nodes": [],
    }
    execution = execute(
        workflow,
        dataframe.copy(deep=True),
        dataset_identifier(configuration),
        target_column(configuration),
        str(configuration["problem_type"]),
        objective_id(configuration),
    )
    completed = [
        item["node_id"]
        for item in execution.get("node_results", [])
        if item.get("status") == "completed" and item.get("node_id") not in CORE_WORKFLOW_NODES
    ]
    # Phase 5 intentionally defers task nodes. Phase 6 below performs the
    # actual training/evaluation, so the named conventional task module is real.
    task = str(configuration["problem_type"])
    if task in module_ids and task not in completed:
        completed.append(task)
    return execution, completed


def all_compatible_recommendation(configuration: dict[str, Any]) -> dict[str, Any]:
    """Adapt the full compatible Phase 6 registry to its normal train API."""

    problem_type = str(configuration["problem_type"])
    candidates = models_for(problem_type)
    return {
        "dataset_id": dataset_identifier(configuration),
        "algorithm": "Fixed baseline model policy",
        "algorithm_version": "BASELINE-1.0",
        "problem_type": problem_type,
        "models": [
            {
                "model_id": model["id"],
                "label": model["label"],
                "decision": "recommended" if model["available"] else "not_selected",
                "available": bool(model["available"]),
                "score": 1.0 if model["available"] else 0.0,
                "rank": index + 1 if model["available"] else None,
                "reasons": ["Fixed baseline trains every available compatible registry model."],
            }
            for index, model in enumerate(candidates)
        ],
    }


def train_models(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    recommendation: dict[str, Any],
    profile: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, float]]:
    """Use one unmodified Phase 6 training implementation for either arm."""

    from time import perf_counter

    started = perf_counter()
    evaluation, pipelines = train_recommended_models(dataframe, configuration, recommendation, profile)
    elapsed = round((perf_counter() - started) * 1_000, 3)
    # Phase 6 returns each model's transaction timing; evaluation happens in
    # that transaction.  Keeping it explicit avoids inventing a false split.
    timings = {"model_training": elapsed, "evaluation": 0.0}
    return evaluation, pipelines, timings


def model_summary(
    recommendation: dict[str, Any], evaluation: dict[str, Any], pipelines: dict[str, Any], problem_type: str,
) -> dict[str, Any]:
    candidates = recommendation.get("models", [])
    selected_ids = [
        item["model_id"]
        for item in candidates
        if item.get("decision") == "recommended" and item.get("available", True)
    ]
    result_by_id = {item["model_id"]: item for item in evaluation.get("results", [])}
    trained_ids = [model_id for model_id in selected_ids if result_by_id.get(model_id, {}).get("status") == "completed"]
    failed_ids = [model_id for model_id in selected_ids if result_by_id.get(model_id, {}).get("status") == "failed"]
    unavailable_ids = [item["model_id"] for item in candidates if not item.get("available", True)]
    best = evaluation.get("best_model")
    best_metrics = (best or {}).get("test_metrics", {})
    return {
        "considered": len(candidates),
        "selected": len(selected_ids),
        "trained": len(trained_ids),
        "failed": len(failed_ids),
        "considered_ids": [item["model_id"] for item in candidates],
        "selected_ids": selected_ids,
        "trained_ids": trained_ids,
        "failed_ids": failed_ids,
        "unavailable_ids": unavailable_ids,
        "best_model": best,
        "best_metrics": best_metrics,
        "model_results": evaluation.get("results", []),
        "pipeline_count": len(pipelines),
        "problem_type": problem_type,
    }


def split_metadata(dataframe: pd.DataFrame, configuration: dict[str, Any], random_state: int) -> dict[str, Any]:
    """Mirror the Phase 6 supervised split exactly and expose a safe fingerprint."""

    problem_type = str(configuration["problem_type"])
    if problem_type == "clustering":
        return {
            "strategy": "not_applicable_unsupervised",
            "random_state": random_state,
            "test_size": None,
            "train_rows": int(len(dataframe)),
            "test_rows": 0,
            "test_index_fingerprint": None,
        }
    target = target_column(configuration)
    assert target is not None
    usable = dataframe.dropna(subset=[target])
    positions = np.arange(len(usable))
    labels = usable[target]
    stratify = labels if problem_type == "classification" and labels.value_counts().min() >= 2 else None
    # The Phase 6 implementation uses sklearn's train_test_split in both
    # cases; ``stratified`` tells researchers whether its optional stratify
    # argument was usable without changing the stable strategy label.
    strategy = "train_test_split"
    stratified = stratify is not None
    try:
        train_positions, test_positions = train_test_split(
            positions, test_size=TEST_SIZE, random_state=random_state, stratify=stratify,
        )
    except ValueError:
        train_positions, test_positions = train_test_split(
            positions, test_size=TEST_SIZE, random_state=random_state, stratify=None,
        )
        stratified = False
    test_source_indexes = [str(usable.index[position]) for position in sorted(test_positions.tolist())]
    fingerprint = hashlib.sha256("|".join(test_source_indexes).encode("utf-8")).hexdigest()[:16]
    return {
        "strategy": strategy,
        "stratified": stratified,
        "random_state": random_state,
        "test_size": TEST_SIZE,
        "train_rows": int(len(train_positions)),
        "test_rows": int(len(test_positions)),
        "test_index_fingerprint": fingerprint,
    }


def reproducibility_metadata(random_state: int) -> dict[str, Any]:
    return {
        "random_state": random_state,
        "test_size": TEST_SIZE,
        "split_policy": "Phase 6 deterministic train_test_split; learned preprocessing fits on train data only.",
        "model_registry_version": "AMRA-1.0",
        "acsa_version": "ACSA-1.0",
        "awga_version": "AWGA-1.0",
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
    }


def measure_entire_run(operation: Any) -> tuple[dict[str, Any], dict[str, float]]:
    """Measure one runner using tracemalloc and CPU process time together."""

    def with_memory() -> dict[str, Any]:
        return operation()

    def with_cpu() -> tuple[dict[str, Any], float]:
        return measure_process_cpu_time(with_memory)

    (result, cpu_ms), peak_memory_mb = measure_peak_memory(with_cpu)
    return result, {
        "peak_python_memory_mb": peak_memory_mb,
        "cpu_process_time_ms": cpu_ms,
    }


def supervised_risk_values(pipeline: Any, features: pd.DataFrame, configuration: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, str, str | None]:
    """Produce an explicitly qualified CIPS risk input without assuming class 1.

    This is intentionally conservative research metadata.  The CIPS package
    receives actual probability/value arrays; the returned direction warning
    remains visible to the caller whenever semantics cannot be inferred.
    """

    model = pipeline.named_steps["model"]
    predictions = np.asarray(pipeline.predict(features))
    if not hasattr(pipeline, "predict_proba"):
        return predictions, np.zeros(len(predictions)), "unavailable", "The fitted classifier has no probability output."
    probabilities = np.asarray(pipeline.predict_proba(features))
    classes = list(model.classes_)
    labels = [str(value).casefold() for value in classes]
    target_name = str(target_column(configuration) or "").casefold()
    objective = objective_id(configuration)
    risk_terms = ("churn", "risk", "default", "fraud", "cancel", "attrition", "loss")
    retention_terms = ("retain", "retention", "active", "loyal")
    positive = next((index for index, value in enumerate(labels) if value in {"1", "true", "yes", "y", "high", "risk", "churn", "default"}), None)
    if any(term in target_name for term in retention_terms):
        retained = next((index for index, value in enumerate(labels) if value in {"1", "true", "yes", "y", "retained", "active"}), None)
        if retained is not None:
            return predictions, 1.0 - probabilities[:, retained], "inverted_retention_probability", "Risk is the inverse probability of the inferred retained/active class."
        return predictions, probabilities[:, 1 if len(classes) > 1 else 0], "ambiguous", "Retention semantics are ambiguous; probability was not silently inverted."
    if any(term in target_name for term in risk_terms) or objective in {"identify_risk", "analyze_retention"}:
        index = positive if positive is not None else (1 if len(classes) > 1 else 0)
        warning = None if positive is not None else "Risk-class semantics are ambiguous; a transparent default class probability was used."
        return predictions, probabilities[:, index], "positive_risk_probability", warning
    index = positive if positive is not None else (1 if len(classes) > 1 else 0)
    return predictions, probabilities[:, index], "ambiguous", "Risk semantics are ambiguous; CIPS uses a transparent default class probability."


def optional_business_output(
    dataframe: pd.DataFrame,
    configuration: dict[str, Any],
    profile: dict[str, Any],
    pipelines: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Run compact Phase 7 algorithm outputs for the best fresh experiment model.

    Only aggregate explanation data and the top ten CIPS records are retained;
    the experiment result never embeds the uploaded dataset.
    """

    problem_type = str(configuration["problem_type"])
    best = evaluation.get("best_model") or {}
    model_id = best.get("model_id")
    if not model_id or model_id not in pipelines:
        return {"status": "unavailable", "reason": "No successfully trained best model is available.", "applicability": "not_applicable"}
    pipeline = pipelines[model_id]
    feature_names = [str(column) for column in getattr(pipeline, "feature_names_in_", [])]
    if not feature_names or any(column not in dataframe.columns for column in feature_names):
        return {"status": "unavailable", "reason": "Best-model feature columns are unavailable.", "applicability": "not_applicable"}
    features = dataframe.loc[:, feature_names].copy()
    target = target_column(configuration)
    target_values = dataframe[target] if target and target in dataframe.columns else None
    warnings: list[str] = []
    if problem_type == "clustering":
        method, importance, importance_warnings = clustering_importance(pipeline, features)
        return {
            "status": "completed",
            "applicability": "not_applicable",
            "reason": "CIPS is not applied to unsupervised clustering.",
            "explainability": {"method": method, "global_importance": importance, "warnings": importance_warnings},
            "cips": None,
        }
    method, importance, importance_warnings = global_importance(pipeline, features, target_values)
    warnings.extend(importance_warnings)
    local, local_warnings = local_explanation(pipeline, features.iloc[[0]], problem_type)
    warnings.extend(local_warnings)
    predictions = np.asarray(pipeline.predict(features))
    if problem_type == "classification":
        predictions, risk_values, risk_direction, risk_warning = supervised_risk_values(pipeline, features, configuration)
    else:
        risk_values = min_max_normalize(predictions)
        risk_direction, risk_warning = "normalized_predicted_value", "Regression priority uses normalized predicted value, not a probability."
    if risk_warning:
        warnings.append(risk_warning)
    signal_mapping, detection_warnings = detect_business_signals(dataframe, {target} if target else set())
    warnings.extend(detection_warnings)
    identifier = next(
        (item.get("column") for item in profile.get("column_types", []) if item.get("is_identifier_candidate") and item.get("column") in dataframe.columns),
        None,
    )
    records, weights, cips_warnings = calculate_cips(
        dataframe, predictions, risk_values, signal_mapping, identifier, objective_id(configuration),
    )
    warnings.extend(cips_warnings)
    counts = {level: sum(item["priority_level"] == level for item in records) for level in ("immediate", "high", "medium", "monitor")}
    return {
        "status": "completed",
        "applicability": "applicable" if signal_mapping else "partially_applicable",
        "explainability": {
            "method": method,
            "global_importance": importance,
            "local_explanation": {"row_index": 0, **local},
        },
        "cips": {
            "risk_direction": risk_direction,
            "signal_mapping": [{"signal": signal, "source_column": column} for signal, column in signal_mapping.items()],
            "effective_weights": weights,
            "summary": {
                "entities_scored": len(records),
                "immediate_count": counts["immediate"],
                "high_count": counts["high"],
                "medium_count": counts["medium"],
                "monitor_count": counts["monitor"],
            },
            "top_entities": records[:10],
        },
        "warnings": warnings,
    }


def base_result(
    *,
    pipeline_name: str,
    configuration: dict[str, Any],
    random_state: int,
    split: dict[str, Any],
    module_ids: list[str],
    pruned_module_ids: list[str],
    model_info: dict[str, Any],
    timings: dict[str, float],
    warnings: list[str],
    experiment_name: str | None,
) -> dict[str, Any]:
    """Build a result with both nested stable fields and clear research aliases."""

    best = model_info.get("best_model")
    resources = {"peak_python_memory_mb": None, "cpu_process_time_ms": None}
    result = {
        "pipeline": pipeline_name,
        "experiment_name": experiment_name,
        "dataset_id": dataset_identifier(configuration),
        "problem_type": configuration["problem_type"],
        "objective": objective_id(configuration),
        "target": target_column(configuration),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow_modules": {
            "considered": len(module_ids) + len(pruned_module_ids),
            "executed": len(module_ids),
            "selected": len(module_ids),
            "pruned": len(pruned_module_ids),
            "ids": module_ids,
            "pruned_ids": pruned_module_ids,
        },
        "models": model_info,
        "timings_ms": timings,
        "resources": resources,
        "best_model": best,
        "best_metrics": model_info.get("best_metrics", {}),
        "split": split,
        "reproducibility": reproducibility_metadata(random_state),
        "warnings": warnings,
        # Flat aliases make persisted research records easy to query and
        # directly satisfy the Phase 8 result description.
        "models_considered": model_info["considered"],
        "models_trained": model_info["trained"],
        "execution_time_ms": timings.get("overall", 0.0),
        "peak_memory_mb": None,
    }
    return result


def attach_resources(result: dict[str, Any], resources: dict[str, float]) -> dict[str, Any]:
    result["resources"] = resources
    result["peak_memory_mb"] = resources["peak_python_memory_mb"]
    return json_safe(result)
