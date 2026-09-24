from typing import Any


SUITABILITY_ORDER = {"high": 0, "medium": 1, "low": 2, "unsuitable": 3}
CLASSIFICATION_TYPES = {"boolean", "binary", "nominal", "ordinal_candidate"}


def _suggest_problem_type(type_info: dict[str, Any]) -> str:
    detected_type = type_info.get("detected_type", "unknown")
    unique_count = int(type_info.get("unique_count", 0))
    if detected_type in CLASSIFICATION_TYPES:
        return "classification"
    if detected_type == "integer":
        return "classification" if unique_count <= 20 else "regression"
    if detected_type == "continuous_numeric":
        return "regression"
    return "unknown"


def analyze_target_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    columns = profile.get("columns", {})

    for type_info in profile.get("column_types", []):
        column = str(type_info["column"])
        details = columns.get(column, {})
        missing = details.get("missing", {})
        missing_percentage = float(missing.get("missing_percentage", 0.0))
        detected_type = str(type_info.get("detected_type", "unknown"))
        is_constant = bool(type_info.get("is_constant", False))
        is_identifier = bool(type_info.get("is_identifier_candidate", False))
        unique_count = int(type_info.get("unique_count", 0))
        reasons: list[str] = []
        warnings: list[str] = []
        suggested_problem_type = _suggest_problem_type(type_info)
        suitability = "high" if suggested_problem_type != "unknown" else "medium"

        if missing_percentage >= 100:
            suitability = "unsuitable"
            reasons.append("Column contains only missing values.")
        elif is_constant:
            suitability = "unsuitable"
            reasons.append("Column is constant and cannot define an outcome.")
        elif is_identifier:
            suitability = "unsuitable"
            reasons.append("Column appears to be an identifier rather than an outcome.")
        else:
            if detected_type in CLASSIFICATION_TYPES:
                reasons.append("Categorical or binary attribute supports classification.")
            elif suggested_problem_type == "regression":
                reasons.append("Numerical variation supports regression.")
            elif detected_type == "text":
                suitability = "low"
                reasons.append("Free-form text is not a reliable supervised target by default.")

            if missing_percentage >= 90:
                suitability = "low"
                warnings.append("Column is almost completely missing.")
            elif missing_percentage >= 30:
                warnings.append("Column has substantial missing values.")

            if type_info.get("cardinality") in {"high", "near_unique"}:
                if detected_type in CLASSIFICATION_TYPES:
                    suitability = "low"
                    warnings.append("High cardinality may make classification impractical.")
                else:
                    warnings.append("High cardinality should be reviewed before using this target.")

            if suggested_problem_type == "unknown":
                warnings.append("No reliable technical problem type could be inferred.")

        candidates.append({
            "column": column,
            "detected_type": detected_type,
            "unique_count": unique_count,
            "missing_percentage": missing_percentage,
            "identifier_candidate": is_identifier,
            "constant": is_constant,
            "suggested_problem_type": suggested_problem_type,
            "target_suitability": suitability,
            "reasons": reasons,
            "warnings": warnings,
        })

    return sorted(candidates, key=lambda item: (SUITABILITY_ORDER[item["target_suitability"]], item["column"].lower()))
