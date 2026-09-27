import numpy as np

from skimage.color import rgb2lab

from src.compute import (
    RAG,
    compute_centroid_and_mean,
    build_bpt,
)

from loguru import logger


def compute_clustering(
    label_map_data: list[list[int]] | None, img_data: list[list[list[int]]] | None
) -> tuple[list[int] | None, list[float] | None]:
    if label_map_data is None:
        return None, None
    label_map = np.asarray(label_map_data)
    img = np.asarray(img_data, dtype=np.uint8)
    if img.ndim == 3 and img.shape[2] == 3:
        logger.info("Using Lab")
        img = rgb2lab(img)
    _, mean = compute_centroid_and_mean(label_map, img)
    rag = RAG.build(label_map, mean)
    parent = build_bpt(img, label_map, rag._adj_matrix)
    altitude = np.zeros(parent.shape, dtype=np.float64)
    altitude[rag.num_nodes :] = np.arange(
        parent.shape[0] - rag.num_nodes, dtype=np.float64
    )
    # parent, altitude = hierarchical_clustering(rag)
    return parent.astype(int).tolist(), altitude.astype(float).tolist()
