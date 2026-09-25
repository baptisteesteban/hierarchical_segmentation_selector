from collections.abc import Iterable
from typing import Any

import numpy as np

from src.compute import LCA


def _leaf_descendants(parents: list[int], node: int) -> set[int]:
    """Return all leaf-region labels under a given merge node."""
    lca = LCA(parents)
    leaf_nodes = [idx for idx, children in enumerate(lca.children) if not children]
    if node in leaf_nodes:
        return {node}
    return {leaf for leaf in leaf_nodes if lca.is_ancestor(node, leaf)}


def select_parent_cluster(
    selected_labels: Iterable[int], parents: list[int]
) -> set[int]:
    """Return the leaf-region set represented by the parent of the current node.

    The current node is the LCA of the selected labels. The parent cluster is the
    merge node directly above that node in the hierarchy.
    """
    labels = {int(label) for label in selected_labels}
    if not labels:
        return set()

    if any(not 0 <= label < len(parents) for label in labels):
        raise ValueError("Selected label index out of bounds for the hierarchy")

    lca = LCA(parents)
    current = min(labels)
    for label in sorted(labels - {current}):
        current = lca(current, label)

    parent = parents[current]
    if parent == -1:
        return _leaf_descendants(parents, current)
    return _leaf_descendants(parents, parent)


def select_cluster_by_wheel(
    selected_labels: Iterable[int], parents: list[int], wheel_delta: int
) -> set[int]:
    """Move one step in the hierarchy according to the wheel direction.

    Positive wheel movement selects the parent region; negative movement selects
    the first child sub-region when available.
    """
    labels = {int(label) for label in selected_labels}
    if not labels:
        return set()

    if wheel_delta > 0:
        return select_parent_cluster(labels, parents)

    lca = LCA(parents)
    current = min(labels)
    for label in sorted(labels - {current}):
        current = lca(current, label)

    children = lca.children[current]
    if not children:
        return {current}
    return _leaf_descendants(parents, children[0])


def select_region(
    click: dict[str, Any] | None,
    borders: list[list[bool]] | None,
    selected_regions: list[list[bool]] | None,
    label_map: list[list[int]] | None,
    image_data: list[list[list[int]]] | None = None,
    triggered_id: str | None = None,
    parents: list[int] | None = None,
    wheel_data: dict[str, Any] | None = None,
) -> list[list[bool]] | None:
    if triggered_id in {
        "image-data",
        "border-data",
        "n-segments-input",
        "compactness-input",
    }:
        return None

    if image_data is None or label_map is None:
        return None

    label_map_np = np.asarray(label_map)
    selected_regions_np = np.zeros_like(label_map_np, dtype=bool)

    if selected_regions is not None:
        selected_regions_candidate = np.asarray(selected_regions, dtype=bool)
        if selected_regions_candidate.shape == selected_regions_np.shape:
            selected_regions_np = selected_regions_candidate

    if triggered_id == "dendrogram-wheel-data" and parents is not None:
        delta = int(wheel_data.get("delta", 0)) if wheel_data else 0
        if delta != 0:
            selected_labels = np.unique(label_map_np[selected_regions_np]).tolist()
            if not selected_labels:
                selected_labels = np.unique(label_map_np).tolist()
            next_labels = select_cluster_by_wheel(selected_labels, parents, delta)
            selected_regions_np[:] = False
            for label in next_labels:
                selected_regions_np[label_map_np == int(label)] = True
            return selected_regions_np.tolist()

    if triggered_id == "image-graph" and click is not None:
        points = click.get("points", [])
        if not points:
            return selected_regions_np.tolist()

        data = points[0]
        x = int(data["x"])
        y = int(data["y"])

        if y < 0 or x < 0 or y >= label_map_np.shape[0] or x >= label_map_np.shape[1]:
            return selected_regions_np.tolist()

        raw_label = data.get("customdata")
        if raw_label is None:
            lbl = int(label_map_np[y, x])
        else:
            lbl = int(raw_label)

        if selected_regions_np[y, x]:
            selected_regions_np[label_map_np == lbl] = False
        else:
            selected_regions_np[label_map_np == lbl] = True

    return selected_regions_np.tolist()
