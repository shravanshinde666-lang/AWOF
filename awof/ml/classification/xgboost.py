def build():
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # Optional dependency; never silently substitute another model.
        raise RuntimeError("XGBoost is unavailable because the optional package is not installed.") from exc
    return XGBClassifier(random_state=42, eval_metric="logloss")
