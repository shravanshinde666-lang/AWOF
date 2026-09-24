from sklearn.cluster import KMeans


def build(n_clusters: int) -> KMeans:
    return KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
