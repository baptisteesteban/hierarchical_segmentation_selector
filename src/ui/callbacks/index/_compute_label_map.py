import numpy as np
from skimage.segmentation import slic
from skimage.morphology import dilation, footprint_rectangle

from loguru import logger

def compute_label_map(image_data: list, n_segments: int, compactness: float) -> tuple[list, list]:
    img = np.asarray(image_data)

    N = img.shape[0] * img.shape[1]
    if n_segments is None or n_segments < 1 or n_segments > N:
        logger.error(f"Invalid number of segment (Got {n_segments}, expected in [1 - {N}])")
        return None, None

    if compactness is None or compactness <= 0:
        logger.error("Compactness must be strictly positive")
        return None, None

    segments = slic(img, n_segments=n_segments, compactness=compactness, start_label=0)
    logger.info(f"SLIC computed with {n_segments} segments (Got {segments.max()} segments)")
    dil = dilation(segments, footprint_rectangle((3, 3)))
    borders = segments != dil

    return segments.tolist(), borders.tolist()