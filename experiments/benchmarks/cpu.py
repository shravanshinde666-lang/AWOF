"""Process CPU-time helpers for research experiments."""

from __future__ import annotations

from collections.abc import Callable
from time import process_time
from typing import Any, TypeVar


T = TypeVar("T")


def measure_process_cpu_time(operation: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[T, float]:
    """Run one operation and return CPU time consumed by this Python process."""

    started_at = process_time()
    result = operation(*args, **kwargs)
    return result, round((process_time() - started_at) * 1_000, 3)
