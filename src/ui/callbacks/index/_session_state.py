from typing import Literal, TypedDict

from ._compute_clustering import compute_clustering
from ._compute_label_map import compute_label_map
from ._import_export import upload_tree_information
from ._load_image import load_image


type ImageData = list[list[list[int]]]
type LabelMapData = list[list[int]]
type MaskData = list[list[bool]]


class UploadedImageSource(TypedDict):
    kind: Literal["image"]
    image_data: ImageData


class UploadedTreeSource(TypedDict):
    kind: Literal["tree"]
    image_data: ImageData
    label_map: LabelMapData
    selected_regions: MaskData
    border: MaskData
    hierarchy_parent: list[int]
    hierarchy_altitude: list[float] | None


type SessionSource = UploadedImageSource | UploadedTreeSource


class SessionState(TypedDict):
    image_data: ImageData | None
    label_map: LabelMapData | None
    border: MaskData | None
    hierarchy_parent: list[int] | None
    hierarchy_altitude: list[float] | None
    tree_import_mode: bool
    initial_selected_regions: MaskData | None


def empty_session_state() -> SessionState:
    return {
        "image_data": None,
        "label_map": None,
        "border": None,
        "hierarchy_parent": None,
        "hierarchy_altitude": None,
        "tree_import_mode": False,
        "initial_selected_regions": None,
    }


def load_session_source(
    triggered_id: str | None,
    image_contents: str | None,
    tree_contents: str | None,
) -> SessionSource | None:
    if triggered_id == "upload-image":
        if image_contents is None:
            return None
        image_source: UploadedImageSource = {
            "kind": "image",
            "image_data": load_image(image_contents),
        }
        return image_source

    if triggered_id == "upload-tree":
        image_data, label_map, selected_regions, border, parent, altitude = (
            upload_tree_information(tree_contents)
        )
        tree_source: UploadedTreeSource = {
            "kind": "tree",
            "image_data": image_data,
            "label_map": label_map,
            "selected_regions": selected_regions,
            "border": border,
            "hierarchy_parent": parent,
            "hierarchy_altitude": altitude,
        }
        return tree_source

    return None


def materialize_session_state(
    session_source: SessionSource | None,
    n_segments: int | None,
    compactness: float | None,
) -> SessionState:
    if session_source is None:
        return empty_session_state()

    if session_source["kind"] == "tree":
        return {
            "image_data": session_source["image_data"],
            "label_map": session_source["label_map"],
            "border": session_source["border"],
            "hierarchy_parent": session_source["hierarchy_parent"],
            "hierarchy_altitude": session_source["hierarchy_altitude"],
            "tree_import_mode": True,
            "initial_selected_regions": session_source["selected_regions"],
        }

    label_map, border = compute_label_map(
        session_source["image_data"],
        n_segments,
        compactness,
    )
    hierarchy_parent, hierarchy_altitude = compute_clustering(
        label_map,
        session_source["image_data"],
    )
    return {
        "image_data": session_source["image_data"],
        "label_map": label_map,
        "border": border,
        "hierarchy_parent": hierarchy_parent,
        "hierarchy_altitude": hierarchy_altitude,
        "tree_import_mode": False,
        "initial_selected_regions": None,
    }
