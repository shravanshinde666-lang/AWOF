from pydantic import BaseModel


class BusinessObjective(BaseModel):
    id: str
    label: str
    description: str
    target_requirement: str
    supported_problem_types: list[str]


class TargetCandidate(BaseModel):
    column: str
    detected_type: str
    unique_count: int
    missing_percentage: float
    identifier_candidate: bool
    constant: bool
    suggested_problem_type: str
    target_suitability: str
    reasons: list[str]
    warnings: list[str]


class ConfigurationRequest(BaseModel):
    business_objective: str
    target_column: str | None = None


class TargetSelection(BaseModel):
    column: str
    detected_type: str
    suitability: str


class AnalysisConfiguration(BaseModel):
    dataset_id: str
    business_objective: dict[str, str]
    target: TargetSelection | None
    problem_type: str
    valid: bool
    warnings: list[str]
    errors: list[str]


class ObjectivesResponse(BaseModel):
    success: bool = True
    objectives: list[BusinessObjective]


class TargetCandidatesResponse(BaseModel):
    success: bool = True
    dataset_id: str
    candidates: list[TargetCandidate]


class ConfigurationResponse(BaseModel):
    success: bool = True
    configuration: AnalysisConfiguration
