from typing import Any
from pydantic import BaseModel

class CapabilityResult(BaseModel):
    id: str
    label: str
    description: str
    category: str
    score: float
    decision: str
    reasons: list[str]
    signals: dict[str, Any]

class ACSASummary(BaseModel):
    total_capabilities: int
    run_count: int
    optional_count: int
    skip_count: int

class ACSAResult(BaseModel):
    dataset_id: str
    algorithm: str
    algorithm_version: str
    generated_at: str
    business_objective: dict[str, str]
    problem_type: str
    thresholds: dict[str, float]
    capabilities: list[CapabilityResult]
    summary: ACSASummary
