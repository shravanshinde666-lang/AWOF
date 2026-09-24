"""Application service for fitted-pipeline explainability."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from awof.explainability import clustering_importance, global_importance, local_explanation, shap_available

from ..config.settings import BACKEND_DIR
from ..database import repository
from .configuration_service import get_saved_configuration
from .dataset_service import get_profile, load_dataset_dataframe
from .model_service import ModelResultNotFoundError, get_evaluation



class ExplainabilityPrerequisiteError(Exception):
    pass


class ExplainabilityNotFoundError(Exception):
    pass


class InvalidExplanationRowError(Exception):
    pass


def _artifact_path(filename: str) -> Path:
    safe_filename = Path(filename).name
    if safe_filename != filename or not safe_filename.endswith(".joblib"):
        raise ExplainabilityPrerequisiteError("The stored model artifact reference is invalid.")
    return BACKEND_DIR.parent / "storage" / "models" / safe_filename


def load_best_model_context(dataset_id: str) -> tuple[Any, pd.DataFrame, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load the already-fitted best pipeline and only its required raw columns."""
    try:
        profile = get_profile(dataset_id)
        configuration = get_saved_configuration(dataset_id)
        evaluation = get_evaluation(dataset_id)
        best = evaluation.get("best_model")
        if not best or not best.get("artifact_filename"):
            raise ExplainabilityPrerequisiteError("A successfully serialized best model is required before explanation.")
        path = _artifact_path(best["artifact_filename"])
        if not path.is_file():
            raise ExplainabilityPrerequisiteError("The best model artifact is unavailable.")
        pipeline = joblib.load(path)
        dataframe = load_dataset_dataframe(dataset_id)
    except (ModelResultNotFoundError, KeyError) as exc:
        raise ExplainabilityPrerequisiteError("Profile, configuration, model evaluation, and a best model artifact are required before explanation.") from exc
    expected = [str(column) for column in getattr(pipeline, "feature_names_in_", [])]
    if not expected or any(column not in dataframe.columns for column in expected):
        raise ExplainabilityPrerequisiteError("The uploaded dataset no longer contains the features required by the best model.")
    return pipeline, dataframe.loc[:, expected].copy(), dataframe, configuration, {"best": best, "profile": profile, "evaluation": evaluation}


def _entity_identifier(profile: dict[str, Any], dataframe: pd.DataFrame, row_index: int) -> str | None:
    identifier = next((item["column"] for item in profile.get("column_types", []) if item.get("is_identifier_candidate") and item.get("column") in dataframe.columns), None)
    if identifier is None:
        return None
    value = dataframe.iloc[row_index][identifier]
    return None if pd.isna(value) else str(value)


def _local(dataset_id: str, row_index: int, pipeline: Any, features: pd.DataFrame, source: pd.DataFrame, configuration: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    if row_index < 0 or row_index >= len(features):
        raise InvalidExplanationRowError("Row index is outside the uploaded dataset.")
    explanation, warnings = local_explanation(pipeline, features.iloc[[row_index]], configuration["problem_type"])
    return {"row_index": row_index, "entity_id": _entity_identifier(profile, source, row_index), **explanation, "warnings": warnings}


def generate_explainability(dataset_id: str) -> dict[str, Any]:
    pipeline, features, source, configuration, context = load_best_model_context(dataset_id)
    profile = context["profile"]
    warnings: list[str] = []
    if shap_available():
        warnings.append("SHAP is installed but this Phase 7 build uses the model-native deterministic method selected below.")
    else:
        warnings.append("SHAP is not installed; the reported fallback method is used transparently.")
    target_column = (configuration.get("target") or {}).get("column")
    target = source[target_column] if target_column and target_column in source.columns else None
    if configuration["problem_type"] == "clustering":
        method, importance, method_warnings = clustering_importance(pipeline, features)
        locals_: list[dict[str, Any]] = []
        warnings.append("Clustering uses centroid/profile differences; supervised local prediction explanations are not applicable.")
    else:
        method, importance, method_warnings = global_importance(pipeline, features, target)
        locals_ = [_local(dataset_id, index, pipeline, features, source, configuration, profile) for index in range(min(5, len(features)))]
    warnings.extend(method_warnings)
    result = {
        "dataset_id": dataset_id,
        "model_id": context["best"]["model_id"],
        "problem_type": configuration["problem_type"],
        "explanation_method": method,
        "model_artifact": context["best"]["artifact_filename"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "global_importance": importance,
        "local_explanations": locals_,
        "warnings": warnings,
    }
    repository.save_stage(dataset_id, "explainability", result)
    return result


def get_explainability(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "explainability")
    except repository.PersistenceNotFoundError as exc:
        raise ExplainabilityNotFoundError("Explainability has not been generated for this dataset.") from exc


def get_local_explanation(dataset_id: str, row_index: int) -> dict[str, Any]:
    get_explainability(dataset_id)
    pipeline, features, source, configuration, context = load_best_model_context(dataset_id)
    return _local(dataset_id, row_index, pipeline, features, source, configuration, context["profile"])
