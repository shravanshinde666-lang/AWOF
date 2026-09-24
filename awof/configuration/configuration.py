from typing import Any

from .objectives import get_objective
from .target_analyzer import analyze_target_candidates


def build_configuration(
    dataset_id: str,
    business_objective: str,
    target_column: str | None,
    profile: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    objective = get_objective(business_objective)
    if objective is None:
        return {
            "dataset_id": dataset_id, "business_objective": None, "target": None,
            "problem_type": "unknown", "valid": False, "warnings": [],
            "errors": ["Business objective is not supported."],
        }

    if objective.target_requirement == "none":
        if target_column:
            warnings.append("Target selection is not used for customer segmentation.")
        return {
            "dataset_id": dataset_id,
            "business_objective": {"id": objective.id, "label": objective.label},
            "target": None, "problem_type": "clustering", "valid": True,
            "warnings": warnings, "errors": [],
        }

    if not target_column:
        if objective.target_requirement == "optional":
            return {
                "dataset_id": dataset_id,
                "business_objective": {"id": objective.id, "label": objective.label},
                "target": None, "problem_type": "business_analysis", "valid": True,
                "warnings": ["No target was selected; this will remain business analysis rather than prediction."],
                "errors": [],
            }
        return {
            "dataset_id": dataset_id,
            "business_objective": {"id": objective.id, "label": objective.label},
            "target": None, "problem_type": "unknown", "valid": False,
            "warnings": [], "errors": ["This business objective requires a target column."],
        }

    candidate = next(
        (item for item in analyze_target_candidates(profile) if item["column"] == target_column),
        None,
    )
    if candidate is None:
        errors.append("Selected target column does not exist in this dataset.")
    elif candidate["constant"] or candidate["missing_percentage"] >= 100:
        errors.append("Selected target column is not usable because it is constant or completely missing.")

    if candidate:
        warnings.extend(candidate["warnings"])
        if candidate["identifier_candidate"]:
            warnings.append("Selected target appears identifier-like and may not be meaningful.")
        problem_type = candidate["suggested_problem_type"]
        if problem_type == "unknown":
            warnings.append("Target type is ambiguous; review this configuration before future analysis.")
        elif problem_type not in objective.supported_problem_types:
            warnings.append(
                f"{objective.label} typically uses {', '.join(objective.supported_problem_types)}, "
                f"but this target suggests {problem_type}."
            )
    else:
        problem_type = "unknown"

    return {
        "dataset_id": dataset_id,
        "business_objective": {"id": objective.id, "label": objective.label},
        "target": None if candidate is None else {
            "column": candidate["column"],
            "detected_type": candidate["detected_type"],
            "suitability": candidate["target_suitability"],
        },
        "problem_type": problem_type,
        "valid": not errors,
        "warnings": warnings,
        "errors": errors,
    }
