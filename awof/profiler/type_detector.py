"""Heuristic, dataset-agnostic column type detection."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
from pandas.api import types as pdt

from .constants import (
    CARDINALITY_CONSTANT_MAX_UNIQUE,
    CARDINALITY_LOW_MAX_UNIQUE,
    CARDINALITY_MEDIUM_MAX_PERCENT,
    CARDINALITY_MEDIUM_MAX_UNIQUE,
    CARDINALITY_NEAR_UNIQUE_MIN_PERCENT,
    IDENTIFIER_MIN_NON_NULL_VALUES,
    IDENTIFIER_NAME_UNIQUENESS_MIN_PERCENT,
    IDENTIFIER_NEAR_UNIQUE_MIN_PERCENT,
    TEXT_AVERAGE_LENGTH_MIN,
    TEXT_AVERAGE_WORDS_MIN,
)


_BOOLEAN_TOKENS = {
    "true",
    "false",
    "yes",
    "no",
    "y",
    "n",
    "t",
    "f",
}
_NUMERIC_BINARY_VALUES = {0.0, 1.0}
_IDENTIFIER_NAME_PATTERN = re.compile(
    r"(?:^|[_\s\-])(id|uuid|guid|identifier|key|index)(?:$|[_\s\-])|(?:_id$)",
    re.IGNORECASE,
)
_BOOLEAN_NAME_PATTERN = re.compile(
    r"^(is|has|can|should|was|does|did)[_\s\-]|(?:flag|boolean|bool)$",
    re.IGNORECASE,
)
_DATETIME_NAME_PATTERN = re.compile(
    r"(?:date|time|timestamp|datetime|created|updated|dob|birth)", re.IGNORECASE
)
_DATE_LIKE_VALUE_PATTERN = re.compile(
    r"^\s*(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|"
    r"\d{4}-\d{1,2}-\d{1,2}[T\s].+)\s*$"
)

# These are intentionally narrow, recognizable sequences rather than a guess
# that every short categorical column has an inherent order.
_ORDINAL_VALUE_SETS = (
    {"low", "medium", "high"},
    {"very low", "low", "medium", "high", "very high"},
    {"poor", "fair", "good", "very good", "excellent"},
    {"strongly disagree", "disagree", "neutral", "agree", "strongly agree"},
    {"small", "medium", "large"},
)


def cardinality_category(unique_count: int, total_count: int) -> str:
    """Return a stable, centrally-thresholded cardinality category."""

    unique_percentage = (unique_count / total_count * 100.0) if total_count else 0.0
    if unique_count <= CARDINALITY_CONSTANT_MAX_UNIQUE:
        return "constant"
    if unique_percentage >= CARDINALITY_NEAR_UNIQUE_MIN_PERCENT:
        return "near_unique"
    if unique_count <= CARDINALITY_LOW_MAX_UNIQUE:
        return "low"
    if (
        unique_count <= CARDINALITY_MEDIUM_MAX_UNIQUE
        or unique_percentage <= CARDINALITY_MEDIUM_MAX_PERCENT
    ):
        return "medium"
    return "high"


def _safe_unique_count(series: pd.Series) -> int:
    try:
        return int(series.nunique(dropna=True))
    except TypeError:
        # Unhashable cells are uncommon in uploaded tabular data, but a
        # profiler should still describe an in-memory DataFrame safely.
        return len({repr(value) for value in series.dropna().tolist()})


def _normalised_values(series: pd.Series) -> list[str]:
    return [str(value).strip().casefold() for value in series.dropna().tolist()]


def _is_datetime_candidate(series: pd.Series, column_name: str) -> bool:
    if pdt.is_datetime64_any_dtype(series):
        return True

    non_null = series.dropna()
    if non_null.empty:
        return False
    if all(hasattr(value, "year") and hasattr(value, "month") for value in non_null):
        return True
    if not (pdt.is_object_dtype(series) or pdt.is_string_dtype(series)):
        return False

    values = [str(value).strip() for value in non_null.tolist()]
    date_like_ratio = sum(bool(_DATE_LIKE_VALUE_PATTERN.match(value)) for value in values) / len(values)
    has_datetime_name = bool(_DATETIME_NAME_PATTERN.search(str(column_name)))
    # Restrict parsing to date-shaped values or a meaningful datetime name;
    # this prevents ordinary numeric/text strings becoming timestamps.
    if date_like_ratio < 0.8 and not has_datetime_name:
        return False
    try:
        parsed = pd.to_datetime(pd.Series(values), errors="coerce", format="mixed")
    except (TypeError, ValueError):
        parsed = pd.to_datetime(pd.Series(values), errors="coerce")
    return bool(parsed.notna().mean() >= 0.9)


def _numeric_values(series: pd.Series) -> np.ndarray | None:
    """Return finite numeric values when a series is reliably numeric-like."""

    non_null = series.dropna()
    if non_null.empty:
        return None
    if pdt.is_numeric_dtype(series) and not pdt.is_bool_dtype(series):
        converted = pd.to_numeric(non_null, errors="coerce")
    elif pdt.is_object_dtype(series) or pdt.is_string_dtype(series):
        converted = pd.to_numeric(non_null, errors="coerce")
        if float(converted.notna().mean()) < 0.95:
            return None
    else:
        return None
    values = np.asarray(converted, dtype=float)
    return values[np.isfinite(values)]


def _numeric_detected_type(series: pd.Series, numeric_values: np.ndarray) -> str:
    if numeric_values.size == 0:
        return "unknown"
    if pdt.is_integer_dtype(series):
        return "integer"
    if np.all(np.isclose(numeric_values, np.round(numeric_values))):
        return "integer"
    return "continuous_numeric"


def _is_ordinal_candidate(series: pd.Series) -> bool:
    if isinstance(series.dtype, pd.CategoricalDtype) and series.dtype.ordered:
        return True
    values = set(_normalised_values(series))
    if len(values) < 2:
        return False
    return any(values.issubset(ordered_set) for ordered_set in _ORDINAL_VALUE_SETS)


def _text_features(series: pd.Series) -> tuple[float, float, float]:
    values = [str(value).strip() for value in series.dropna().tolist()]
    if not values:
        return 0.0, 0.0, 0.0
    lengths = [len(value) for value in values]
    words = [len(value.split()) for value in values]
    unique_ratio = _safe_unique_count(series) / len(values)
    return float(np.mean(lengths)), float(np.mean(words)), float(unique_ratio)


def _is_text_candidate(series: pd.Series) -> bool:
    average_length, average_words, unique_ratio = _text_features(series)
    return bool(
        average_length >= TEXT_AVERAGE_LENGTH_MIN
        and (average_words >= TEXT_AVERAGE_WORDS_MIN or unique_ratio >= 0.5)
    )


def _has_identifier_name(column_name: str) -> bool:
    return bool(_IDENTIFIER_NAME_PATTERN.search(str(column_name)))


def _is_identifier_candidate(
    series: pd.Series,
    column_name: str,
    base_type: str,
    is_text: bool,
) -> bool:
    non_null_count = int(series.notna().sum())
    if non_null_count == 0 or is_text:
        return False
    unique_count = _safe_unique_count(series)
    unique_percentage = unique_count / non_null_count * 100.0
    if _has_identifier_name(column_name):
        return unique_percentage >= IDENTIFIER_NAME_UNIQUENESS_MIN_PERCENT
    # A short, almost entirely unique categorical code column can be an ID
    # without a helpful name. Numeric measurements are not marked as IDs from
    # uniqueness alone, because e.g. a real-valued measurement is often unique.
    if (
        base_type in {"nominal", "binary"}
        and non_null_count >= IDENTIFIER_MIN_NON_NULL_VALUES
        and unique_percentage >= IDENTIFIER_NEAR_UNIQUE_MIN_PERCENT
    ):
        average_length, _, _ = _text_features(series)
        return average_length <= 36.0
    return False


class TypeDetector:
    """Detect broad, descriptive column types without modifying a DataFrame."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.dataframe = dataframe

    def detect_column(
        self,
        series: pd.Series,
        column_name: str | None = None,
        column_key: str | None = None,
    ) -> dict[str, Any]:
        """Return type/cardinality metadata for one Series."""

        display_name = str(series.name if column_name is None else column_name)
        total_count = int(len(series))
        non_null_count = int(series.notna().sum())
        unique_count = _safe_unique_count(series)
        unique_percentage = unique_count / total_count * 100.0 if total_count else 0.0
        is_constant = unique_count <= CARDINALITY_CONSTANT_MAX_UNIQUE

        detected_type = "unknown"
        broad_type = "unknown"
        base_type = "unknown"

        if non_null_count:
            numeric_values = _numeric_values(series)
            normalised = set(_normalised_values(series))
            numeric_binary = (
                numeric_values is not None
                and numeric_values.size > 0
                and set(np.unique(numeric_values)).issubset(_NUMERIC_BINARY_VALUES)
                and len(np.unique(numeric_values)) <= 2
            )

            if _is_datetime_candidate(series, display_name):
                base_type = detected_type = "datetime"
                broad_type = "datetime"
            elif pdt.is_bool_dtype(series) or (
                normalised and normalised.issubset(_BOOLEAN_TOKENS) and len(normalised) <= 2
            ):
                base_type = detected_type = "boolean"
                broad_type = "boolean"
            elif numeric_binary:
                # Numeric 0/1 attributes are binary by default. A strongly
                # boolean-like name provides the useful boolean distinction.
                if _BOOLEAN_NAME_PATTERN.search(display_name):
                    base_type = detected_type = "boolean"
                    broad_type = "boolean"
                else:
                    base_type = detected_type = "binary"
                    broad_type = "categorical"
            elif numeric_values is not None and numeric_values.size:
                base_type = detected_type = _numeric_detected_type(series, numeric_values)
                broad_type = "numerical"
            elif _is_ordinal_candidate(series):
                base_type = detected_type = "ordinal_candidate"
                broad_type = "categorical"
            elif unique_count == 2:
                base_type = detected_type = "binary"
                broad_type = "categorical"
            elif _is_text_candidate(series):
                base_type = detected_type = "text"
                broad_type = "text"
            elif pdt.is_object_dtype(series) or pdt.is_string_dtype(series) or isinstance(
                series.dtype, pd.CategoricalDtype
            ):
                base_type = detected_type = "nominal"
                broad_type = "categorical"

            is_text = base_type == "text"
            identifier_candidate = _is_identifier_candidate(
                series, display_name, base_type, is_text
            )
            if identifier_candidate:
                detected_type = "identifier_candidate"
        else:
            identifier_candidate = False

        result: dict[str, Any] = {
            "column": display_name,
            "pandas_dtype": str(series.dtype),
            "detected_type": detected_type,
            "broad_type": broad_type,
            "nullable": bool(series.isna().any()),
            "unique_count": unique_count,
            "unique_percentage": float(unique_percentage),
            "cardinality": cardinality_category(unique_count, total_count),
            "is_constant": bool(is_constant),
            "is_identifier_candidate": bool(identifier_candidate),
        }
        if column_key is not None:
            result["column_key"] = column_key
        return result

    def detect(self) -> list[dict[str, Any]]:
        """Detect every column in dataframe order, including duplicate labels."""

        results: list[dict[str, Any]] = []
        used_keys: dict[str, int] = {}
        for position, column_name in enumerate(self.dataframe.columns):
            display_name = str(column_name)
            occurrence = used_keys.get(display_name, 0)
            used_keys[display_name] = occurrence + 1
            column_key = display_name if occurrence == 0 else f"{display_name}__{occurrence + 1}"
            results.append(
                self.detect_column(
                    self.dataframe.iloc[:, position],
                    column_name=display_name,
                    column_key=column_key,
                )
            )
        return results

    # A readable alias for callers that prefer an explicit name.
    detect_types = detect
