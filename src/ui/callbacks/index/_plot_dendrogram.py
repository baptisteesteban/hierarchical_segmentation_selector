import plotly.graph_objects as go

from loguru import logger

from typing import Any


def plot_dendrogram(parents: list[int] | None, altitude: list[Any] | None) -> go.Figure:
    if parents is None or altitude is None:
        return go.Figure()

    fig = go.Figure()

    # Build node positions using a recursive layout algorithm
    node_positions = {}  # Maps node index to (x, y) coordinates

    def get_leaves(node: int) -> list[int]:
        """Get all leaf nodes (indices < len(parents)) under a given node."""
        if node < len([p for p in parents if p != -1]):
            # This is a leaf node
            return [node]

        leaves = []
        for i, p in enumerate(parents):
            if p == node:
                leaves.extend(get_leaves(i))
        return leaves

    def layout_node(node: int, min_x: float, max_x: float) -> tuple[float, float]:
        """
        Recursively layout nodes and return their position.
        Returns (x, y) where y is the altitude.
        """
        if node in node_positions:
            return node_positions[node]

        # Find children of this node
        children = [i for i, p in enumerate(parents) if p == node]

        if not children:
            # Leaf node - place at x position, y = 0
            x = (min_x + max_x) / 2
            y = 0
            node_positions[node] = (x, y)
            return (x, y)

        # Non-leaf node - position children and connect them
        child_positions = []
        segment_size = (max_x - min_x) / len(children)

        for i, child in enumerate(children):
            child_min = min_x + i * segment_size
            child_max = min_x + (i + 1) * segment_size
            child_x, child_y = layout_node(child, child_min, child_max)
            child_positions.append((child_x, child_y))

        # Position this node at the center of its children, at its altitude
        x = (min_x + max_x) / 2
        y = altitude[node] if node < len(altitude) else 0
        node_positions[node] = (x, y)

        return (x, y)

    # Find the root node(s)
    roots = [i for i, p in enumerate(parents) if p == -1]

    if not roots:
        logger.warning("No root node found in dendrogram")
        return fig

    # Layout from root
    num_leaves = sum(
        1
        for i in range(len(parents))
        if i < len(parents) and all(parents[j] != i for j in range(len(parents)))
    )
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

                # Draw vertical line from child to parent
                fig.add_trace(
                    go.Scatter(
                        x=[child_x, child_x, parent_x],
                        y=[child_y, parent_y, parent_y],
                        mode="lines",
                        line=dict(color="darkblue", width=1),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

    # Add leaf nodes as points
    leaf_nodes = [
        i
        for i in range(len(parents))
        if all(parents[j] != i for j in range(len(parents)))
    ]
    leaf_x = [node_positions[node][0] for node in leaf_nodes if node in node_positions]
    leaf_y = [node_positions[node][1] for node in leaf_nodes if node in node_positions]

    fig.add_trace(
        go.Scatter(
            x=leaf_x,
            y=leaf_y,
            mode="markers",
            marker=dict(size=6, color="darkblue"),
            text=[f"Region {i}" for i in leaf_nodes],
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
