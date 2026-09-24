"""Business-priority orchestration using predictions from a fitted best model."""

from __future__ import annotations

from typing import Any

import numpy as np

from awof.cips import BASE_WEIGHTS, calculate_cips, detect_business_signals

from ..database import repository
from .explainability_service import ExplainabilityNotFoundError, ExplainabilityPrerequisiteError, get_explainability, load_best_model_context
from .model_service import ModelResultNotFoundError, get_prediction_records



class BusinessPrerequisiteError(Exception):
    pass


class BusinessResultNotFoundError(Exception):
    pass


def _identifier_column(profile: dict[str, Any], dataframe: Any) -> str | None:
    return next((item["column"] for item in profile.get("column_types", []) if item.get("is_identifier_candidate") and item.get("column") in dataframe.columns), None)


def _classification_risk(pipeline: Any, features: Any, configuration: dict[str, Any], records: list[dict[str, Any]] | None = None) -> tuple[np.ndarray, np.ndarray, str, str | None]:
    model = pipeline.named_steps["model"]
    predictions = np.asarray([record["prediction"] for record in records]) if records else np.asarray(pipeline.predict(features))
    if not hasattr(pipeline, "predict_proba"):
        return predictions, np.zeros(len(predictions)), "unavailable", "The selected classifier does not provide probabilities, so CIPS is only partially applicable."
    if records and all("probabilities_by_class" in record for record in records):
        probabilities = np.asarray([[record["probabilities_by_class"].get(str(label), 0.0) for label in model.classes_] for record in records])
    else:
        probabilities = np.asarray(pipeline.predict_proba(features))
    classes = list(model.classes_)
    labels = [str(value).casefold() for value in classes]
    target_name = str((configuration.get("target") or {}).get("column") or "").casefold()
    objective = configuration["business_objective"]["id"]
    risk_terms = ("churn", "risk", "default", "fraud", "cancel", "attrition", "loss")
    retention_terms = ("retain", "retention", "active", "loyal")
    likely_positive = next((index for index, label in enumerate(labels) if label in {"1", "true", "yes", "y", "high", "risk", "churn", "default"}), None)
    if any(term in target_name for term in retention_terms):
        retained_index = next((index for index, label in enumerate(labels) if label in {"1", "true", "yes", "y", "retained", "active"}), None)
        if retained_index is not None:
            return predictions, 1.0 - probabilities[:, retained_index], "inverted_retention_probability", "Risk is the inverse probability of the likely retained/active class."
        return predictions, probabilities[:, 1 if len(classes) > 1 else 0], "ambiguous", "Retention semantics are ambiguous; the displayed class probability was not silently inverted."
    if any(term in target_name for term in risk_terms) or objective in {"identify_risk", "analyze_retention"}:
        selected = likely_positive if likely_positive is not None else (1 if len(classes) > 1 else 0)
        warning = None if likely_positive is not None else "Risk-class semantics are ambiguous; the second model class probability was used transparently."
        return predictions, probabilities[:, selected], "positive_risk_probability", warning
    selected = likely_positive if likely_positive is not None else (1 if len(classes) > 1 else 0)
    return predictions, probabilities[:, selected], "ambiguous", "Risk semantics are ambiguous; CIPS uses a transparent default class probability."


def _not_applicable(dataset_id: str, problem_type: str, reason: str) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id, "model_id": None, "problem_type": problem_type, "applicability": "not_applicable",
        "risk_direction": None, "risk_direction_warning": reason, "signal_mapping": [], "effective_weights": {},
        "summary": {"entities_scored": 0, "immediate_count": 0, "high_count": 0, "medium_count": 0, "monitor_count": 0, "signals_used": [], "signals_missing": list(BASE_WEIGHTS)},
        "items": [], "warnings": [reason],
    }


def _format(dataset_id: str, stored: dict[str, Any], limit: int) -> dict[str, Any]:
    return {**stored["result"], "items": stored["items"][:limit]}


def generate_business_priority(dataset_id: str, limit: int = 100) -> dict[str, Any]:
    try:
        get_explainability(dataset_id)
        pipeline, features, source, configuration, context = load_best_model_context(dataset_id)
        prediction_records = get_prediction_records(dataset_id)
    except (ExplainabilityNotFoundError, ExplainabilityPrerequisiteError, ModelResultNotFoundError) as exc:
        raise BusinessPrerequisiteError("Explainability and a serialized best model must be generated before business prioritization.") from exc
    problem_type = configuration["problem_type"]
    if problem_type == "clustering":
        result = _not_applicable(dataset_id, problem_type, "Business prioritization is not applicable to an unsupervised clustering workflow.")
        repository.save_stage(dataset_id, "business_priority", {"result": result, "items": []})
        return result
    predictions = np.asarray([record["prediction"] for record in prediction_records])
    warnings: list[str] = []
    if problem_type == "classification":
        predictions, risk_values, risk_direction, direction_warning = _classification_risk(pipeline, features, configuration, prediction_records)
    else:
        from awof.cips import min_max_normalize
        risk_values, risk_direction, direction_warning = min_max_normalize(predictions), "normalized_predicted_value", "Regression priority uses normalized predicted value rather than a probability."
    if direction_warning:
        warnings.append(direction_warning)
    target_column = (configuration.get("target") or {}).get("column")
    signal_mapping, detection_warnings = detect_business_signals(source, {target_column} if target_column else set())
    warnings.extend(detection_warnings)
    records, weights, calculation_warnings = calculate_cips(source, predictions, risk_values, signal_mapping, _identifier_column(context["profile"], source), configuration["business_objective"]["id"])
    warnings.extend(calculation_warnings)
    counts = {level: sum(item["priority_level"] == level for item in records) for level in ("immediate", "high", "medium", "monitor")}
    applicability = "applicable" if signal_mapping else "partially_applicable"
    result = {
        "dataset_id": dataset_id, "model_id": context["best"]["model_id"], "problem_type": problem_type,
        "applicability": applicability, "risk_direction": risk_direction, "risk_direction_warning": direction_warning,
        "signal_mapping": [{"signal": signal, "source_column": column} for signal, column in signal_mapping.items()],
        "effective_weights": weights,
        "summary": {"entities_scored": len(records), "immediate_count": counts["immediate"], "high_count": counts["high"], "medium_count": counts["medium"], "monitor_count": counts["monitor"], "signals_used": list(weights), "signals_missing": [signal for signal in BASE_WEIGHTS if signal not in weights]},
        "items": [], "warnings": warnings,
    }
    stored = {"result": result, "items": records}
    repository.save_stage(dataset_id, "business_priority", stored)
    return _format(dataset_id, stored, limit)


def get_business_priority(dataset_id: str, limit: int = 100) -> dict[str, Any]:
    try:
        return _format(dataset_id, repository.get_stage(dataset_id, "business_priority"), limit)
    except repository.PersistenceNotFoundError as exc:
        raise BusinessResultNotFoundError("Business priorities have not been generated.") from exc
