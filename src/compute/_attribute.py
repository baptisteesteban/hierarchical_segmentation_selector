import numpy as np


# @njit
def _compute_attributes(
    label_map: np.ndarray, img: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    N = label_map.max() + 1
    sum_p = np.zeros((N, 2), dtype=np.uint32)
    sum_v = None
    if img.ndim == 2:
        sum_v = np.zeros((N,), dtype=np.uint32)
    else:
        sum_v = np.zeros((N, 3), dtype=np.uint32)
    area = np.zeros((N,), dtype=np.uint32)

    for i in range(label_map.shape[0]):
        for c in range(label_map.shape[1]):
            lbl = label_map[i, c]
            sum_p[lbl, 0] += i
            sum_p[lbl, 1] += c
            sum_v[lbl] += img[i, c]
            area[lbl] += 1

    return sum_p, sum_v, area


def compute_centroid_and_mean(
    label_map: np.ndarray, img: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    sum_p, sum_v, area = _compute_attributes(label_map, img)
    return sum_p / area[:, None], sum_v / area[:, None]
