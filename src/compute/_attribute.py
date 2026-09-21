import numpy as np
from numba import njit

@njit
def _compute_attributes(label_map: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    N = label_map.max() + 1
    sum_p = np.zeros((N, 2), dtype=np.uint32)
    area = np.zeros((N,), dtype=np.uint32)

    for l in range(label_map.shape[0]):
        for c in range(label_map.shape[1]):
            lbl = label_map[l, c]
            sum_p[lbl, 0] += l
            sum_p[lbl, 1] += c
            area[lbl] += 1

    return sum_p, area

def compute_centroid(label_map: np.ndarray) -> np.ndarray:
    sum_p, area = _compute_attributes(label_map)
    return sum_p / area[:, None]