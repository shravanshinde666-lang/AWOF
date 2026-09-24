from sklearn.linear_model import Ridge


def build() -> Ridge:
    return Ridge(alpha=1.0, random_state=42)
