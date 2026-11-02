"""Inference and counterfactual reasoning engine for fitted AWOF pipelines."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from awof.explainability.feature_importance import local_explanation


def _json_safe(value: Any) -> Any:
    """Ensure primitives are JSON-serializable."""
    if isinstance(value, (np.generic,)):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def extract_inference_features(pipeline: Any, dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Inspect expected features and compute bounds, categories, and defaults."""
    feature_names = [str(col) for col in getattr(pipeline, "feature_names_in_", [])]
    if not feature_names:
        feature_names = [str(col) for col in dataframe.columns]

    feature_metadata: list[dict[str, Any]] = []

    for name in feature_names:
        if name not in dataframe.columns:
            continue

        series = dataframe[name].dropna()
        is_numeric = bool(pd.api.types.is_numeric_dtype(series))

        if is_numeric and series.nunique() > 1:
            val_min = float(series.min())
            val_max = float(series.max())
            val_mean = float(series.mean())
            val_median = float(series.median())
            
            # Step heuristic
            is_int = bool(pd.api.types.is_integer_dtype(series))
            step = 1.0 if is_int else round(max((val_max - val_min) / 100.0, 0.01), 4)

            default_val = int(val_median) if is_int else round(val_median, 4)

            feature_metadata.append({
                "name": name,
                "type": "integer" if is_int else "numeric",
                "min": round(val_min, 4),
                "max": round(val_max, 4),
                "mean": round(val_mean, 4),
                "median": round(val_median, 4),
                "step": step,
                "default_value": default_val,
                "categories": None,
            })
        else:
            categories = [str(x) for x in series.unique() if pd.notna(x)]
            # Bounded list of categories
            categories = sorted(categories[:50])
            mode_val = str(series.mode()[0]) if not series.empty else (categories[0] if categories else "")

            feature_metadata.append({
                "name": name,
                "type": "categorical",
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "step": None,
                "default_value": mode_val,
                "categories": categories,
            })

    return feature_metadata


def predict_with_explanation(
    pipeline: Any,
    input_data: dict[str, Any],
    problem_type: str,
    top_n: int = 10,
) -> dict[str, Any]:
    """Execute live inference and instance-level explanation."""
    expected_cols = [str(col) for col in getattr(pipeline, "feature_names_in_", list(input_data.keys()))]
    
    # Construct clean single-row dataframe
    row_dict = {col: input_data.get(col) for col in expected_cols}
    row_df = pd.DataFrame([row_dict])

    prediction_raw = pipeline.predict(row_df)[0]
    prediction = _json_safe(prediction_raw)

    probabilities: dict[str, float] = {}
    confidence: float | None = None

    if problem_type == "classification" and hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(row_df)[0]
        model = pipeline.named_steps.get("model")
        classes = [_json_safe(cls) for cls in getattr(model, "classes_", [])]
        for cls_name, prob in zip(classes, probs):
            probabilities[str(cls_name)] = round(float(prob), 4)
        if str(prediction) in probabilities:
            confidence = probabilities[str(prediction)]
        elif probabilities:
            confidence = max(probabilities.values())

    # Get local explanation
    try:
        explanation, _ = local_explanation(pipeline, row_df, problem_type, top_n=top_n)
        local_factors = explanation.get("feature_contributions", [])
    except Exception:
        local_factors = []

    return {
        "prediction": prediction,
        "prediction_label": str(prediction),
        "probabilities": probabilities,
        "confidence": confidence,
        "local_factors": local_factors,
    }


