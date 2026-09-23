import numpy as np

from loguru import logger

from src.compute import RAG, compute_centroid_and_mean, hierarhical_clustering

def compute_clustering(label_map_data, img_data):
    if label_map_data is None:
        return None, None
    label_map = np.asarray(label_map_data)
    img = np.asarray(img_data, dtype=np.uint8)
    centroid, mean = compute_centroid_and_mean(label_map, img)
    rag = RAG.build(label_map, mean)
    parent, altitude = hierarhical_clustering(rag)
    return parent, altitude