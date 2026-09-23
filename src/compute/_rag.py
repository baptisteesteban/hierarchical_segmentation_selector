import numpy as np
from numba import njit

@njit
def _build_rag(label_map: np.ndarray, region_model: np.ndarray) -> np.ndarray:
    DL = (0, -1, 0, 1)
    DC = (-1, 0, 1, 0)

    N = label_map.max() + 1
    res = np.full((N, N), -1, dtype=np.float32)

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
                    res[a, b] = res[b, a] = np.linalg.norm(region_model[a] - region_model[b])

    return res

class RAG:
    def __init__(self, adj_matrix: np.ndarray, region_model: np.ndarray):
        self._adj_matrix = adj_matrix
        self._region_model = region_model

    @property
    def num_nodes(self) -> int:
        return self._adj_matrix.shape[0]

    def edge_weight(self, a: int, b: int):
        assert a >= 0 and b >= 0 and a < self.num_nodes and b < self.num_nodes
        return self._adj_matrix[a, b]

    def node_weight(self, n: int):
        return self._region_model[n]

    @staticmethod
    def build(label_map: np.ndarray, region_model: np.ndarray) -> "RAG":
        adj_mat = _build_rag(label_map, region_model)
        return RAG(adj_mat, region_model)

    def process_rag_for_display(self, centroid: np.ndarray) -> np.ndarray:
        res = []

        for n in range(centroid.shape[0]):
            for d in range(n, centroid.shape[0]):
                if self._adj_matrix[n, d] >= 0:
                    res.append([
                        centroid[n, 0],
                        centroid[n, 1],
                        centroid[d, 0],
                        centroid[d, 1],
                        self._adj_matrix[n, d]
                    ])

        return np.asarray(res)