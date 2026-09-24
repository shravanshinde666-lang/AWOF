"""Bounded, deterministic cross-validation for supervised model pipelines."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score


def evaluate_cross_validation(pipeline: Any, features: Any, target: Any, problem_type: str) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    sample_count = len(features)
    if problem_type == "classification":
        counts = target.value_counts(dropna=False)
        folds = min(5, int(counts.min()) if len(counts) else 0)
        scorer = "f1_weighted"
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42) if folds >= 2 else None
    else:
        folds = min(5, sample_count)
        scorer = "neg_root_mean_squared_error"
        splitter = KFold(n_splits=folds, shuffle=True, random_state=42) if folds >= 2 else None
    if splitter is None:
        return {"applicable": False, "folds": 0, "metric": scorer, "mean": None, "scores": []}, ["Cross-validation requires at least two viable folds."]
    try:
        scores = cross_val_score(pipeline, features, target, cv=splitter, scoring=scorer, n_jobs=1)
        if problem_type == "regression":
            scores = -scores
        rounded_scores = [round(float(value), 6) for value in scores]
        return {"applicable": True, "folds": folds, "metric": "f1_weighted" if problem_type == "classification" else "rmse", "mean": round(float(np.mean(scores)), 6), "scores": rounded_scores}, warnings
    except (ValueError, TypeError) as exc:
        warnings.append(f"Cross-validation was unavailable: {exc}")
        return {"applicable": False, "folds": folds, "metric": scorer, "mean": None, "scores": []}, warnings
