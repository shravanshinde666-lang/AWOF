"""AMRA ranking and Top-K selection."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .model_registry import MODEL_REGISTRY, models_for, top_k_for
from .suitability import build_signals, score_model


class AMRARecommender:
    algorithm = "AMRA"
    algorithm_version = "AMRA-1.0"

    def recommend(
        self,
        profile: dict[str, Any],
        configuration: dict[str, Any],
        execution: dict[str, Any],
        dataframe: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        problem_type = configuration["problem_type"]
        signals = build_signals(profile, configuration, execution, dataframe)
        scored: list[dict[str, Any]] = []
        for registry_order, model in enumerate(models_for(problem_type)):
            if not model["available"]:
                scored.append({
                    "model_id": model["id"], "label": model["label"], "score": 0.0,
                    "rank": None, "decision": "not_selected", "reasons": ["Unavailable: the optional XGBoost package is not installed."],
                    "signals": {"availability": "unavailable"}, "estimated_complexity": model["training_complexity"],
                    "available": False, "registry_order": registry_order,
                })
                continue
            score, reasons = score_model(model, signals)
            scored.append({
                "model_id": model["id"], "label": model["label"], "score": score,
                "rank": None, "decision": "candidate", "reasons": reasons, "signals": signals.copy(),
                "estimated_complexity": model["training_complexity"], "available": True, "registry_order": registry_order,
            })

        available = sorted((item for item in scored if item["available"]), key=lambda item: (-item["score"], item["registry_order"]))
        for rank, item in enumerate(available, start=1):
            item["rank"] = rank
            item["decision"] = "recommended" if rank <= top_k_for(problem_type) else "candidate" if item["score"] >= 0.45 else "not_selected"
        results = sorted(scored, key=lambda item: (item["rank"] is None, item["rank"] or 10_000, item["registry_order"]))
        for item in results:
            item.pop("registry_order")
        incompatible_models = [
            {
                "model_id": model["id"], "label": model["label"], "problem_type": model["problem_type"],
                "score": 0.0, "rank": None, "decision": "incompatible",
                "reasons": [f"This model is for {model['problem_type']}, not the configured {problem_type} task, so AMRA did not score it."],
            }
            for model in MODEL_REGISTRY if model["problem_type"] != problem_type
        ]
        return {
            "dataset_id": configuration["dataset_id"], "algorithm": self.algorithm, "algorithm_version": self.algorithm_version,
            "problem_type": problem_type, "models": results, "signals": signals,
            "incompatible_models": incompatible_models,
            "summary": {
                "models_evaluated": len(results),
                "models_recommended": sum(item["decision"] == "recommended" for item in results),
                "top_k": top_k_for(problem_type),
                "unavailable_models": [item["model_id"] for item in results if not item["available"]],
            },
        }
