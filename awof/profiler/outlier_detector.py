"""Non-destructive IQR-based outlier detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import to_json_safe


def _finite_numeric_values(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return np.asarray(values, dtype=float)


def detect_iqr_outliers(series: pd.Series) -> dict[str, Any]:
    """Describe IQR outliers; no values are removed or modified."""

    values = _finite_numeric_values(series)
    analyzed_count = int(values.size)
    result: dict[str, Any] = {
        "method": "iqr",
        "analyzed_count": analyzed_count,
        "q1": None,
        "q3": None,
        "iqr": None,
        "lower_bound": None,
        "upper_bound": None,
        "outlier_count": 0,
        "outlier_percentage": 0.0,
        "z_score_outlier_count": None,
        "z_score_outlier_percentage": None,
    }
    if analyzed_count == 0:
        return result

    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outlier_count = int(np.count_nonzero((values < lower_bound) | (values > upper_bound)))
    result.update(
        {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": outlier_count,
            "outlier_percentage": outlier_count / analyzed_count * 100.0,
        }
    )

    # Z scores are supplemental only. A zero-variance column has no stable
    # z-score interpretation, so those fields remain null.
    if analyzed_count >= 3:
        standard_deviation = float(np.std(values, ddof=0))
        if np.isfinite(standard_deviation) and standard_deviation > 0.0:
            z_count = int(np.count_nonzero(np.abs((values - np.mean(values)) / standard_deviation) > 3.0))
            result["z_score_outlier_count"] = z_count
            result["z_score_outlier_percentage"] = z_count / analyzed_count * 100.0
    return to_json_safe(result)


class OutlierDetector:
    """Facade for direct use and DatasetProfiler orchestration."""

    @staticmethod
    def analyze(series: pd.Series) -> dict[str, Any]:
        return detect_iqr_outliers(series)

    detect = analyze
