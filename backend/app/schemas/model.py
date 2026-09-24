from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ModelRecommendation(BaseModel):
    model_id: str
    label: str
    score: float
    rank: int | None
    decision: str
    reasons: list[str]
    signals: dict[str, Any]
    estimated_complexity: str
    available: bool = True


class AMRAResult(BaseModel):
    dataset_id: str
    algorithm: str
    algorithm_version: str
    problem_type: str
    models: list[ModelRecommendation]
    incompatible_models: list[dict[str, Any]]
    signals: dict[str, Any]
    summary: dict[str, Any]


class ModelMetricSet(BaseModel):
    model_config = ConfigDict(extra="allow")


class ModelTrainingResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_id: str
    status: str
    training_duration_ms: float
    cross_validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    feature_count: int
    train_rows: int
    test_rows: int
    warnings: list[str]


class ModelEvaluationResult(BaseModel):
    dataset_id: str
    problem_type: str
    results: list[ModelTrainingResult]
    best_model: dict[str, Any] | None
    comparison: list[dict[str, Any]]
