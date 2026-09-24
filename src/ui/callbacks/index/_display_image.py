import numpy as np

import plotly.graph_objects as go

from loguru import logger


def display_image(
    image_data: list[list[list[int]]] | None,
    label_map: list[list[int]] | None,
    selected_regions: list[list[bool]] | None,
    border: list[list[bool]],
    selected_color: str,
) -> go.Figure:
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

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
        fig.add_trace(
            go.Heatmap(z=label_map_np, opacity=0, showscale=False, hovertemplate=None)
        )
    fig.update_layout(showlegend=False)
    return fig
