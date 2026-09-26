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
    if any(lca.children[label] for label in labels):
        raise ValueError("Selected labels must reference leaf regions")

    current = min(labels)
    for label in sorted(labels - {current}):
        current = lca(current, label)

    current_cluster = _leaf_descendants(parents, current)

    # If the current selection is only a partial subset under the LCA,
    # first snap to that minimal enclosing cluster before moving one level up.
    if labels != current_cluster:
        return current_cluster

    parent = parents[current]
    if parent == -1:
        return current_cluster
    return _leaf_descendants(parents, parent)


def select_region(
    click: dict[str, Any] | None,
    selected_regions: list[list[bool]] | None,
    label_map: list[list[int]] | None,
    image_data: list[list[list[int]]] | None = None,
    triggered_id: str | None = None,
    parents: list[int] | None = None,
) -> tuple[list[list[bool]] | None, str, bool]:
    if triggered_id == "reset-selection-button":
        if label_map is None:
            return None, "", False
        label_map_np = np.asarray(label_map)
        return np.zeros_like(label_map_np, dtype=bool).tolist(), "", False

    if triggered_id in {
        "image-data",
        "border-data",
        "n-segments-input",
        "compactness-input",
    }:
        return None, "", False

    if triggered_id == "parent-region-button":
        if selected_regions is None or label_map is None:
            return None, "No selection is available to expand.", True

        selected_mask = np.asarray(selected_regions, dtype=bool)
        label_map_np = np.asarray(label_map)
        if selected_mask.shape != label_map_np.shape:
            return (
                selected_regions,
                "Selection is out of sync with the current segmentation. Recompute segmentation or reset selection.",
                True,
            )

        selected_labels = [
            int(label) for label in np.unique(label_map_np[selected_mask]).tolist()
        ]
        if not selected_labels:
            return selected_regions, "Select at least one region first.", True
        if parents is None:
            return selected_regions, "Hierarchy is not available yet.", True

        try:
            next_labels = select_parent_cluster(selected_labels, parents)
        except ValueError as exc:
            return selected_regions, str(exc), True

        selected_regions_np = np.zeros_like(label_map_np, dtype=bool)
        for label in next_labels:
            selected_regions_np[label_map_np == int(label)] = True
        return selected_regions_np.tolist(), "", False

    if image_data is None or label_map is None:
        return None, "", False

    label_map_np = np.asarray(label_map)
    selected_regions_np = np.zeros_like(label_map_np, dtype=bool)

    if selected_regions is not None:
        selected_regions_candidate = np.asarray(selected_regions, dtype=bool)
        if selected_regions_candidate.shape == selected_regions_np.shape:
            selected_regions_np = selected_regions_candidate

    if triggered_id == "image-graph" and click is not None:
        points = click.get("points", [])
        if not points:
            return selected_regions_np.tolist(), "", False

        data = points[0]
        x = int(data["x"])
        y = int(data["y"])

        if y < 0 or x < 0 or y >= label_map_np.shape[0] or x >= label_map_np.shape[1]:
            return selected_regions_np.tolist(), "", False

        raw_label = data.get("customdata")
        if raw_label is None:
            lbl = int(label_map_np[y, x])
        else:
            lbl = int(raw_label)

        if selected_regions_np[y, x]:
            selected_regions_np[label_map_np == lbl] = False
        else:
            selected_regions_np[label_map_np == lbl] = True

    return selected_regions_np.tolist(), "", False
