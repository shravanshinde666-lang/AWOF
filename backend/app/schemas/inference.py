from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class FeatureMetaSchema(BaseModel):
    name: str
    type: str  # "numeric" | "integer" | "categorical"
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    step: float | None = None
    default_value: Any = None
    categories: list[str] | None = None


class SampleRowItem(BaseModel):
    row_index: int
    label: str
    values: dict[str, Any]


class InferenceSchemaResponse(BaseModel):
    dataset_id: str
    model_id: str
    problem_type: str
    target_column: str | None = None
    target_classes: list[str] = []
    features: list[FeatureMetaSchema]
    sample_rows: list[SampleRowItem] = []


class PredictionRequest(BaseModel):
    features: dict[str, Any]
    target_class: Any | None = None


class LocalFactorItem(BaseModel):
    feature: str
    importance: float
    contribution: float | None = None
    direction: str | None = None
    original_feature: str | None = None


class CounterfactualItem(BaseModel):
    feature: str
    feature_type: str
    current_value: Any
    proposed_value: Any
    delta: str
    projected_prediction: Any
    projected_confidence: float | None = None
    action_text: str
    impact: str


class PredictionResponse(BaseModel):
    prediction: Any
    prediction_label: str
    probabilities: dict[str, float] = {}
    confidence: float | None = None
    local_factors: list[LocalFactorItem] = []
    counterfactuals: list[CounterfactualItem] = []
