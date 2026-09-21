import numpy as np
from numba import njit

@njit
def build_rag(label_map: np.ndarray) -> np.ndarray:
    DL = (0, -1, 0, 1)
    DC = (-1, 0, 1, 0)

    N = label_map.max() + 1
    res = np.zeros((N, N), dtype=np.uint8)

    for l in range(label_map.shape[0]):
        for c in range(label_map.shape[1]):
            for dl, dc in zip(DL, DC):
                nl = l + dl
                nc = c + dc
                if nl < 0 or nc < 0 or nl >= label_map.shape[0] or nc >= label_map.shape[1]:
                    continue
                a = label_map[l, c]
                b = label_map[nl, nc]
                if a != b:
                    res[a, b] = res[b, a] = 1

    return res