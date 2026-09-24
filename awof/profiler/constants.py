"""Shared, documented thresholds for dataset profiling heuristics.

The values in this module are deliberately conservative.  They describe data
characteristics; they do not make semantic or business decisions.
"""

from __future__ import annotations

from datetime import date, datetime
import math
from typing import Any

import numpy as np
import pandas as pd

# Cardinality is assessed against the total number of rows.  Near-unique is
# checked first, followed by small absolute-cardinality categories.
CARDINALITY_CONSTANT_MAX_UNIQUE = 1
CARDINALITY_NEAR_UNIQUE_MIN_PERCENT = 90.0
CARDINALITY_LOW_MAX_UNIQUE = 10
CARDINALITY_MEDIUM_MAX_UNIQUE = 50
CARDINALITY_MEDIUM_MAX_PERCENT = 20.0

# Missingness severity thresholds are inclusive at their upper boundary.
MISSING_LOW_MAX_PERCENT = 5.0
MISSING_MODERATE_MAX_PERCENT = 20.0
MISSING_HIGH_MAX_PERCENT = 50.0

# Detection heuristics.  They intentionally require more than a column name
# alone before a value pattern is labelled as an identifier or free text.
IDENTIFIER_MIN_NON_NULL_VALUES = 10
IDENTIFIER_NEAR_UNIQUE_MIN_PERCENT = 98.0
IDENTIFIER_NAME_UNIQUENESS_MIN_PERCENT = 50.0
TEXT_AVERAGE_LENGTH_MIN = 20.0
TEXT_AVERAGE_WORDS_MIN = 3.0

# Aggregated data sent to a client must stay bounded.
TOP_CATEGORY_LIMIT = 10
MAX_HISTOGRAM_BINS = 30

# Pearson correlation labels use absolute values and must never be read as
# causal claims.
CORRELATION_VERY_WEAK_MAX = 0.19
CORRELATION_WEAK_MAX = 0.39
CORRELATION_MODERATE_MAX = 0.59
CORRELATION_STRONG_MAX = 0.79


def to_json_safe(value: Any) -> Any:
    """Recursively convert pandas/NumPy values to strict JSON-safe values.

    Non-finite numeric values and missing temporal values become ``None`` so
    callers can safely use the standard library's ``json.dumps(...,
    allow_nan=False)``.
    """

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, (pd.Timestamp, datetime, date)):
        if pd.isna(value):
            return None
        return value.isoformat()

    if isinstance(value, np.generic):
        return to_json_safe(value.item())

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, (list, tuple, set, np.ndarray, pd.Index)):
        return [to_json_safe(item) for item in value]

    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}

    # ``pd.isna`` can return an array for collection-like custom objects.
    try:
        is_missing = pd.isna(value)
        if isinstance(is_missing, (bool, np.bool_)) and is_missing:
            return None
    except (TypeError, ValueError):
        pass

    # JSON can represent regular scalar values directly.  Convert uncommon
    # scalar objects (for example Decimal) to strings rather than leaking an
    # unserializable object to an API response.
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)
