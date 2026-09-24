from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ObjectiveDefinition:
    id: str
    label: str
    description: str
    target_requirement: str
    supported_problem_types: tuple[str, ...]


OBJECTIVES: dict[str, ObjectiveDefinition] = {
    "predict_behavior": ObjectiveDefinition(
        "predict_behavior", "Predict Behavior",
        "Use historical features to predict a known outcome.",
        "required", ("classification", "regression"),
    ),
    "segment_customers": ObjectiveDefinition(
        "segment_customers", "Segment Customers",
        "Discover natural customer or data groups without a predefined label.",
        "none", ("clustering",),
    ),
    "identify_risk": ObjectiveDefinition(
        "identify_risk", "Identify Risk",
        "Predict or prioritize risk outcomes.",
        "required", ("classification", "regression"),
    ),
    "analyze_retention": ObjectiveDefinition(
        "analyze_retention", "Analyze Retention",
        "Analyze or predict retention, renewal, churn, or disengagement.",
        "required", ("classification",),
    ),
    "optimize_revenue": ObjectiveDefinition(
        "optimize_revenue", "Optimize Revenue",
        "Analyze customer value or predict a revenue-related outcome.",
        "optional", ("regression", "business_analysis"),
    ),
}


def get_objective(objective_id: str) -> ObjectiveDefinition | None:
    return OBJECTIVES.get(objective_id)


def list_objectives() -> list[dict[str, object]]:
    return [asdict(objective) for objective in OBJECTIVES.values()]
