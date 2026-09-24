"""Main JSON-safe, non-destructive dataset intelligence profiler."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from .constants import (
    CORRELATION_MODERATE_MAX,
    CORRELATION_STRONG_MAX,
    CORRELATION_VERY_WEAK_MAX,
    CORRELATION_WEAK_MAX,
    to_json_safe,
)
from .distribution_analyzer import analyze_distribution
from .outlier_detector import detect_iqr_outliers
from .quality_analyzer import QualityAnalyzer
from .statistics import calculate_categorical_statistics, calculate_numeric_statistics
from .type_detector import TypeDetector


def correlation_strength(correlation: float) -> str:
    """Classify absolute Pearson correlation; this is not a causal statement."""

    absolute_value = abs(correlation)
    if absolute_value <= CORRELATION_VERY_WEAK_MAX:
        return "very_weak"
    if absolute_value <= CORRELATION_WEAK_MAX:
        return "weak"
    if absolute_value <= CORRELATION_MODERATE_MAX:
        return "moderate"
    if absolute_value <= CORRELATION_STRONG_MAX:
        return "strong"
    return "very_strong"


class DatasetProfiler:
    """Build a stable profile from a pandas DataFrame without changing it.

    Parameters
    ----------
    dataframe:
        The already loaded dataset.  File parsing remains the responsibility
        of the application service, so one profiling request uses one frame.
    dataset_id:
        Optional opaque identifier echoed in the profile for an API caller.
    """

    def __init__(self, dataframe: pd.DataFrame, dataset_id: str | None = None) -> None:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("DatasetProfiler expects a pandas DataFrame")
        self.dataframe = dataframe
        self.dataset_id = dataset_id

    def _summary(self, column_types: list[dict[str, Any]], quality: dict[str, Any]) -> dict[str, Any]:
        rows, columns = (int(value) for value in self.dataframe.shape)
        total_cells = rows * columns
        missing_cells = int(quality["missing_values"]["total_missing"])
        duplicate_rows = int(quality["duplicates"]["duplicate_rows"])
        try:
            memory_usage_bytes = int(self.dataframe.memory_usage(index=True, deep=True).sum())
        except (TypeError, ValueError):
            memory_usage_bytes = 0

        return {
            "rows": rows,
            "columns": columns,
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_percentage": float(
                missing_cells / total_cells * 100.0 if total_cells else 0.0
            ),
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": float(
                duplicate_rows / rows * 100.0 if rows else 0.0
            ),
            "memory_usage_bytes": memory_usage_bytes,
            "numerical_columns": sum(
                1 for item in column_types if item.get("broad_type") == "numerical"
            ),
            "categorical_columns": sum(
                1 for item in column_types if item.get("broad_type") == "categorical"
            ),
            "boolean_columns": sum(
                1 for item in column_types if item.get("broad_type") == "boolean"
            ),
            "datetime_columns": sum(
                1 for item in column_types if item.get("broad_type") == "datetime"
            ),
            "text_columns": sum(
                1 for item in column_types if item.get("broad_type") == "text"
            ),
        }

    def _column_profiles(
        self,
        column_types: list[dict[str, Any]],
        quality: dict[str, Any],
    ) -> tuple[dict[str, dict[str, Any]], int]:
        profiles: dict[str, dict[str, Any]] = {}
        columns_with_outliers = 0
        missing_by_column = quality["missing_values"]["by_column"]

        for position, type_info in enumerate(column_types):
            key = str(type_info.get("column_key", type_info["column"]))
            series = self.dataframe.iloc[:, position]
            is_numeric = type_info.get("broad_type") == "numerical"
            is_categorical = type_info.get("broad_type") in {"categorical", "boolean", "text"}

            numeric_statistics = calculate_numeric_statistics(series) if is_numeric else None
            categorical_statistics = (
                calculate_categorical_statistics(series) if is_categorical else None
            )
            outliers = detect_iqr_outliers(series) if is_numeric else None
            distribution = analyze_distribution(series) if is_numeric else None
            if outliers and int(outliers.get("outlier_count", 0)) > 0:
                columns_with_outliers += 1

            profiles[key] = {
                "column": type_info["column"],
                "type_info": type_info,
                "cardinality": {
                    "unique_count": type_info["unique_count"],
                    "unique_percentage": type_info["unique_percentage"],
                    "category": type_info["cardinality"],
                },
                "missing": missing_by_column[key],
                "is_constant": type_info["is_constant"],
                "numeric_statistics": numeric_statistics,
                "categorical_statistics": categorical_statistics,
                "outliers": outliers,
                "distribution": distribution,
            }
        return profiles, columns_with_outliers

    def _correlations(self, column_types: list[dict[str, Any]]) -> dict[str, Any]:
        numeric_columns: dict[str, pd.Series] = {}
        for position, type_info in enumerate(column_types):
            if type_info.get("broad_type") != "numerical":
                continue
            key = str(type_info.get("column_key", type_info["column"]))
            converted = pd.to_numeric(self.dataframe.iloc[:, position], errors="coerce")
            numeric_columns[key] = converted.replace([np.inf, -np.inf], np.nan)

        if len(numeric_columns) < 2:
            return {"method": "pearson", "pairs": []}

        numeric_frame = pd.DataFrame(numeric_columns)
        correlation_matrix = numeric_frame.corr(method="pearson", min_periods=2)
        names = list(numeric_frame.columns)
        pairs: list[dict[str, Any]] = []
        for first_index, first_name in enumerate(names):
            for second_name in names[first_index + 1 :]:
                value = correlation_matrix.loc[first_name, second_name]
                if pd.isna(value) or not np.isfinite(float(value)):
                    # Constant / under-observed pairs have no meaningful
                    # Pearson coefficient, so omit them rather than emitting
                    # an invalid JSON NaN.
                    continue
                coefficient = float(value)
                pairs.append(
                    {
                        "feature_1": first_name,
                        "feature_2": second_name,
                        "correlation": coefficient,
                        "strength": correlation_strength(coefficient),
                    }
                )
        return {"method": "pearson", "pairs": pairs}

    def generate_profile(self) -> dict[str, Any]:
        """Generate the full profile using actual DataFrame values only."""

        column_types = TypeDetector(self.dataframe).detect()
        quality = QualityAnalyzer(self.dataframe).analyze(column_types)
        quality["has_duplicates"] = quality["duplicates"]["has_duplicates"]
        quality["duplicate_rows"] = quality["duplicates"]["duplicate_rows"]
        quality["duplicate_percentage"] = quality["duplicates"]["duplicate_percentage"]
        columns, columns_with_outliers = self._column_profiles(column_types, quality)
        quality["summary"]["columns_with_outliers"] = columns_with_outliers

        profile: dict[str, Any] = {
            "summary": self._summary(column_types, quality),
            "column_types": column_types,
            "columns": columns,
            "quality": quality,
            "correlations": self._correlations(column_types),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.dataset_id is not None:
            profile["dataset_id"] = str(self.dataset_id)
        return to_json_safe(profile)

    # A concise alias for interactive/data-science use.
    profile = generate_profile
