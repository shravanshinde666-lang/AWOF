from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .capability_registry import CAPABILITIES
from .rules import score_rules
from .thresholds import ALGORITHM_VERSION, OPTIONAL_THRESHOLD, RUN_THRESHOLD, decision_for


class ACSAScorer:
    def __init__(self, profile: dict[str, Any], configuration: dict[str, Any], dataframe: pd.DataFrame | None = None) -> None:
        self.profile, self.configuration, self.dataframe = profile, configuration, dataframe

    def generate(self) -> dict[str, Any]:
        values = score_rules(self.profile, self.configuration, self.dataframe)
        capabilities = []
        for definition in CAPABILITIES:
            score, signals, reasons = values[definition.id]
            capabilities.append({"id": definition.id, "label": definition.label, "description": definition.description, "category": definition.category, "score": score, "decision": decision_for(score), "reasons": reasons, "signals": signals})
        return {
            "dataset_id": self.configuration["dataset_id"], "algorithm": "Adaptive Capability Scoring Algorithm",
            "algorithm_version": ALGORITHM_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(),
            "business_objective": self.configuration["business_objective"], "problem_type": self.configuration["problem_type"],
            "thresholds": {"run": RUN_THRESHOLD, "optional": OPTIONAL_THRESHOLD, "skip_below": OPTIONAL_THRESHOLD},
            "capabilities": capabilities,
            "summary": {"total_capabilities": len(capabilities), "run_count": sum(c["decision"] == "run" for c in capabilities), "optional_count": sum(c["decision"] == "optional" for c in capabilities), "skip_count": sum(c["decision"] == "skip" for c in capabilities)},
        }
