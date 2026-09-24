"""Dataset-agnostic Customer Intervention Priority Score calculation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .prioritizer import recommended_action
from .weights import effective_weights, priority_level


SIGNAL_TERMS = {
    "business_value": ("revenue", "spend", "amount", "value", "charges", "purchase_amount", "clv", "lifetime_value"),
    "engagement": ("frequency", "transactions", "visits", "usage", "orders"),
    "complaint": ("complaint", "support", "ticket", "service_call"),
    "sentiment": ("sentiment",),
    "recency": ("recency", "last_purchase", "last_activity"),
}

DISPLAY_NAMES = {
    "risk": "predicted risk",
    "business_value": "business value",
    "engagement": "engagement activity",
    "complaint": "support or complaint activity",
    "sentiment": "sentiment signal",
    "recency": "recency signal",
}


def detect_business_signals(dataframe: pd.DataFrame, excluded_columns: set[str] | None = None) -> tuple[dict[str, str], list[str]]:
    excluded_columns = excluded_columns or set()
    mapping: dict[str, str] = {}
    warnings: list[str] = []
    for signal, terms in SIGNAL_TERMS.items():
        for column in dataframe.columns:
            if column in excluded_columns or not pd.api.types.is_numeric_dtype(dataframe[column]):
                continue
            normalized = str(column).casefold()
            if any(term in normalized for term in terms):
                mapping[signal] = str(column)
                if signal in {"recency", "sentiment"}:
                    warnings.append(f"{signal.title()} direction is semantically ambiguous and was not automatically inverted.")
                break
    return mapping, warnings


def min_max_normalize(values: pd.Series | np.ndarray) -> np.ndarray:
    numeric = np.asarray(pd.to_numeric(values, errors="coerce"), dtype=float)
    finite = np.isfinite(numeric)
    if not finite.any():
        return np.zeros(len(numeric), dtype=float)
    minimum, maximum = float(np.nanmin(numeric[finite])), float(np.nanmax(numeric[finite]))
    if maximum == minimum:
        return np.full(len(numeric), 0.5, dtype=float)
    result = (numeric - minimum) / (maximum - minimum)
    result[~finite] = 0.0
    return np.clip(result, 0.0, 1.0)


def calculate_cips(
    dataframe: pd.DataFrame,
    predictions: np.ndarray,
    risk_values: np.ndarray,
    signal_mapping: dict[str, str],
    entity_column: str | None,
    objective_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Calculate compact, ranked rows from risk plus detected available signals."""
    available = ["risk", *signal_mapping.keys()]
    weights = effective_weights(available)
    normalized: dict[str, np.ndarray] = {"risk": np.clip(np.asarray(risk_values, dtype=float), 0.0, 1.0)}
    for signal, column in signal_mapping.items():
        normalized[signal] = min_max_normalize(dataframe[column])
    records: list[dict[str, Any]] = []
    for index in range(len(dataframe)):
        contributions = {signal: float(weights[signal] * normalized[signal][index]) for signal in weights}
        score = round(float(np.clip(sum(contributions.values()) * 100, 0.0, 100.0)), 6)
        level = priority_level(score)
        ranked_signals = sorted(contributions, key=lambda signal: (-contributions[signal], signal))
        top_reasons = [f"High {DISPLAY_NAMES[signal]}" for signal in ranked_signals[:3] if normalized[signal][index] > 0]
        signals = {signal: round(float(normalized[signal][index]), 8) for signal in normalized}
        if entity_column:
            entity_value = dataframe.iloc[index][entity_column]
            entity_id = None if pd.isna(entity_value) else str(entity_value)
        else:
            entity_id = None
        prediction = predictions[index]
        if isinstance(prediction, np.generic):
            prediction = prediction.item()
        records.append({
            "row_index": int(index), "entity_id": entity_id, "prediction": prediction,
            "risk_probability": round(float(normalized["risk"][index]), 8), "cips_score": score,
            "priority_level": level, "signals": signals, "effective_weights": weights,
            "top_reasons": top_reasons or ["Available priority signals are low."],
            "recommended_action": recommended_action(level, objective_id),
        })
    records.sort(key=lambda item: (-item["cips_score"], item["row_index"]))
    return records, weights, []
