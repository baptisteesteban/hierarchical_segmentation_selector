import numpy as np
import base64
import gzip
import json
import tempfile

from dash import dcc
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from skimage.morphology import dilation, footprint_rectangle

from src.compute import LCA


@dataclass
class TreeInformation:
    parent: np.ndarray
    altitude: np.ndarray | None
    nodemap: np.ndarray
    img: np.ndarray
    selected_nodes: np.ndarray


def _encode_ndarray(array: np.ndarray) -> dict[str, Any]:
    contiguous_array = np.ascontiguousarray(array)
    encoded_data = base64.b64encode(contiguous_array.tobytes()).decode("ascii")
    return {
        "dtype": contiguous_array.dtype.str,
        "shape": list(contiguous_array.shape),
        "data": encoded_data,
    }


def _decode_ndarray(payload: dict[str, Any]) -> np.ndarray:
    raw_bytes = base64.b64decode(payload["data"])
    dtype = np.dtype(payload["dtype"])
    shape = tuple(payload["shape"])
    return np.frombuffer(raw_bytes, dtype=dtype).reshape(shape)


def export_tree_information(
    tree_information: TreeInformation, output_path: str | Path
) -> None:
    payload: dict[str, Any] = {
        "parent": _encode_ndarray(tree_information.parent),
        "altitude": (
            _encode_ndarray(tree_information.altitude)
            if tree_information.altitude is not None
            else None
        ),
        "nodemap": _encode_ndarray(tree_information.nodemap),
        "img": _encode_ndarray(tree_information.img),
        "selected_nodes": _encode_ndarray(tree_information.selected_nodes),
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(output_file, mode="wt", encoding="utf-8") as compressed_file:
        json.dump(payload, compressed_file, separators=(",", ":"))


def import_tree_information(input_path: str | Path) -> TreeInformation:
    input_file = Path(input_path)

    with gzip.open(input_file, mode="rt", encoding="utf-8") as compressed_file:
        payload: dict[str, Any] = json.load(compressed_file)

    altitude_payload = payload["altitude"]
    altitude = (
        _decode_ndarray(altitude_payload) if altitude_payload is not None else None
    )

    return TreeInformation(
        parent=_decode_ndarray(payload["parent"]),
        altitude=altitude,
        nodemap=_decode_ndarray(payload["nodemap"]),
        img=_decode_ndarray(payload["img"]),
        selected_nodes=_decode_ndarray(payload["selected_nodes"]),
    )


def download_tree_information(
    click: int | None,
    hierarchy_parent: list[int] | None,
    hierarchy_altitude: list[float] | None,
    label_map_data: list[list[int]] | None,
    image_data: list[list[list[int]]] | None,
    selected_regions_data: list[list[bool]] | None,
) -> dict[str, Any] | None:
    if click is None or click == 0:
        return None
    if hierarchy_parent is None or label_map_data is None or image_data is None:
        logger.error("Empty image")
        return None

    label_map = np.asarray(label_map_data)
    selected_nodes = np.array([], dtype=np.int64)
    if selected_regions_data is not None:
        selected_regions = np.asarray(selected_regions_data, dtype=bool)
        if selected_regions.shape == label_map.shape:
            selected_nodes = np.unique(label_map[selected_regions])

    tree_information = TreeInformation(
        parent=np.asarray(hierarchy_parent),
        altitude=np.asarray(hierarchy_altitude)
        if hierarchy_altitude is not None
        else None,
        nodemap=label_map,
        img=np.asarray(image_data),
        selected_nodes=selected_nodes,
    )

    with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as file:
        output_path = file.name

    try:
        export_tree_information(tree_information, output_path)
        with open(output_path, "rb") as exported_file:
            exported_bytes = exported_file.read()
    finally:
        Path(output_path).unlink(missing_ok=True)

    return dcc.send_bytes(exported_bytes, "tree_information.json.gz")


def upload_tree_information(
    content: str | None,
) -> tuple[
    list[list[list[int]]],
    list[list[int]],
    list[list[bool]],
    list[list[bool]],
    list[int],
    list[float] | None,
]:
    if content is None:
        raise ValueError("Missing uploaded tree content")

    _, encoded = content.split(",", 1)
    compressed_bytes = base64.b64decode(encoded)

    with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as file:
        input_path = file.name
        file.write(compressed_bytes)

    try:
        tree_information = import_tree_information(input_path)
    finally:
        Path(input_path).unlink(missing_ok=True)

    label_map = np.asarray(tree_information.nodemap)
    if label_map.ndim != 2:
        raise ValueError("Imported nodemap must be a 2D array")

    selected_regions = np.zeros_like(label_map, dtype=bool)
    if tree_information.selected_nodes.size > 0:
        selected_nodes = np.asarray(tree_information.selected_nodes, dtype=int)
        leaf_labels = np.unique(label_map).astype(int)
        leaf_label_set = set(leaf_labels.tolist())
        expanded_selected_labels: set[int] = set()

        parent_array = np.asarray(tree_information.parent, dtype=int)
        try:
            lca = LCA(parent_array.tolist())
        except ValueError:
            lca = None

        for node in selected_nodes.tolist():
            if node in leaf_label_set:
                expanded_selected_labels.add(node)
                continue

            if lca is None or node < 0 or node >= len(parent_array):
                continue

            for label in leaf_label_set:
                if lca.is_ancestor(node, label):
                    expanded_selected_labels.add(label)

        if expanded_selected_labels:
            selected_regions = np.isin(label_map, list(expanded_selected_labels))

    borders = label_map != dilation(label_map, footprint_rectangle((3, 3)))

    altitude = (
        np.asarray(tree_information.altitude, dtype=float).tolist()
        if tree_information.altitude is not None
        else None
    )

    return (
        np.asarray(tree_information.img).tolist(),
        label_map.tolist(),
        selected_regions.tolist(),
        borders.tolist(),
        np.asarray(tree_information.parent, dtype=int).tolist(),
        altitude,
    )
