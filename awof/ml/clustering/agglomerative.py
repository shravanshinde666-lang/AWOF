from sklearn.cluster import AgglomerativeClustering


def build(n_clusters: int = 2) -> AgglomerativeClustering:
    return AgglomerativeClustering(n_clusters=n_clusters)
