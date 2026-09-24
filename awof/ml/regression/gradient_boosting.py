from sklearn.ensemble import GradientBoostingRegressor


def build() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(random_state=42)
