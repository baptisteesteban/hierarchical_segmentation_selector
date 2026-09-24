from io import BytesIO
from typing import Any

import numpy as np
from dash import dcc
from imageio.v3 import imwrite


def download_segmentation(
    click: int, selected_regions_data: list[list[bool]] | None
) -> dict[str, Any] | None:
    if selected_regions_data is None or click == 0:
        return None
    selected_regions = np.asarray(selected_regions_data)
    buffer = BytesIO()
    imwrite(buffer, selected_regions, extension=".png")
    return dcc.send_bytes(buffer.getvalue(), "segmentation.png")