def search_counterfactuals(
    pipeline: Any,
    input_data: dict[str, Any],
    problem_type: str,
    features_metadata: list[dict[str, Any]],
    target_class: Any | None = None,
    max_recommendations: int = 4,
) -> list[dict[str, Any]]:
    """Search for minimal single-feature perturbations that flip or significantly alter model outcome."""
    expected_cols = [str(col) for col in getattr(pipeline, "feature_names_in_", list(input_data.keys()))]
    meta_lookup = {item["name"]: item for item in features_metadata}

    base_prediction = predict_with_explanation(pipeline, input_data, problem_type)
    current_pred = base_prediction["prediction"]

    counterfactuals: list[dict[str, Any]] = []

    # Sort candidates by local factor importance if available, else standard order
    priority_cols = [f["original_feature"] for f in base_prediction["local_factors"] if f.get("original_feature")]
    ordered_cols = list(dict.fromkeys(priority_cols + expected_cols))

    if problem_type == "classification":
        # Search for changes that flip classification
        for col_name in ordered_cols:
            if col_name not in meta_lookup or col_name not in input_data:
                continue
            meta = meta_lookup[col_name]
            current_val = input_data[col_name]

            if meta["type"] in ("numeric", "integer"):
                val_min = meta["min"]
                val_max = meta["max"]
                if val_min is None or val_max is None or val_min >= val_max:
                    continue

                curr_num = float(current_val) if current_val is not None else meta["median"]
                span = val_max - val_min

                # Probe 15 grid points across range
                test_points = np.linspace(val_min, val_max, 15)
                # Sort points by proximity to current value
                test_points = sorted(test_points, key=lambda x: abs(x - curr_num))

                for candidate in test_points:
                    candidate_clean = int(round(candidate)) if meta["type"] == "integer" else round(float(candidate), 4)
                    if candidate_clean == curr_num:
                        continue

                    perturbed = dict(input_data)
                    perturbed[col_name] = candidate_clean
                    result = predict_with_explanation(pipeline, perturbed, problem_type)

                    is_flip = (
                        (result["prediction"] == target_class)
                        if target_class is not None
                        else (result["prediction"] != current_pred)
                    )

                    if is_flip:
                        delta = candidate_clean - curr_num
                        pct = round((delta / (curr_num if curr_num != 0 else 1.0)) * 100, 1)
                        sign = "+" if delta > 0 else ""
                        counterfactuals.append({
                            "feature": col_name,
                            "feature_type": meta["type"],
                            "current_value": current_val,
                            "proposed_value": candidate_clean,
                            "delta": f"{sign}{round(delta, 2)} ({sign}{pct}%)",
                            "abs_cost": abs(delta) / (span if span > 0 else 1.0),
                            "projected_prediction": result["prediction"],
                            "projected_confidence": result["confidence"],
                            "action_text": f"Change {col_name} from {current_val} to {candidate_clean}",
                            "impact": f"Flips prediction to {result['prediction']} ({int((result['confidence'] or 0)*100)}% confidence)",
                        })
                        break

            elif meta["type"] == "categorical" and meta["categories"]:
                for cat in meta["categories"]:
                    if str(cat) == str(current_val):
                        continue
                    perturbed = dict(input_data)
                    perturbed[col_name] = cat
                    result = predict_with_explanation(pipeline, perturbed, problem_type)

                    is_flip = (
                        (result["prediction"] == target_class)
                        if target_class is not None
                        else (result["prediction"] != current_pred)
                    )

                    if is_flip:
                        counterfactuals.append({
                            "feature": col_name,
                            "feature_type": "categorical",
                            "current_value": current_val,
                            "proposed_value": cat,
                            "delta": f"Switch category to '{cat}'",
                            "abs_cost": 0.5,  # Moderate categorical switch penalty
                            "projected_prediction": result["prediction"],
                            "projected_confidence": result["confidence"],
                            "action_text": f"Switch {col_name} to '{cat}'",
                            "impact": f"Flips prediction to {result['prediction']}",
                        })
                        break

        # Sort counterfactuals by minimal disruption (abs_cost)
        counterfactuals.sort(key=lambda x: x["abs_cost"])

    else:
        # Regression: Sensitivity & Target shift elasticity
        curr_pred_num = float(current_pred) if current_pred is not None else 0.0

        for col_name in ordered_cols:
            if col_name not in meta_lookup or col_name not in input_data:
                continue
            meta = meta_lookup[col_name]
            current_val = input_data[col_name]

            if meta["type"] in ("numeric", "integer"):
                curr_num = float(current_val) if current_val is not None else meta["median"]
                val_min = meta["min"]
                val_max = meta["max"]

                for pct_shift in [0.15, -0.15]:
                    shift_val = curr_num * (1.0 + pct_shift)
                    if val_min is not None and shift_val < val_min:
                        shift_val = val_min
                    if val_max is not None and shift_val > val_max:
                        shift_val = val_max

                    clean_shift = int(round(shift_val)) if meta["type"] == "integer" else round(shift_val, 4)
                    if clean_shift == curr_num:
                        continue

                    perturbed = dict(input_data)
                    perturbed[col_name] = clean_shift
                    result = predict_with_explanation(pipeline, perturbed, problem_type)
                    new_pred_num = float(result["prediction"])
                    pred_delta = new_pred_num - curr_pred_num

                    counterfactuals.append({
                        "feature": col_name,
                        "feature_type": meta["type"],
                        "current_value": current_val,
                        "proposed_value": clean_shift,
                        "delta": f"{'+' if pct_shift > 0 else ''}{int(pct_shift*100)}%",
                        "abs_cost": abs(pct_shift),
                        "projected_prediction": round(new_pred_num, 4),
                        "projected_confidence": None,
                        "action_text": f"Shift {col_name} by {'+' if pct_shift > 0 else ''}{int(pct_shift*100)}% (to {clean_shift})",
                        "impact": f"Shifts target by {'+' if pred_delta > 0 else ''}{round(pred_delta, 2)}",
                    })

        counterfactuals.sort(key=lambda x: abs(float(x.get("projected_prediction", 0) or 0) - curr_pred_num), reverse=True)

    return counterfactuals[:max_recommendations]
