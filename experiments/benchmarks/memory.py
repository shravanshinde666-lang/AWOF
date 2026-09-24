"""Python-allocation memory measurements for research experiments.

``tracemalloc`` measures allocations tracked by Python, rather than total
machine RAM or every native allocation made by scientific libraries.  Result
fields deliberately call this ``peak_python_memory_mb`` to make that scope
clear in API responses and research reports.
"""

from __future__ import annotations

from collections.abc import Callable
import tracemalloc
from typing import Any, TypeVar


T = TypeVar("T")


def bytes_to_mb(value: int) -> float:
    """Convert bytes to MiB and retain a useful research-report precision."""

    return round(float(value) / (1024 * 1024), 6)


def measure_peak_memory(operation: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[T, float]:
    """Return an operation result and its peak tracked Python allocation in MiB.

    If a caller already enabled ``tracemalloc``, this function does not stop
    that caller's tracing session.  The peak is reset before the operation so
    the value still pertains to this measurement interval.
    """

    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        result = operation(*args, **kwargs)
        _, peak_bytes = tracemalloc.get_traced_memory()
        return result, bytes_to_mb(peak_bytes)
    finally:
        if not was_tracing:
            tracemalloc.stop()
