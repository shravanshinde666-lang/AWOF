from sklearn.cluster import DBSCAN


def build() -> DBSCAN:
    return DBSCAN(eps=0.5, min_samples=5)
