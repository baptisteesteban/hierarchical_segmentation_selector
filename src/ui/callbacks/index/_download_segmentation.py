import numpy as np
from imageio.v3 import imwrite

from dash import dcc
from typing import Any

from io import BytesIO

def download_segmentation(click: int, selected_regions_data: list[list[bool]] | None) -> dict[str, Any] | None:
    if selected_regions_data is None or click == 0:
        return None
    selected_regions = np.asarray(selected_regions_data)
    buffer = BytesIO()
    imwrite(buffer, selected_regions, extension=".png")
    return dcc.send_bytes(buffer.getvalue(), "segmentation.png")