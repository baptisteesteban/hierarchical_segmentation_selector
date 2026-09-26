from typing import Any

import plotly.graph_objects as go

from loguru import logger

from src.compute import LCA


def plot_dendrogram(
    parents: list[int] | None,
    altitude: list[Any] | None,
    selected_labels: list[int] | set[int] | None = None,
) -> go.Figure:
    if parents is None or altitude is None:
        return go.Figure()

    try:
        lca = LCA(parents)
    except ValueError as exc:
        logger.warning(f"Invalid hierarchy parent table: {exc}")
        return go.Figure()

    children = lca.children
    leaf_nodes = [
        node for node, node_children in enumerate(children) if not node_children
    ]
    leaf_node_set = set(leaf_nodes)

    fig = go.Figure()
    selected_leaf_nodes: set[int] = set()
    selected_branch_edges: set[tuple[int, int]] = set()
    depth_cache: dict[int, int] = {}
    leaf_descendants_cache: dict[int, set[int]] = {}

    def is_valid_node(node: int) -> bool:
        return 0 <= node < len(parents)

    def get_leaf_descendants(node: int) -> set[int]:
        if node in leaf_descendants_cache:
            return leaf_descendants_cache[node]
        if node in leaf_node_set:
            leaf_descendants_cache[node] = {node}
            return leaf_descendants_cache[node]
        leaf_descendants_cache[node] = {
            leaf for leaf in leaf_nodes if lca.is_ancestor(node, leaf)
        }
        return leaf_descendants_cache[node]

    def get_depth(node: int) -> int:
        if node in depth_cache:
            return depth_cache[node]

        depth = 0
        current = node
        while parents[current] != -1:
            depth += 1
            current = parents[current]
        depth_cache[node] = depth
        return depth

    def add_branch_edges_from(node: int, stop_at: int | None = None) -> None:
        current = node
        while current != -1 and (stop_at is None or current != stop_at):
            parent = parents[current]
            if parent != -1 and is_valid_node(parent):
                selected_branch_edges.add((current, parent))
            current = parent

    if selected_labels:
        selected_leaves: set[int] = set()
        for label in selected_labels:
            node = int(label)
            if not is_valid_node(node):
                continue

            for leaf in get_leaf_descendants(node):
                if not is_valid_node(leaf):
                    continue
                selected_leaves.add(leaf)

        if selected_leaves:
            selected_leaf_nodes = selected_leaves.copy()
            selected_leaf_set = selected_leaves.copy()

            # Build maximal fully selected regions. A region is fully selected
            # when all its descendant leaves are selected.
            fully_selected_nodes = {
                node
                for node in range(len(parents))
                if get_leaf_descendants(node).issubset(selected_leaf_set)
                and get_leaf_descendants(node)
            }

            maximal_selected_nodes = {
                node
                for node in fully_selected_nodes
                if parents[node] == -1 or parents[node] not in fully_selected_nodes
            }

            for node in sorted(maximal_selected_nodes, key=get_depth):
                if node in leaf_node_set:
                    continue
                for leaf in get_leaf_descendants(node):
                    add_branch_edges_from(leaf, stop_at=node)

    # Build node positions using a recursive layout algorithm
    node_positions = {}  # Maps node index to (x, y) coordinates

    def layout_node(node: int, min_x: float, max_x: float) -> tuple[float, float]:
        """
        Recursively layout nodes and return their position.
        Returns (x, y) where y is the altitude.
        """
        if node in node_positions:
            return node_positions[node]

        # Find children of this node
        node_children = children[node]

        if not node_children:
            # Leaf node - place at x position, y = 0
            x = (min_x + max_x) / 2
            y = 0
            node_positions[node] = (x, y)
            return (x, y)

        # Non-leaf node - position children and connect them
        segment_size = (max_x - min_x) / len(node_children)

        for i, child in enumerate(node_children):
            child_min = min_x + i * segment_size
            child_max = min_x + (i + 1) * segment_size
            layout_node(child, child_min, child_max)

        # Position this node at the center of its children, at its altitude
        x = (min_x + max_x) / 2
        y = altitude[node] if node < len(altitude) else 0
        node_positions[node] = (x, y)

        return (x, y)

    # Find the root node(s)
    roots = [lca.root]

    if not roots:
        logger.warning("No root node found in dendrogram")
        return fig

    # Layout from root
    num_leaves = len(leaf_nodes)
    if num_leaves == 0:
        num_leaves = len(parents)

    for root in roots:
        layout_node(root, 0, num_leaves)

    # Draw connections (lines) for all parent-child relationships
    for node_idx in range(len(parents)):
        if parents[node_idx] != -1:
            parent_idx = parents[node_idx]
            if node_idx in node_positions and parent_idx in node_positions:
                child_x, child_y = node_positions[node_idx]
                parent_x, parent_y = node_positions[parent_idx]
                edge_color = (
                    "#FF0000"
                    if (node_idx, parent_idx) in selected_branch_edges
                    else "darkblue"
                )

                # Draw vertical line from child to parent
                fig.add_trace(
                    go.Scatter(
                        x=[child_x, child_x, parent_x],
                        y=[child_y, parent_y, parent_y],
                        mode="lines",
                        line={"color": edge_color, "width": 1},
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

    # Add leaf nodes as points
    leaf_x = [node_positions[node][0] for node in leaf_nodes if node in node_positions]
    leaf_y = [node_positions[node][1] for node in leaf_nodes if node in node_positions]
    leaf_colors = [
        "#FF0000" if node in selected_leaf_nodes else "darkblue"
        for node in leaf_nodes
        if node in node_positions
    ]

    fig.add_trace(
        go.Scatter(
            x=leaf_x,
            y=leaf_y,
            mode="markers",
            marker={"size": 6, "color": leaf_colors},
            text=[f"Region {i}" for i in leaf_nodes if i in node_positions],
            hoverinfo="text",
            showlegend=False,
        )
    )

    # Update layout
    fig.update_layout(
        title="Hierarchical Clustering Dendrogram",
        xaxis_title="Regions",
        yaxis_title="Altitude (Merge Distance)",
        hovermode="closest",
        height=600,
        showlegend=False,
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True)

    return fig
