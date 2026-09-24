from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class BusinessSignal(BaseModel):
    signal: str
    source_column: str


class CIPSResultItem(BaseModel):
    row_index: int
    entity_id: str | None = None
    prediction: Any
    risk_probability: float | None = None
    cips_score: float
    priority_level: str
    signals: dict[str, float]
    effective_weights: dict[str, float]
    top_reasons: list[str]
    recommended_action: str


class CIPSSummary(BaseModel):
    entities_scored: int
    immediate_count: int
    high_count: int
    medium_count: int
    monitor_count: int
    signals_used: list[str]
    signals_missing: list[str]


class BusinessIntelligenceResult(BaseModel):
    dataset_id: str
    model_id: str | None = None
    problem_type: str
    applicability: str
    risk_direction: str | None = None
    risk_direction_warning: str | None = None
    signal_mapping: list[BusinessSignal]
    effective_weights: dict[str, float]
    summary: CIPSSummary
    items: list[CIPSResultItem]
    warnings: list[str]
