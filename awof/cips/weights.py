"""Central CIPS weights and priority thresholds."""

from __future__ import annotations


BASE_WEIGHTS = {
    "risk": 0.45,
    "business_value": 0.25,
    "engagement": 0.10,
    "complaint": 0.10,
    "sentiment": 0.05,
    "recency": 0.05,
}

PRIORITY_THRESHOLDS = (
    (85.0, "immediate"),
    (70.0, "high"),
    (40.0, "medium"),
    (0.0, "monitor"),
)


def effective_weights(available_signals: list[str]) -> dict[str, float]:
    selected = {signal: BASE_WEIGHTS[signal] for signal in available_signals if signal in BASE_WEIGHTS}
    total = sum(selected.values())
    if total == 0:
        return {}
    return {signal: value / total for signal, value in selected.items()}


def priority_level(score: float) -> str:
    for threshold, level in PRIORITY_THRESHOLDS:
        if score >= threshold:
            return level
    return "monitor"
