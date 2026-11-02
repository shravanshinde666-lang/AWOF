"""Application service for interactive live inference and counterfactual simulation."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from awof.inference.counterfactual import (
    extract_inference_features,
    predict_with_explanation,
    search_counterfactuals,
)
from .explainability_service import (
    ExplainabilityPrerequisiteError,
    load_best_model_context,
)


class InferenceError(Exception):
    pass


def _clean_val(val: Any) -> Any:
    if isinstance(val, (np.generic,)):
        return val.item()
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def get_inference_schema(dataset_id: str) -> dict[str, Any]:
    """Return feature descriptors, input defaults, and sample rows for the best fitted pipeline."""
    try:
        pipeline, _, source_df, configuration, context = load_best_model_context(dataset_id)
    except ExplainabilityPrerequisiteError as exc:
        raise InferenceError(str(exc)) from exc

    features_meta = extract_inference_features(pipeline, source_df)

    # Format 5 sample rows so users can easily load real data into the playground
    sample_rows = []
    target_col = (configuration.get("target") or {}).get("column")
    profile = context.get("profile", {})
    id_col = next((item["column"] for item in profile.get("column_types", []) if item.get("is_identifier_candidate")), None)

    for idx in range(min(5, len(source_df))):
        row = source_df.iloc[idx]
        row_dict = {
            col: _clean_val(row[col])
            for col in getattr(pipeline, "feature_names_in_", source_df.columns)
            if col in row
        }
        
        label_parts = []
        if id_col and id_col in row and pd.notna(row[id_col]):
            label_parts.append(f"ID: {row[id_col]}")
        else:
            label_parts.append(f"Row {idx}")
        if target_col and target_col in row and pd.notna(row[target_col]):
            label_parts.append(f"Actual: {row[target_col]}")

        sample_rows.append({
            "row_index": idx,
            "label": " · ".join(label_parts),
            "values": row_dict,
        })

    model = pipeline.named_steps.get("model")
    target_classes = [_clean_val(c) for c in getattr(model, "classes_", [])]

    return {
        "dataset_id": dataset_id,
        "model_id": context["best"]["model_id"],
        "problem_type": configuration["problem_type"],
        "target_column": target_col,
        "target_classes": [str(c) for c in target_classes],
        "features": features_meta,
        "sample_rows": sample_rows,
    }


def run_live_inference(
    dataset_id: str,
    features: dict[str, Any],
    target_class: Any | None = None,
) -> dict[str, Any]:
    """Run prediction, local explanation, and counterfactuals on user-provided inputs."""
    try:
        pipeline, _, source_df, configuration, context = load_best_model_context(dataset_id)
    except ExplainabilityPrerequisiteError as exc:
        raise InferenceError(str(exc)) from exc

    problem_type = configuration["problem_type"]
    features_meta = extract_inference_features(pipeline, source_df)

    # Sanitize and convert numeric types in user input
    cleaned_input: dict[str, Any] = {}
    meta_lookup = {item["name"]: item for item in features_meta}

    for col in getattr(pipeline, "feature_names_in_", []):
        val = features.get(col)
        meta = meta_lookup.get(col)
        if meta and meta["type"] in ("numeric", "integer"):
            try:
                if val is None or val == "":
                    cleaned_input[col] = meta["median"]
                elif meta["type"] == "integer":
                    cleaned_input[col] = int(round(float(val)))
                else:
                    cleaned_input[col] = float(val)
            except (ValueError, TypeError):
                cleaned_input[col] = meta["median"]
        else:
            cleaned_input[col] = str(val) if val is not None else (meta.get("default_value") if meta else "")

    prediction_result = predict_with_explanation(pipeline, cleaned_input, problem_type)

    counterfactuals = search_counterfactuals(
        pipeline=pipeline,
        input_data=cleaned_input,
        problem_type=problem_type,
        features_metadata=features_meta,
        target_class=target_class,
    )

    return {
        **prediction_result,
        "counterfactuals": counterfactuals,
    }
