"""Optional SHAP capability detection.

SHAP is intentionally not emulated: callers use deterministic fallbacks when
the optional dependency is absent or incompatible.
"""

from importlib.util import find_spec


def shap_available() -> bool:
    return find_spec("shap") is not None
