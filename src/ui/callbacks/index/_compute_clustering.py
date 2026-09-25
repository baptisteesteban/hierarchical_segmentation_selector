import numpy as np

from src.compute import RAG, compute_centroid_and_mean, hierarchical_clustering


def compute_clustering(
    label_map_data: list[list[int]] | None, img_data: list[list[list[int]]] | None
) -> tuple[list[int] | None, list[float] | None]:
    if label_map_data is None:
        return None, None
    label_map = np.asarray(label_map_data)
    img = np.asarray(img_data, dtype=np.uint8)
    _, mean = compute_centroid_and_mean(label_map, img)
    rag = RAG.build(label_map, mean)
    parent, altitude = hierarchical_clustering(rag)
    return parent, altitude
