import numpy as np

from dash import ctx
from typing import Any

def select_region(click: dict[str, Any] | None, borders: list[list[bool]], selected_regions: list[list[bool]] | None, label_map: list[list[int]]) -> list[list[bool]] | None:
    if borders is None:
        return None
    
    selected_regions_np = None
    if ctx.triggered_id == "image-graph" and click is not None:
        selected_regions_np = np.asarray(selected_regions)
        label_map_np = np.asarray(label_map)
        data = click["points"][0]
        x = int(data["x"])
        y = int(data["y"])
        lbl = int(data["z"])
        if selected_regions_np[y, x]:
            selected_regions_np[label_map_np == lbl] = False
        else:
            selected_regions_np[label_map_np == lbl] = True
    else:
        selected_regions_np = np.zeros_like(borders)
            
    return selected_regions_np.tolist()