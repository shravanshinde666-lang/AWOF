def build():
    try:
        from xgboost import XGBRegressor
    except ImportError as exc:
        raise RuntimeError("XGBoost is unavailable because the optional package is not installed.") from exc
    return XGBRegressor(random_state=42, objective="reg:squarederror")
