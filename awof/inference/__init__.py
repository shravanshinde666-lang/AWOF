"""Inference and counterfactual explanation package for AWOF."""

from .counterfactual import (
    extract_inference_features,
    predict_with_explanation,
    search_counterfactuals,
)

__all__ = [
    "extract_inference_features",
    "predict_with_explanation",
    "search_counterfactuals",
]
