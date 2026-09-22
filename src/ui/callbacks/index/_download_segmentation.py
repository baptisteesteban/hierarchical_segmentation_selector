import numpy as np
from imageio.v3 import imwrite

from dash import dcc

from io import BytesIO

def download_segmentation(click: dict, selected_regions_data: list) -> dict:
    if selected_regions_data is None:
        return None
    selected_regions = np.asarray(selected_regions_data)
    buffer = BytesIO()
    imwrite(buffer, selected_regions, extension=".png")
    return dcc.send_bytes(buffer.getvalue(), "segmentation.png")