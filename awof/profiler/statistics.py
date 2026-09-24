"""Descriptive numerical and categorical statistics for a dataset profile."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .constants import TOP_CATEGORY_LIMIT, to_json_safe


def _finite_numeric_series(series: pd.Series) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    values = converted.replace([np.inf, -np.inf], np.nan).dropna()
    return values.astype(float)


def calculate_numeric_statistics(series: pd.Series) -> dict[str, Any]:
    """Calculate safe descriptive statistics without changing ``series``.

    Variance and standard deviation use the conventional sample definition
    (``ddof=1``) when at least two finite observations are available.
    """

    numeric = _finite_numeric_series(series)
    count = int(len(numeric))
    empty_result: dict[str, Any] = {
        "count": count,
        "mean": None,
        "median": None,
        "mode": None,
        "minimum": None,
        "maximum": None,
        "range": None,
        "variance": None,
        "standard_deviation": None,
        "q1": None,
        "q2": None,
        "q3": None,
        "iqr": None,
        "skewness": None,
        "kurtosis": None,
    }
    if count == 0:
        return empty_result

    modes = numeric.mode(dropna=True)
    mode = modes.iloc[0] if not modes.empty else None
    minimum = numeric.min()
    maximum = numeric.max()
    q1 = numeric.quantile(0.25)
    q2 = numeric.quantile(0.50)
    q3 = numeric.quantile(0.75)

    empty_result.update(
        {
            "mean": numeric.mean(),
            "median": q2,
            "mode": mode,
            "minimum": minimum,
            "maximum": maximum,
            "range": maximum - minimum,
            "variance": numeric.var(ddof=1) if count > 1 else None,
            "standard_deviation": numeric.std(ddof=1) if count > 1 else None,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "iqr": q3 - q1,
            "skewness": numeric.skew() if count >= 3 else None,
            "kurtosis": numeric.kurt() if count >= 4 else None,
        }
    )
    return to_json_safe(empty_result)


def _safe_value_counts(series: pd.Series) -> list[tuple[Any, int]]:
    non_null = series.dropna()
    try:
        counts = non_null.value_counts(dropna=True)
        return [(value, int(count)) for value, count in counts.items()]
    except TypeError:
        # Fallback for rare unhashable in-memory cell values.
        result: dict[str, int] = {}
        for value in non_null.tolist():
            key = repr(value)
            result[key] = result.get(key, 0) + 1
        return sorted(result.items(), key=lambda item: (-item[1], item[0]))


def calculate_categorical_statistics(
    series: pd.Series, top_limit: int = TOP_CATEGORY_LIMIT
) -> dict[str, Any]:
    """Return bounded frequency information for categorical-like columns."""

    counts = _safe_value_counts(series)
    non_missing_count = int(series.notna().sum())
    unique_count = len(counts)
    if counts:
        mode_value, mode_frequency = counts[0]
        mode_percentage = mode_frequency / non_missing_count * 100.0 if non_missing_count else 0.0
    else:
        mode_value, mode_frequency, mode_percentage = None, 0, 0.0

    top_values = [
        {
            "value": to_json_safe(value),
            "count": int(count),
            "percentage": float(count / non_missing_count * 100.0) if non_missing_count else 0.0,
        }
        for value, count in counts[: max(0, top_limit)]
    ]
    return to_json_safe(
        {
            "count": non_missing_count,
            "unique_count": unique_count,
            "mode": mode_value,
            "mode_frequency": int(mode_frequency),
            "mode_percentage": float(mode_percentage),
            "top_values": top_values,
        }
    )


class StatisticsAnalyzer:
    """Small façade used by :class:`DatasetProfiler` and direct callers."""

    @staticmethod
    def numeric(series: pd.Series) -> dict[str, Any]:
        return calculate_numeric_statistics(series)

    @staticmethod
    def categorical(series: pd.Series, top_limit: int = TOP_CATEGORY_LIMIT) -> dict[str, Any]:
        return calculate_categorical_statistics(series, top_limit=top_limit)
