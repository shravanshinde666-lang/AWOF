from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    rank: int
    direction: str | None = None
    original_feature: str | None = None


class FeatureContribution(FeatureImportanceItem):
    contribution: float


class LocalExplanation(BaseModel):
    row_index: int
    entity_id: str | None = None
    prediction: Any
    prediction_probability: float | None = None
    predicted_value: float | str | None = None
    probabilities_by_class: dict[str, float] = {}
    baseline_value: float | None = None
    method: str
    feature_contributions: list[FeatureContribution]
    top_positive_factors: list[FeatureContribution]
    top_negative_factors: list[FeatureContribution]
    warnings: list[str] = []


class ExplainabilityResult(BaseModel):
    dataset_id: str
    model_id: str
    problem_type: str
    explanation_method: str
    model_artifact: str
    generated_at: str
    global_importance: list[FeatureImportanceItem]
    local_explanations: list[LocalExplanation]
    warnings: list[str] = []
