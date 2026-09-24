"""CIPS priority labels and conservative generic business actions."""

from __future__ import annotations


ACTIONS = {
    "immediate": "Immediate review/intervention recommended.",
    "high": "Prioritize for proactive outreach.",
    "medium": "Monitor and consider targeted engagement.",
    "monitor": "Continue standard monitoring.",
}


def recommended_action(level: str, objective_id: str) -> str:
    if objective_id == "optimize_revenue" and level in {"immediate", "high"}:
        return "Prioritize a value-focused business review."
    return ACTIONS[level]
