import numpy as np

from heapq import heappush, heappop


class Accumulator:
    def __init__(self, is_grayscale: bool):
        self._area = 0
        self._sum = 0 if is_grayscale else np.zeros((3,), dtype=np.float64)
        self._is_grayscale = is_grayscale

    @property
    def area(self):
        return self._area

    @property
    def sum(self):
        return self._sum

    @property
    def mean(self):
        return self._sum / self._area

    def take(self, v):
        if isinstance(v, Accumulator):
            self._area += v._area
            self._sum += v._sum
        else:
            self._area += 1
            self._sum += v

    def __add__(self, other):
        new = Accumulator(self._is_grayscale)
        new.take(self)
        new.take(other)
        return new


def build_bpt(
    img: np.ndarray, initial_partition: np.ndarray, rag: np.ndarray
) -> np.ndarray:
    N = 2 * rag.shape[0] - 1
    heap = []
    valid_nodes = [True for _ in range(rag.shape[0])]
    rag_algo = np.full((N, N), -1, dtype=np.float64)

    accs = [Accumulator(img.ndim == 2) for _ in range(rag.shape[0])]
    for li in range(img.shape[0]):
        for c in range(img.shape[1]):
            accs[initial_partition[li, c]] += img[li, c]

    rag_algo = np.zeros((N, N))

    # Enqueue all edges in the heap
    for v1 in range(rag.shape[0]):
        for v2 in range(v1 + 1, rag.shape[0]):
            if rag[v1, v2] >= 0:
                union = accs[v1] + accs[v2]
                rag_algo[v1, v2] = rag_algo[v2, v1] = accs[v1].area * np.linalg.norm(
                    accs[v1].mean.astype(np.int16) - union.mean
                ) + accs[v2].area * np.linalg.norm(
                    accs[v2].mean.astype(np.int16) - union.mean
                )
                heappush(heap, (rag_algo[v1, v2], (v1, v2)))

    parent = np.zeros(N, dtype=np.int32)

    new_node = rag.shape[0]
    while len(heap) > 0:
        w, (v1, v2) = heappop(heap)
        # Lazy deletion
        if not valid_nodes[v1] or not valid_nodes[v2]:
            continue

        # Merge nodes v1 and v2
        parent[new_node] = -1
        parent[v1] = new_node
        parent[v2] = new_node
        valid_nodes.append(True)
        accs.append(accs[v1] + accs[v2])
        valid_nodes[v1] = valid_nodes[v2] = False
        for vn in range(new_node):
            union = accs[new_node] + accs[vn]
            if rag_algo[v1, vn] > 0:
                rag_algo[new_node, vn] = rag_algo[vn, new_node] = accs[
                    vn
                ].area * np.linalg.norm(
                    accs[vn].mean.astype(np.int16) - union.mean
                ) + accs[new_node].area * np.linalg.norm(
                    accs[new_node].mean.astype(np.int16) - union.mean
                )
                heappush(heap, (rag_algo[new_node, vn], (new_node, vn)))
            if rag_algo[v2, vn] > 0:
                rag_algo[new_node, vn] = rag_algo[vn, new_node] = accs[
                    vn
                ].area * np.linalg.norm(
                    accs[vn].mean.astype(np.int16) - union.mean
                ) + accs[new_node].area * np.linalg.norm(
                    accs[new_node].mean.astype(np.int16) - union.mean
                )
                heappush(heap, (rag_algo[new_node, vn], (new_node, vn)))

        new_node += 1

    return parent
