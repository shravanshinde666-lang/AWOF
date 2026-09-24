"""Application orchestration for AMRA and the ML engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from awof.amra import AMRARecommender
from awof.ml import train_recommended_models

from ..config.settings import BACKEND_DIR
from ..database import repository
from .capability_service import CapabilityResultNotFoundError, get_capabilities
from .configuration_service import ConfigurationNotFoundError, get_saved_configuration
from .dataset_service import DatasetNotFoundError, load_dataset_dataframe, get_profile
from .execution_service import get_execution
from .workflow_service import WorkflowNotFoundError, get_workflow



class ModelPrerequisiteError(Exception):
    pass


class ModelResultNotFoundError(Exception):
    pass


def _resolve_inputs(dataset_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Any]:
    try:
        profile = get_profile(dataset_id)
        configuration = get_saved_configuration(dataset_id)
        get_capabilities(dataset_id)
        get_workflow(dataset_id)
        execution = get_execution(dataset_id)
        dataframe = load_dataset_dataframe(dataset_id)
    except (CapabilityResultNotFoundError, ConfigurationNotFoundError, DatasetNotFoundError, KeyError, WorkflowNotFoundError) as exc:
        # Existing services intentionally use distinct in-memory exception types.
        # The API exposes one clear prerequisite message rather than their internals.
        raise ModelPrerequisiteError(
            "Profile, configuration, ACSA, workflow generation, pruning, and execution must be completed before model operations."
        ) from exc
    return profile, configuration, execution, dataframe


def recommend_models(dataset_id: str) -> dict[str, Any]:
    profile, configuration, execution, dataframe = _resolve_inputs(dataset_id)
    result = AMRARecommender().recommend(profile, configuration, execution, dataframe)
    repository.save_stage(dataset_id, "model_recommendations", result)
    return result


def get_recommendations(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "model_recommendations")
    except repository.PersistenceNotFoundError as exc:
        raise ModelResultNotFoundError("Model recommendations have not been generated.") from exc


def _model_directory() -> Path:
    directory = BACKEND_DIR.parent / "storage" / "models"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _json_value(value: Any) -> Any:
    return value.item() if isinstance(value, np.generic) else value


def _store_prediction_records(dataset_id: str, pipeline: Any, dataframe: Any) -> None:
    """Retain only compact row/prediction mapping, never the user dataset itself."""
    features = dataframe.loc[:, list(pipeline.feature_names_in_)]
    model = pipeline.named_steps["model"]
    try:
        predictions = pipeline.predict(features)
    except AttributeError:
        predictions = getattr(model, "labels_", [])
    probabilities = pipeline.predict_proba(features) if hasattr(pipeline, "predict_proba") else None
    classes = [_json_value(value) for value in getattr(model, "classes_", [])]
    records: list[dict[str, Any]] = []
    for row_index, prediction in enumerate(predictions):
        record: dict[str, Any] = {"row_index": row_index, "prediction": _json_value(prediction)}
        if probabilities is not None:
            record["probabilities_by_class"] = {
                str(label): round(float(probability), 8)
                for label, probability in zip(classes, probabilities[row_index])
            }
        records.append(record)
    repository.save_stage(dataset_id, "prediction_records", {"records": records})


def train_models(dataset_id: str) -> dict[str, Any]:
    recommendation = get_recommendations(dataset_id)
    profile, configuration, _, dataframe = _resolve_inputs(dataset_id)
    evaluation, pipelines = train_recommended_models(dataframe, configuration, recommendation, profile)
    evaluation["dataset_id"] = dataset_id
    scores = {item["model_id"]: item["score"] for item in recommendation["models"]}
    for result in evaluation["results"]:
        result["amra_score"] = scores.get(result["model_id"])
    best = evaluation.get("best_model")
    if best and best["model_id"] in pipelines:
        filename = f"{dataset_id}_{best['model_id']}.joblib"
        joblib.dump(pipelines[best["model_id"]], _model_directory() / filename)
        best["artifact_filename"] = filename
        best["amra_score"] = scores.get(best["model_id"])
        for result in evaluation["results"]:
            if result["model_id"] == best["model_id"]:
                result["artifact_filename"] = filename
                break
        _store_prediction_records(dataset_id, pipelines[best["model_id"]], dataframe)
    repository.save_stage(dataset_id, "model_evaluation", evaluation)
    return evaluation


def get_evaluation(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "model_evaluation")
    except repository.PersistenceNotFoundError as exc:
        raise ModelResultNotFoundError("Recommended models have not been trained.") from exc


def get_prediction_records(dataset_id: str) -> list[dict[str, Any]]:
    try:
        return repository.get_stage(dataset_id, "prediction_records")["records"]
    except (repository.PersistenceNotFoundError, KeyError) as exc:
        raise ModelResultNotFoundError("Model predictions have not been retained for this dataset.") from exc
