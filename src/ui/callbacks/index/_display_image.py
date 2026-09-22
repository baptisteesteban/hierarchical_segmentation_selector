import numpy as np

import plotly.graph_objects as go
import plotly.express as px

from loguru import logger

from src.compute import compute_centroid_and_mean, RAG

def display_image(image_data: list, label_map: list, selected_regions: list, border:list, selected_color: str) -> go.Figure:
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    if image_data is None:
        return go.Figure()

    img = np.array(image_data, dtype=np.uint8)
    displayed_img = img
    if img.ndim != 3 or img.shape[2] != 3:
        logger.error("Invalid image data")
        return go.Figure()

    if selected_regions is not None:
        displayed_np = np.asarray(selected_regions)
        displayed_np = np.logical_or(displayed_np, np.asarray(border))
        displayed_img[displayed_np] = hex_to_rgb(selected_color)

            
    fig = go.Figure()
    fig.add_trace(go.Image(z=displayed_img, hoverinfo="skip"))
    if label_map is not None:
        label_map_np = np.asarray(label_map)
        fig.add_trace(go.Heatmap(z=label_map_np, opacity=0, showscale=False, hovertemplate=None))

        logger.info("Computing information for RAG")
        centroid, mean = compute_centroid_and_mean(label_map_np, img)
        logger.info("Building RAG")
        rag = RAG.build(label_map_np, mean)
        logger.info("Computing information for RAG")
        lines = rag.process_rag_for_display(centroid)

        logger.info("Displaying RAG")
        w = lines[:, 4]
        colors = px.colors.sample_colorscale("Inferno", (w - w.min()) / (w.max() - w.min()))
                
        for i in range(len(lines)):
            x_line = [lines[i, 1], lines[i, 3]]
            y_line = [lines[i, 0], lines[i, 2]]
            fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", hoverinfo="skip", line=dict(color=colors[i])))

        fig.add_trace(go.Scatter(x=centroid[1:, 1], y=centroid[1:, 0], mode='markers', hoverinfo="skip", marker={"color": selected_color}))
    fig.update_layout(showlegend=False)
    return fig