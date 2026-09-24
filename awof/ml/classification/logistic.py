from sklearn.linear_model import LogisticRegression


def build() -> LogisticRegression:
    return LogisticRegression(max_iter=1_000, random_state=42)
