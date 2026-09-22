import plotly.graph_objects as go

from loguru import logger


def plot_dendrogram(parents):
    """
    Display the binary partition clustering hierarchy as a tree.
    
    Args:
        parents: List where parents[i] is the parent node index of node i.
                 Leaf nodes are indices 0 to n-1, internal nodes start from n.
                 Root node has parent value -1.
    
    Returns:
        A Plotly figure object displaying the tree hierarchy.
    """
    if not parents or len(parents) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No hierarchy data available")
        return fig
    
    parents = list(parents)
    n_leaves = (len(parents) + 1) // 2
    
    logger.debug(f"Tree: {len(parents)} total nodes, {n_leaves} leaves")
    
    # Build children map
    children_map = {}
    for i in range(len(parents)):
        parent_idx = parents[i]
        if parent_idx >= 0 and parent_idx < len(parents):
            if parent_idx not in children_map:
                children_map[parent_idx] = []
            children_map[parent_idx].append(i)
    
    # Find root
    root = None
    for i in range(n_leaves, len(parents)):
        if parents[i] == -1:
            root = i
            break
    if root is None:
        root = len(parents) - 1
    
    # Assign positions to nodes using tree layout
    node_x = {}
    node_y = {}
    
    def assign_positions(node, depth, left, right):
        """Assign x, y coordinates to node"""
        x = (left + right) / 2
        y = -depth
        node_x[node] = x
        node_y[node] = y
        
        if node in children_map:
            children = sorted(children_map[node])
            child_width = (right - left) / len(children)
            for i, child in enumerate(children):
                child_left = left + i * child_width
                child_right = child_left + child_width
                assign_positions(child, depth + 1, child_left, child_right)
    
    assign_positions(root, 0, 0, 100)
    
    # Prepare edges and nodes
    edge_x = []
    edge_y = []
    
    for node in range(len(parents)):
        parent_idx = parents[node]
        if parent_idx >= 0 and parent_idx in node_x:
            edge_x.append(node_x[parent_idx])
            edge_x.append(node_x[node])
            edge_x.append(None)
            edge_y.append(node_y[parent_idx])
            edge_y.append(node_y[node])
            edge_y.append(None)
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1.5, color='#1f77b4'),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Add nodes
    node_list = list(node_x.keys())
    node_x_list = [node_x[n] for n in node_list]
    node_y_list = [node_y[n] for n in node_list]
    
    leaf_mask = [n < n_leaves for n in node_list]
    
    # Leaf nodes
    leaf_indices = [i for i, is_leaf in enumerate(leaf_mask) if is_leaf]
    fig.add_trace(go.Scatter(
        x=[node_x_list[i] for i in leaf_indices],
        y=[node_y_list[i] for i in leaf_indices],
        mode='markers+text',
        marker=dict(size=10, color='#ff7f0e', line=dict(width=2, color='#d46700')),
        text=[f"S{node_list[i]}" for i in leaf_indices],
        textposition='middle center',
        textfont=dict(size=9, color='white', family='monospace'),
        hovertemplate='Segment %{text}<extra></extra>',
        showlegend=False
    ))
    
    # Internal nodes
    internal_indices = [i for i, is_leaf in enumerate(leaf_mask) if not is_leaf]
    if internal_indices:
        fig.add_trace(go.Scatter(
            x=[node_x_list[i] for i in internal_indices],
            y=[node_y_list[i] for i in internal_indices],
            mode='markers+text',
            marker=dict(size=8, color='#2ca02c', line=dict(width=1.5, color='#1d6b1d')),
            text=[f"N{node_list[i]}" for i in internal_indices],
            textposition='middle center',
            textfont=dict(size=8, color='white', family='monospace'),
            hovertemplate='Node %{text}<extra></extra>',
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title='Clustering Hierarchy Tree',
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis_title='',
        yaxis_title=''
    )
    
    return fig