import numpy as np
from numba import njit

from ._rag import RAG

#@njit
def _find_root(parent: np.ndarray, n: int) -> int:
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

#@njit
def _edges_from_rag(adj_mat: np.ndarray) -> list:
    edges = []

    for n in range(adj_mat.shape[0]):
        for d in range(n, adj_mat.shape[1]):
            if adj_mat[n, d] >= 0:
                edges.append([n, d, adj_mat[n, d]])

    return edges

def hierarhical_clustering(rag: RAG) -> list:
    e = _edges_from_rag(rag._adj_matrix)
    e = sorted(e, key=lambda v: v[2])

    parent = [-1 for _ in range(rag.num_nodes)]
    zpar = [-1 for _ in range(rag.num_nodes)]
    cur = rag.num_nodes

    for (u, v, _) in e:
        ru = _find_root(zpar, u)
        rv = _find_root(zpar, v)
        if ru != rv:
            zpar.append(-1)
            parent.append(-1)
            parent[ru] = parent[rv] = zpar[ru] = zpar[rv] = cur
            cur += 1

    return parent
