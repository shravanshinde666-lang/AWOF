"""Small, dependency-free wall-clock timing helpers for research runs."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, TypeVar


T = TypeVar("T")


def elapsed_ms(started_at: float, finished_at: float | None = None) -> float:
    """Return a rounded ``perf_counter`` duration in milliseconds."""

    end = perf_counter() if finished_at is None else finished_at
    return round((end - started_at) * 1_000, 3)


def measure_runtime(operation: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[T, float]:
    """Run an operation once and return its result plus wall-clock milliseconds."""

    started_at = perf_counter()
    result = operation(*args, **kwargs)
    return result, elapsed_ms(started_at)
