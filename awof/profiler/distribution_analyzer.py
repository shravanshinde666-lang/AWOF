"""Bounded histogram and descriptive distribution-shape information."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import MAX_HISTOGRAM_BINS, to_json_safe


def _finite_numeric_values(series: pd.Series) -> np.ndarray:
    converted = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return np.asarray(converted, dtype=float)


def _distribution_shape(values: np.ndarray) -> str:
    if values.size == 0:
        return "unavailable"
    if np.allclose(values, values[0]):
        return "constant"
    if values.size < 3:
        return "insufficient_data"
    skewness = float(pd.Series(values).skew())
    if not np.isfinite(skewness):
        return "unavailable"
    if skewness > 0.5:
        return "right_skewed"
    if skewness < -0.5:
        return "left_skewed"
    return "symmetric_candidate"


def analyze_distribution(series: pd.Series) -> dict[str, Any]:
    """Create chart-ready histogram aggregates only, never raw dataset rows."""

    values = _finite_numeric_values(series)
    sample_size = int(values.size)
    if sample_size == 0:
        return {
            "sample_size": 0,
            "distribution_shape": "unavailable",
            "histogram": {"counts": [], "bin_edges": []},
        }

    if np.allclose(values, values[0]):
        counts = np.asarray([sample_size], dtype=int)
        # A visual width around a constant value is more useful than duplicate
        # bin edges and is handled consistently by chart libraries.
        center = float(values[0])
        width = max(abs(center) * 0.01, 0.5)
        edges = np.asarray([center - width, center + width], dtype=float)
    else:
        bin_count = min(MAX_HISTOGRAM_BINS, max(1, int(np.ceil(np.sqrt(sample_size)))))
        counts, edges = np.histogram(values, bins=bin_count)
    return to_json_safe(
        {
            "sample_size": sample_size,
            "distribution_shape": _distribution_shape(values),
            "histogram": {
                "counts": [int(value) for value in counts.tolist()],
                "bin_edges": [float(value) for value in edges.tolist()],
            },
        }
    )


class DistributionAnalyzer:
    """Facade for chart-safe numeric distribution analysis."""

    @staticmethod
    def analyze(series: pd.Series) -> dict[str, Any]:
        return analyze_distribution(series)
