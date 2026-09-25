import numpy as np

from loguru import logger

import plotly.graph_objects as go


def display_image(
    image_data: list[list[list[int]]] | None,
    label_map: list[list[int]] | None,
    selected_regions: list[list[bool]] | None,
    border: list[list[bool]] | None,
    selected_color: str,
) -> go.Figure:
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

    if image_data is None:
        return go.Figure()

    img = np.array(image_data, dtype=np.uint8)
    if img.ndim != 3 or img.shape[2] != 3:
        logger.error("Invalid image data")
        return go.Figure()

    height, width = img.shape[:2]

    selected_mask = np.zeros((height, width), dtype=bool)
    if selected_regions is not None:
        selected_mask_candidate = np.asarray(selected_regions, dtype=bool)
        if selected_mask_candidate.shape == selected_mask.shape:
            selected_mask = selected_mask_candidate
        else:
            logger.warning(
                f"Ignoring selected regions with unexpected shape: {selected_mask_candidate.shape}"
            )

    border_mask = np.zeros((height, width), dtype=bool)
    if border is not None:
        border_mask_candidate = np.asarray(border, dtype=bool)
        if border_mask_candidate.shape == border_mask.shape:
            border_mask = border_mask_candidate
        else:
            logger.warning(
                f"Ignoring border data with unexpected shape: {border_mask_candidate.shape}"
            )

    red, green, blue = hex_to_rgb(selected_color)
    selection_rgba = f"rgba({red}, {green}, {blue}, 0.35)"
    border_rgba = f"rgba({red}, {green}, {blue}, 0.75)"
    selected_border_rgba = f"rgba({red}, {green}, {blue}, 1.0)"

    selection_overlay = selected_mask.astype(np.uint8)
    border_overlay = border_mask.astype(np.uint8)
    selected_border_overlay = np.logical_and(border_mask, selected_mask).astype(np.uint8)

    fig = go.Figure()
    if label_map is not None:
        label_map_np = np.asarray(label_map)
        fig.add_trace(
            go.Image(
                z=img,
                customdata=label_map_np,
                hovertemplate="Label: %{customdata}<extra></extra>",
            )
        )
    else:
        fig.add_trace(go.Image(z=img, hoverinfo="skip"))

    fig.add_trace(
        go.Heatmap(
            z=selection_overlay,
            zmin=0,
            zmax=1,
            colorscale=[[0.0, "rgba(0, 0, 0, 0)"], [1.0, selection_rgba]],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Heatmap(
            z=border_overlay,
            zmin=0,
            zmax=1,
            colorscale=[[0.0, "rgba(0, 0, 0, 0)"], [1.0, border_rgba]],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Heatmap(
            z=selected_border_overlay,
            zmin=0,
            zmax=1,
            colorscale=[[0.0, "rgba(0, 0, 0, 0)"], [1.0, selected_border_rgba]],
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(showlegend=False)
    return fig
