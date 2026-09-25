from typing import Any

import numpy as np

from dash import ctx


def select_region(
    click: dict[str, Any] | None,
    borders: list[list[bool]] | None,
    selected_regions: list[list[bool]] | None,
    label_map: list[list[int]] | None,
) -> list[list[bool]] | None:
    if borders is None or label_map is None:
        return None

    label_map_np = np.asarray(label_map)
    selected_regions_np = np.zeros_like(label_map_np, dtype=bool)

    if selected_regions is not None:
        selected_regions_candidate = np.asarray(selected_regions, dtype=bool)
        if selected_regions_candidate.shape == selected_regions_np.shape:
            selected_regions_np = selected_regions_candidate

    if ctx.triggered_id == "image-graph" and click is not None:
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
