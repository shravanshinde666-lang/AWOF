from sklearn.ensemble import GradientBoostingClassifier


def build() -> GradientBoostingClassifier:
    return GradientBoostingClassifier(random_state=42)
