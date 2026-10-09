"""Dataset-agnostic visualization aggregates derived from existing data/configuration."""
from __future__ import annotations
from typing import Any
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
from .configuration_service import get_saved_configuration
from .dataset_service import get_profile, load_dataset_dataframe


def _feature_target_ranking(frame: pd.DataFrame, profile: dict[str, Any], target: str | None, problem_type: str | None) -> dict[str, Any]:
    """Calculate bounded, non-linear feature--target relevance for numeric features."""
    if not target or target not in frame or problem_type not in {"classification", "regression"}:
        return {"method": "mutual_information", "items": [], "message": "Requires a configured supervised target."}
    identifiers = {item["column"] for item in profile["column_types"] if item.get("is_identifier_candidate")}
    features = [item["column"] for item in profile["column_types"] if item.get("broad_type") == "numerical" and item["column"] != target and item["column"] not in identifiers]
    if not features:
        return {"method": "mutual_information", "items": [], "message": "No eligible numerical features are available."}
    data = frame[features + [target]].dropna(subset=[target]).copy()
    if len(data) < 5 or data[target].nunique(dropna=True) < 2:
        return {"method": "mutual_information", "items": [], "message": "Insufficient non-missing target variation."}
    feature_frame = data[features].apply(pd.to_numeric, errors="coerce")
    feature_frame = feature_frame.fillna(feature_frame.median()).fillna(0.0)
    try:
        if problem_type == "classification":
            encoded_target = LabelEncoder().fit_transform(data[target].astype(str))
            scores = mutual_info_classif(feature_frame, encoded_target, random_state=42)
        else:
            numeric_target = pd.to_numeric(data[target], errors="coerce")
            valid = numeric_target.notna()
            if int(valid.sum()) < 5:
                return {"method": "mutual_information", "items": [], "message": "The regression target must be numeric."}
            scores = mutual_info_regression(feature_frame.loc[valid], numeric_target.loc[valid], random_state=42)
    except (TypeError, ValueError):
        return {"method": "mutual_information", "items": [], "message": "Feature--target ranking could not be calculated for this dataset."}
    items = sorted(
        [{"feature": feature, "score": round(float(score), 6)} for feature, score in zip(features, scores)],
        key=lambda item: item["score"], reverse=True,
    )[:20]
    return {"method": "mutual_information", "items": items, "message": None}

def get_visual_insights(dataset_id: str) -> dict[str, Any]:
    frame = load_dataset_dataframe(dataset_id)
    profile = get_profile(dataset_id)
    try:
        configuration = get_saved_configuration(dataset_id)
    except Exception:
        configuration = None
    target = ((configuration or {}).get("target") or {}).get("column")
    result: dict[str, Any] = {"target": target, "problem_type": (configuration or {}).get("problem_type"), "target_distribution": [], "positive_class": None, "category_target_rates": [], "correlation_matrix": None, "feature_target_ranking": {"method": "mutual_information", "items": [], "message": "Requires a configured supervised target."}}
    if target and target in frame.columns:
        counts = frame[target].dropna().value_counts()
        result["target_distribution"] = [{"label": str(label), "count": int(count), "percentage": float(count / counts.sum() * 100)} for label, count in counts.items()]
        if len(counts) == 2 and result["problem_type"] == "classification":
            positive = next((value for value in counts.index if str(value).strip().casefold() in {"yes", "true", "churn", "positive", "1"}), counts.index[-1])
            result["positive_class"] = str(positive)
            identifiers = {item["column"] for item in profile["column_types"] if item.get("is_identifier_candidate")}
            candidates = [item["column"] for item in profile["column_types"] if item["column"] != target and item["column"] not in identifiers and item.get("broad_type") in {"categorical", "boolean"} and 2 <= item.get("unique_count", 0) <= 12]
            binary_target = frame[target].eq(positive)
            for column in candidates[:6]:
                grouped = pd.DataFrame({"category": frame[column], "positive": binary_target}).dropna().groupby("category", observed=True)["positive"].agg(["mean", "size"]).reset_index()
                result["category_target_rates"].append({"feature": column, "values": [{"category": str(row.category), "rate": round(float(row.mean) * 100, 4), "count": int(row.size)} for row in grouped.itertuples(index=False)]})
    numeric = [item["column"] for item in profile["column_types"] if item.get("broad_type") == "numerical" and not item.get("is_identifier_candidate")]
    if len(numeric) >= 2:
        corr = frame[numeric].apply(pd.to_numeric, errors="coerce").corr()
        result["correlation_matrix"] = {"columns": numeric, "values": [[None if pd.isna(value) else round(float(value), 6) for value in row] for row in corr.to_numpy()]}
    result["feature_target_ranking"] = _feature_target_ranking(frame, profile, target, result["problem_type"])
    return result
