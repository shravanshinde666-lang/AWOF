"""Factual data-quality signals; this module never cleans or transforms data."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .constants import (
    MISSING_HIGH_MAX_PERCENT,
    MISSING_LOW_MAX_PERCENT,
    MISSING_MODERATE_MAX_PERCENT,
)


def missing_severity(missing_percentage: float) -> str:
    """Classify a percentage using the profiler's documented thresholds."""

    if missing_percentage <= 0.0:
        return "none"
    if missing_percentage <= MISSING_LOW_MAX_PERCENT:
        return "low"
    if missing_percentage <= MISSING_MODERATE_MAX_PERCENT:
        return "moderate"
    if missing_percentage <= MISSING_HIGH_MAX_PERCENT:
        return "high"
    return "critical"


def analyze_missing_values(series: pd.Series) -> dict[str, Any]:
    total_count = int(len(series))
    missing_count = int(series.isna().sum())
    non_missing_count = total_count - missing_count
    missing_percentage = missing_count / total_count * 100.0 if total_count else 0.0
    return {
        "missing_count": missing_count,
        "missing_percentage": float(missing_percentage),
        "non_missing_count": non_missing_count,
        "severity": missing_severity(float(missing_percentage)),
    }


class QualityAnalyzer:
    """Inspect missingness and duplicate rows without changing the input."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.dataframe = dataframe

    def analyze(self, column_types: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        type_list = list(column_types) if column_types is not None else []
        missing_by_column: dict[str, dict[str, Any]] = {}
        total_missing = 0
        for position, column_name in enumerate(self.dataframe.columns):
            info = analyze_missing_values(self.dataframe.iloc[:, position])
            key = str(column_name)
            # The detector supplies a stable suffix for duplicate column names.
            if position < len(type_list):
                key = str(type_list[position].get("column_key", key))
            missing_by_column[key] = {"column": str(column_name), **info}
            total_missing += int(info["missing_count"])

        rows = int(len(self.dataframe))
        total_cells = rows * int(self.dataframe.shape[1])
        try:
            duplicate_rows = int(self.dataframe.duplicated().sum())
        except TypeError:
            # Uploaded CSV/Excel cells are hashable. This merely keeps direct
            # in-memory use from failing for exotic object columns.
            duplicate_rows = 0
        duplicate_percentage = duplicate_rows / rows * 100.0 if rows else 0.0

        missing_values = {
            "total_missing": int(total_missing),
            "overall_missing_percentage": float(
                total_missing / total_cells * 100.0 if total_cells else 0.0
            ),
            "by_column": missing_by_column,
        }
        duplicates = {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": float(duplicate_percentage),
            "has_duplicates": bool(duplicate_rows > 0),
        }
        return {
            "missing_values": missing_values,
            "duplicates": duplicates,
            # Flat aliases make the core quality report convenient for simple
            # consumers while preserving the grouped, extensible structure.
            "total_missing": missing_values["total_missing"],
            "overall_missing_percentage": missing_values["overall_missing_percentage"],
            "duplicate_rows": duplicates["duplicate_rows"],
            "duplicate_percentage": duplicates["duplicate_percentage"],
            "has_duplicates": duplicates["has_duplicates"],
            "summary": {
                "columns_with_missing_values": sum(
                    1 for item in missing_by_column.values() if item["missing_count"] > 0
                ),
                "constant_columns": sum(
                    1 for item in type_list if bool(item.get("is_constant"))
                ),
                "high_cardinality_columns": sum(
                    1
                    for item in type_list
                    if item.get("cardinality") in {"high", "near_unique"}
                ),
                # DatasetProfiler fills this factual count after IQR analysis.
                "columns_with_outliers": 0,
            },
        }
