"""Dataset-agnostic visualization aggregates derived from existing data/configuration."""
from __future__ import annotations
from typing import Any
import pandas as pd
from .configuration_service import get_saved_configuration
from .dataset_service import get_profile, load_dataset_dataframe

def get_visual_insights(dataset_id: str) -> dict[str, Any]:
    frame = load_dataset_dataframe(dataset_id)
    profile = get_profile(dataset_id)
    try:
        configuration = get_saved_configuration(dataset_id)
    except Exception:
        configuration = None
    target = ((configuration or {}).get("target") or {}).get("column")
    result: dict[str, Any] = {"target": target, "problem_type": (configuration or {}).get("problem_type"), "target_distribution": [], "positive_class": None, "category_target_rates": [], "correlation_matrix": None}
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
    return result
