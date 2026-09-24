ALGORITHM_VERSION = "ACSA-1.0"
RUN_THRESHOLD = 0.70
OPTIONAL_THRESHOLD = 0.40
MAX_MISSING_PERCENTAGE = 50.0
MAX_DUPLICATE_PERCENTAGE = 20.0
MAX_OUTLIER_PERCENTAGE = 20.0
HIGH_CORRELATION = 0.80

def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)

def decision_for(score: float) -> str:
    if score >= RUN_THRESHOLD:
        return "run"
    if score >= OPTIONAL_THRESHOLD:
        return "optional"
    return "skip"
