from imageio.v3 import imread

import base64


def load_image(content: str) -> list[list[list[int]]]:
    _, encoded = content.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    img = imread(image_bytes)
    if img.ndim == 2:
        img = img[:, :, None]
        img = img.repeat(3, axis=2)

    return img.tolist()
