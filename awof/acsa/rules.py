from typing import Any

import pandas as pd

from .thresholds import HIGH_CORRELATION, MAX_DUPLICATE_PERCENTAGE, MAX_MISSING_PERCENTAGE, MAX_OUTLIER_PERCENTAGE, clamp_score


def profile_signals(profile: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
    summary = profile["summary"]
    types = profile["column_types"]
    target = (configuration.get("target") or {}).get("column")
    feature_types = [item for item in types if item["column"] != target]
    columns = profile["columns"]
    numeric = [item for item in feature_types if item.get("broad_type") == "numerical"]
    categorical = [item for item in feature_types if item.get("broad_type") in {"categorical", "boolean"}]
    text = [item for item in feature_types if item.get("broad_type") == "text"]
    datetime = [item for item in feature_types if item.get("broad_type") == "datetime"]
    maximum_missing = max((float(columns[item["column"]]["missing"]["missing_percentage"]) for item in types), default=0.0)
    outlier_values = [float(columns[item["column"]]["outliers"]["outlier_percentage"]) for item in numeric if columns[item["column"]].get("outliers")]
    strong_correlations = sum(1 for pair in profile["correlations"]["pairs"] if abs(float(pair["correlation"])) >= HIGH_CORRELATION)
    return {
        "summary": summary, "types": types, "feature_types": feature_types, "numeric": numeric,
        "categorical": categorical, "text": text, "datetime": datetime, "target": target,
        "feature_count": len(feature_types), "maximum_missing_percentage": maximum_missing,
        "outlier_values": outlier_values, "strong_correlations": strong_correlations,
        "problem_type": configuration["problem_type"],
        "objective_id": configuration["business_objective"]["id"],
        "columns": columns,
    }


def score_rules(profile: dict[str, Any], configuration: dict[str, Any], dataframe: pd.DataFrame | None = None) -> dict[str, tuple[float, dict[str, Any], list[str]]]:
    s = profile_signals(profile, configuration)
    summary, features = s["summary"], max(s["feature_count"], 1)
    missing = clamp_score(.55 * min(summary["missing_percentage"] / MAX_MISSING_PERCENTAGE, 1) + .25 * min(summary["missing_cells"] / max(summary["total_cells"], 1) * 10, 1) + .20 * min(s["maximum_missing_percentage"] / 100, 1))
    duplicate = clamp_score(min(summary["duplicate_percentage"] / MAX_DUPLICATE_PERCENTAGE, 1))
    outlier_rates = s["outlier_values"]
    outlier = clamp_score((len([v for v in outlier_rates if v > 0]) / max(len(s["numeric"]), 1)) * .55 + (max(outlier_rates, default=0) / MAX_OUTLIER_PERCENTAGE) * .45)
    encoding = clamp_score((len(s["categorical"]) / features) * .70 + (.30 if s["problem_type"] in {"classification", "regression", "clustering"} and s["categorical"] else 0))
    numeric_ranges = [abs(float(s["columns"][item["column"]]["numeric_statistics"]["range"] or 0)) for item in s["numeric"] if s["columns"][item["column"]].get("numeric_statistics")]
    heterogeneous = 1.0 if len(numeric_ranges) > 1 and max(numeric_ranges, default=0) > min((v for v in numeric_ranges if v > 0), default=max(numeric_ranges, default=1)) * 10 else 0.0
    scaling = clamp_score((len(s["numeric"]) / features) * .35 + (.45 if s["problem_type"] == "clustering" else .20 if s["problem_type"] in {"classification", "regression"} else 0) + .20 * heterogeneous)
    constants = sum(bool(item.get("is_constant")) for item in s["feature_types"])
    identifiers = sum(bool(item.get("is_identifier_candidate")) for item in s["feature_types"])
    high_card = sum(item.get("cardinality") in {"high", "near_unique"} for item in s["feature_types"])
    selection = clamp_score(min(features / 50, 1) * .30 + (constants + identifiers + high_card) / features * .35 + min(s["strong_correlations"] / max(len(s["numeric"]), 1), 1) * .35)
    text_score = clamp_score(len(s["text"]) / features)
    temporal = clamp_score(len(s["datetime"]) / features)
    dimension = clamp_score(min(len(s["numeric"]) / 40, 1) * .45 + min(s["strong_correlations"] / max(len(s["numeric"]), 1), 1) * .35 + (.20 if s["problem_type"] == "clustering" else 0))
    cluster = .95 if s["objective_id"] == "segment_customers" else .10
    classification = .95 if s["problem_type"] == "classification" else .05
    regression = .95 if s["problem_type"] == "regression" else .05
    explain = .90 if s["problem_type"] in {"classification", "regression"} else .55 if s["problem_type"] == "clustering" else .25
    business = {"identify_risk": .90, "analyze_retention": .90, "optimize_revenue": .90, "predict_behavior": .60, "segment_customers": .25}[s["objective_id"]]
    imbalance, imbalance_signals = imbalance_score(s, dataframe)
    return {
        "missing_value_handling": (missing, {"overall_missing_percentage": summary["missing_percentage"], "maximum_column_missing_percentage": s["maximum_missing_percentage"]}, [f"Overall missingness is {summary['missing_percentage']:.2f}%."]),
        "duplicate_handling": (duplicate, {"duplicate_rows": summary["duplicate_rows"], "duplicate_percentage": summary["duplicate_percentage"]}, [f"{summary['duplicate_rows']} duplicate rows detected."]),
        "outlier_analysis": (outlier, {"numeric_columns": len(s["numeric"]), "columns_with_outliers": len([v for v in outlier_rates if v > 0]), "max_outlier_percentage": max(outlier_rates, default=0)}, ["IQR outlier signals were evaluated for numerical features."]),
        "encoding": (encoding, {"categorical_feature_columns": len(s["categorical"]), "feature_columns": s["feature_count"], "problem_type": s["problem_type"]}, ["Categorical features may require numerical representation for future workflows."]),
        "scaling": (scaling, {"numeric_feature_columns": len(s["numeric"]), "heterogeneous_ranges": bool(heterogeneous), "problem_type": s["problem_type"]}, ["Scaling relevance depends on task type and observed numerical ranges."]),
        "feature_selection": (selection, {"feature_columns": s["feature_count"], "constant_columns": constants, "identifier_candidates": identifiers, "high_cardinality_columns": high_card, "strong_correlations": s["strong_correlations"]}, ["Feature filtering signals include constants, identifiers, cardinality, and correlation."]),
        "imbalance_handling": (imbalance, imbalance_signals, ["Class distribution is evaluated only for classification targets."]),
        "text_analysis": (text_score, {"text_columns": len(s["text"]), "feature_columns": s["feature_count"]}, ["Free-form text columns were detected from the dataset profile."]),
        "temporal_analysis": (temporal, {"datetime_columns": len(s["datetime"]), "feature_columns": s["feature_count"]}, ["Datetime columns were detected from the dataset profile."]),
        "dimensionality_reduction": (dimension, {"numeric_feature_columns": len(s["numeric"]), "strong_correlations": s["strong_correlations"], "problem_type": s["problem_type"]}, ["Dimensionality signals use numerical width and correlation redundancy."]),
        "clustering": (cluster, {"business_objective": s["objective_id"], "problem_type": s["problem_type"]}, ["Customer segmentation directly requests a clustering workflow."]),
        "classification": (classification, {"problem_type": s["problem_type"]}, ["Classification is driven by the configured technical problem type."]),
        "regression": (regression, {"problem_type": s["problem_type"]}, ["Regression is driven by the configured technical problem type."]),
        "explainability": (explain, {"problem_type": s["problem_type"], "business_objective": s["objective_id"]}, ["Business-facing supervised decisions benefit from explanation."]),
        "business_prioritization": (business, {"business_objective": s["objective_id"]}, ["Business prioritization relevance is driven by the selected objective."]),
    }


def imbalance_score(signals: dict[str, Any], dataframe: pd.DataFrame | None) -> tuple[float, dict[str, Any]]:
    if signals["problem_type"] != "classification" or dataframe is None or not signals["target"]:
        return 0.0, {"problem_type": signals["problem_type"], "minority_ratio": None, "imbalance_ratio": None}
    values = dataframe[signals["target"]].dropna().value_counts()
    if len(values) < 2:
        return 0.0, {"class_count": int(len(values)), "minority_ratio": None, "imbalance_ratio": None}
    minority, majority = int(values.min()), int(values.max())
    ratio = minority / majority
    return clamp_score(1 - ratio), {"class_count": int(len(values)), "majority_count": majority, "minority_count": minority, "minority_ratio": ratio, "imbalance_ratio": majority / minority}
