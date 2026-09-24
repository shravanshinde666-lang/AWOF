from sklearn.ensemble import RandomForestRegressor


def build() -> RandomForestRegressor:
    return RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1)
