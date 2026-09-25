import numpy as np
from numba import njit

from ._rag import RAG


@njit
def _find_root(parent: list[int], n: int) -> int:
    # Find root
    r = n
    while parent[r] >= 0:
        r = parent[r]

    # Path compression
    q = n
    while parent[q] >= 0:
        tmp = parent[q]
        parent[q] = r
        q = tmp

    return r


@njit
def _edges_from_rag(adj_mat: np.ndarray) -> list[tuple[int, int, float]]:
    edges = []

    for n in range(adj_mat.shape[0]):
        for d in range(n, adj_mat.shape[1]):
            if adj_mat[n, d] >= 0:
                edges.append((n, d, adj_mat[n, d]))

    return edges


def _kruskal(
    sorted_edges: list[tuple[int, int, float]], rag_num_nodes: int
) -> tuple[list[int], list[float]]:
    parent: list[int] = [-1 for _ in range(rag_num_nodes)]
    zpar: list[int] = [-1 for _ in range(rag_num_nodes)]
    alt: list[float] = [0.0 for _ in range(rag_num_nodes)]
    cur = rag_num_nodes

    for u, v, w in sorted_edges:
        ru = _find_root(zpar, u)
        rv = _find_root(zpar, v)
        if ru != rv:
            zpar.append(-1)
            parent.append(-1)
            alt.append(w)
            parent[ru] = parent[rv] = zpar[ru] = zpar[rv] = cur
            cur += 1

    return parent, alt


@njit
def _canonize(
    parent: list[int], altitude: list[float], rag_num_nodes: int
) -> tuple[list[int], list[float]]:
    qct_parent = parent.copy()
    qct_altitude = altitude.copy()

    # Collect all non-leaf, non-root nodes by decreasing order of altitude
    nodes_to_remove = []
    for n in range(rag_num_nodes):
        if qct_parent[n] >= 0:  # Not a root
            # Check if it's a non-leaf node (has children in original parent array)
            has_children = False
            for i in range(len(parent)):
                if i != n and parent[i] == n:
                    has_children = True
                    break
            if has_children:
                nodes_to_remove.append((qct_altitude[n], n))

    # Sort by altitude in decreasing order
    nodes_to_remove.sort(reverse=True)

    # Process each node to remove
    for _, n in nodes_to_remove:
        p = qct_parent[n]
        if p >= 0:
            # Redirect all children of n to its parent p
            for i in range(len(qct_parent)):
                if qct_parent[i] == n:
                    qct_parent[i] = p

    return qct_parent, qct_altitude


def hierarchical_clustering(rag: RAG) -> tuple[list[int], list[float]]:
    e = _edges_from_rag(rag._adj_matrix)
    e = sorted(e, key=lambda v: v[2])

    parent, altitude = _kruskal(e, rag.num_nodes)
    parent, altitude = _canonize(parent, altitude, rag.num_nodes)

    return parent, altitude
