from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExperimentRequest(BaseModel):
    runs: int = Field(default=3, ge=1, le=10)
    experiment_name: str | None = Field(default=None, max_length=120)


class BenchmarkMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")


class PipelineExperimentResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    pipeline: str
    problem_type: str
    workflow_modules: dict[str, Any]
    models: dict[str, Any]
    timings_ms: dict[str, float]
    resources: dict[str, float]
    best_model: dict[str, Any] | None = None
    best_metrics: dict[str, Any] = {}
    split: dict[str, Any] = {}
    warnings: list[str] = []


class ExperimentComparison(BaseModel):
    model_config = ConfigDict(extra="allow")

    module_reduction_count: float
    module_reduction_percentage: float | None = None
    model_reduction_count: float
    model_reduction_percentage: float | None = None
    execution_time_difference_ms: float
    execution_time_reduction_percentage: float | None = None
    memory_difference_mb: float
    memory_reduction_percentage: float | None = None
    performance: dict[str, Any]
    factual_statements: list[str]
    warnings: list[str] = []


class ResearchExperimentResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    experiment_id: str
    dataset_id: str
    dataset_name: str
    problem_type: str
    objective: str
    target: str | None = None
    timestamp: str
    metadata: dict[str, Any]
    baseline: PipelineExperimentResult
    awof: PipelineExperimentResult
    comparison: ExperimentComparison
    warnings: list[str] = []


class ExperimentSummary(BaseModel):
    experiment_id: str
    dataset_id: str
    dataset_name: str
    problem_type: str
    objective: str
    timestamp: str
    runs: int = Field(default=1, ge=1, le=10)
