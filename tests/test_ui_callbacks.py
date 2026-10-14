import base64
import tempfile
import unittest

from io import BytesIO
from pathlib import Path

import numpy as np

from imageio.v3 import imwrite

from src.ui.callbacks.index._compute_clustering import compute_clustering
from src.ui.callbacks.index._compute_label_map import compute_label_map
from src.ui.callbacks.index._display_image import display_image
from src.ui.callbacks.index._download_segmentation import download_segmentation
from src.ui.callbacks.index._import_export import (
    TreeInformation,
    download_tree_information,
    export_tree_information,
    import_tree_information,
    upload_tree_information,
)
from src.ui.callbacks.index._load_image import load_image
from src.ui.callbacks.index._select_region import select_region


def _to_upload_content(image: np.ndarray) -> str:
    buffer = BytesIO()
    imwrite(buffer, image, extension=".png")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _to_tree_upload_content(tree: TreeInformation) -> str:
    with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as file:
        export_path = file.name

    try:
        export_tree_information(tree, export_path)
        encoded = base64.b64encode(Path(export_path).read_bytes()).decode("ascii")
    finally:
        Path(export_path).unlink(missing_ok=True)

    return f"data:application/gzip;base64,{encoded}"


class LoadImageCallbackTest(unittest.TestCase):
    def test_load_image_promotes_grayscale_to_rgb(self) -> None:
        gray = np.array([[10, 20], [30, 40]], dtype=np.uint8)
        loaded = np.asarray(load_image(_to_upload_content(gray)), dtype=np.uint8)

        self.assertEqual(loaded.shape, (2, 2, 3))
        self.assertTrue(np.array_equal(loaded[:, :, 0], gray))
        self.assertTrue(np.array_equal(loaded[:, :, 1], gray))
        self.assertTrue(np.array_equal(loaded[:, :, 2], gray))

    def test_load_image_keeps_rgb_shape(self) -> None:
        rgb = np.array(
            [
                [[255, 0, 0], [0, 255, 0]],
                [[0, 0, 255], [255, 255, 0]],
            ],
            dtype=np.uint8,
        )
        loaded = np.asarray(load_image(_to_upload_content(rgb)), dtype=np.uint8)

        self.assertEqual(loaded.shape, rgb.shape)
        self.assertTrue(np.array_equal(loaded, rgb))

    def test_load_image_rejects_malformed_content(self) -> None:
        with self.assertRaises(ValueError):
            load_image("not-a-data-uri")


class ComputeLabelMapCallbackTest(unittest.TestCase):
    def test_compute_label_map_rejects_invalid_parameters(self) -> None:
        image = np.zeros((4, 4, 3), dtype=np.uint8).tolist()

        self.assertEqual(compute_label_map(None, 2, 10.0), (None, None))
        self.assertEqual(compute_label_map(image, 0, 10.0), (None, None))
        self.assertEqual(compute_label_map(image, 99, 10.0), (None, None))
        self.assertEqual(compute_label_map(image, 2, 0.0), (None, None))

    def test_compute_label_map_returns_map_and_border(self) -> None:
        image = np.zeros((6, 6, 3), dtype=np.uint8)
        image[:3, :, :] = 255

        label_map, border = compute_label_map(image.tolist(), n_segments=4, compactness=5.0)

        self.assertIsNotNone(label_map)
        self.assertIsNotNone(border)

        label_map_np = np.asarray(label_map)
        border_np = np.asarray(border, dtype=bool)

        self.assertEqual(label_map_np.shape, (6, 6))
        self.assertEqual(border_np.shape, (6, 6))


class ComputeClusteringCallbackTest(unittest.TestCase):
    def test_compute_clustering_handles_missing_label_map(self) -> None:
        self.assertEqual(compute_clustering(None, None), (None, None))

    def test_compute_clustering_returns_valid_tree_shape(self) -> None:
        label_map = [[0, 0], [1, 1]]
        img = np.zeros((2, 2, 3), dtype=np.uint8).tolist()

        parent, altitude = compute_clustering(label_map, img)

        self.assertIsNotNone(parent)
        self.assertIsNotNone(altitude)
        assert parent is not None
        assert altitude is not None
        self.assertEqual(len(parent), 3)
        self.assertEqual(len(altitude), 3)
        self.assertEqual(parent.count(-1), 1)


class DisplayImageCallbackTest(unittest.TestCase):
    def test_display_image_with_missing_or_invalid_image(self) -> None:
        self.assertEqual(len(display_image(None, None, None, None, "#FF0000").data), 0)

        invalid = np.zeros((4, 4), dtype=np.uint8).tolist()
        fig = display_image(invalid, None, None, None, "#FF0000")
        self.assertEqual(len(fig.data), 0)

    def test_display_image_returns_expected_layers(self) -> None:
        image = np.zeros((3, 3, 3), dtype=np.uint8)
        label_map = np.array(
            [
                [0, 0, 1],
                [0, 2, 2],
                [3, 3, 3],
            ],
            dtype=int,
        )
        selected = np.array(
            [
                [True, True, False],
                [True, False, False],
                [False, False, False],
            ],
            dtype=bool,
        )
        border = np.zeros((3, 3), dtype=bool)
        border[:, 1] = True

        fig = display_image(
            image.tolist(),
            label_map.tolist(),
            selected.tolist(),
            border.tolist(),
            "#00FF00",
        )

        self.assertEqual(len(fig.data), 4)
        first_trace = fig.data[0]
        self.assertTrue(hasattr(first_trace, "customdata"))

    def test_display_image_ignores_shape_mismatch_for_overlays(self) -> None:
        image = np.zeros((3, 3, 3), dtype=np.uint8)
        label_map = np.zeros((3, 3), dtype=int)
        bad_selected = np.array([[True, False]], dtype=bool)
        bad_border = np.array([[True]], dtype=bool)

        fig = display_image(
            image.tolist(),
            label_map.tolist(),
            bad_selected.tolist(),
            bad_border.tolist(),
            "#FF0000",
        )

        self.assertEqual(len(fig.data), 4)
        selection_trace = fig.data[1]
        border_trace = fig.data[2]
        self.assertEqual(int(np.asarray(selection_trace.z).sum()), 0)
        self.assertEqual(int(np.asarray(border_trace.z).sum()), 0)


class DownloadSegmentationCallbackTest(unittest.TestCase):
    def test_download_segmentation_handles_missing_inputs(self) -> None:
        self.assertIsNone(download_segmentation(0, [[True]]))
        self.assertIsNone(download_segmentation(1, None))

    def test_download_segmentation_returns_download_payload(self) -> None:
        payload = download_segmentation(1, [[True, False], [False, True]])

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.get("filename"), "segmentation.png")
        self.assertIn("content", payload)


class SelectRegionCallbackTest(unittest.TestCase):
    def test_select_region_click_toggles_whole_label(self) -> None:
        label_map = np.array([[0, 0], [1, 1]], dtype=int)
        image = np.zeros((2, 2, 3), dtype=np.uint8).tolist()

        selected, message, is_open = select_region(
            click={"points": [{"x": 0, "y": 0, "customdata": 0}]},
            selected_regions=None,
            label_map=label_map.tolist(),
            image_data=image,
            triggered_id="image-graph",
            parents=[2, 2, -1],
        )

        self.assertEqual(message, "")
        self.assertFalse(is_open)
        self.assertEqual(
            selected,
            np.array([[True, True], [False, False]], dtype=bool).tolist(),
        )

    def test_select_region_reset_clears_selection(self) -> None:
        label_map = np.array([[0, 1], [2, 3]], dtype=int)

        selected, message, is_open = select_region(
            click=None,
            selected_regions=[[True, True], [True, True]],
            label_map=label_map.tolist(),
            image_data=np.zeros((2, 2, 3), dtype=np.uint8).tolist(),
            triggered_id="reset-selection-button",
            parents=[4, 4, 5, 5, 6, 6, -1],
        )

        self.assertEqual(message, "")
        self.assertFalse(is_open)
        self.assertEqual(selected, np.zeros((2, 2), dtype=bool).tolist())

    def test_select_region_click_toggles_label_off(self) -> None:
        label_map = np.array([[0, 0], [1, 1]], dtype=int)
        image = np.zeros((2, 2, 3), dtype=np.uint8).tolist()
        already_selected = np.array([[True, True], [False, False]], dtype=bool)

        selected, message, is_open = select_region(
            click={"points": [{"x": 1, "y": 0, "customdata": 0}]},
            selected_regions=already_selected.tolist(),
            label_map=label_map.tolist(),
            image_data=image,
            triggered_id="image-graph",
            parents=[2, 2, -1],
        )

        self.assertEqual(message, "")
        self.assertFalse(is_open)
        self.assertEqual(selected, np.zeros((2, 2), dtype=bool).tolist())

    def test_select_region_click_out_of_bounds_keeps_state(self) -> None:
        label_map = np.array([[0, 1], [2, 3]], dtype=int)
        image = np.zeros((2, 2, 3), dtype=np.uint8).tolist()
        current = np.array([[False, True], [False, False]], dtype=bool)

        selected, message, is_open = select_region(
            click={"points": [{"x": 8, "y": 9}]},
            selected_regions=current.tolist(),
            label_map=label_map.tolist(),
            image_data=image,
            triggered_id="image-graph",
            parents=[4, 4, 5, 5, 6, 6, -1],
        )

        self.assertEqual(message, "")
        self.assertFalse(is_open)
        self.assertEqual(selected, current.tolist())

    def test_select_region_parent_button_requires_selection(self) -> None:
        label_map = np.array([[0, 1], [2, 3]], dtype=int)
        image = np.zeros((2, 2, 3), dtype=np.uint8).tolist()

        selected, message, is_open = select_region(
            click=None,
            selected_regions=np.zeros((2, 2), dtype=bool).tolist(),
            label_map=label_map.tolist(),
            image_data=image,
            triggered_id="parent-region-button",
            parents=[4, 4, 5, 5, 6, 6, -1],
        )

        self.assertEqual(selected, np.zeros((2, 2), dtype=bool).tolist())
        self.assertIn("Select at least one region first", message)
        self.assertTrue(is_open)

    def test_select_region_parent_button_requires_hierarchy(self) -> None:
        label_map = np.array([[0, 1], [2, 3]], dtype=int)
        image = np.zeros((2, 2, 3), dtype=np.uint8).tolist()
        selected_regions = np.array([[True, False], [False, False]], dtype=bool)

        selected, message, is_open = select_region(
            click=None,
            selected_regions=selected_regions.tolist(),
            label_map=label_map.tolist(),
            image_data=image,
            triggered_id="parent-region-button",
            parents=None,
        )

        self.assertEqual(selected, selected_regions.tolist())
        self.assertIn("Hierarchy is not available yet", message)
        self.assertTrue(is_open)

    def test_select_region_ignores_non_interactive_triggers(self) -> None:
        selected, message, is_open = select_region(
            click=None,
            selected_regions=[[True]],
            label_map=[[0]],
            image_data=[[[0, 0, 0]]],
            triggered_id="compactness-input",
            parents=[-1],
        )

        self.assertIsNone(selected)
        self.assertEqual(message, "")
        self.assertFalse(is_open)


class TreeImportExportCallbackTest(unittest.TestCase):
    def test_export_then_import_roundtrip_is_lossless(self) -> None:
        tree = TreeInformation(
            parent=np.array([3, 3, 4, 4, -1], dtype=np.int32),
            altitude=np.array([0.0, 0.0, 0.0, 1.0, 2.0], dtype=np.float64),
            nodemap=np.array([[0, 0], [1, 2]], dtype=np.int32),
            img=np.array(
                [
                    [[1, 2, 3], [4, 5, 6]],
                    [[7, 8, 9], [10, 11, 12]],
                ],
                dtype=np.uint8,
            ),
            selected_nodes=np.array([0, 2], dtype=np.int32),
        )

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as file:
            path = file.name

        try:
            export_tree_information(tree, path)
            restored = import_tree_information(path)
        finally:
            Path(path).unlink(missing_ok=True)

        self.assertTrue(np.array_equal(restored.parent, tree.parent))
        self.assertTrue(np.array_equal(restored.nodemap, tree.nodemap))
        self.assertTrue(np.array_equal(restored.img, tree.img))
        self.assertTrue(np.array_equal(restored.selected_nodes, tree.selected_nodes))
        self.assertIsNotNone(restored.altitude)
        assert restored.altitude is not None
        self.assertTrue(np.array_equal(restored.altitude, tree.altitude))

    def test_download_tree_information_returns_download_payload(self) -> None:
        payload = download_tree_information(
            click=1,
            hierarchy_parent=[3, 3, 4, 4, -1],
            hierarchy_altitude=[0.0, 0.0, 0.0, 1.0, 2.0],
            label_map_data=[[0, 0], [1, 2]],
            image_data=[
                [[1, 2, 3], [4, 5, 6]],
                [[7, 8, 9], [10, 11, 12]],
            ],
            selected_regions_data=[[True, True], [False, True]],
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.get("filename"), "tree_information.json.gz")
        self.assertIn("content", payload)

    def test_download_tree_information_missing_inputs_returns_none(self) -> None:
        self.assertIsNone(
            download_tree_information(
                click=1,
                hierarchy_parent=None,
                hierarchy_altitude=[0.0],
                label_map_data=[[0]],
                image_data=[[[0, 0, 0]]],
                selected_regions_data=[[True]],
            )
        )
        self.assertIsNone(
            download_tree_information(
                click=0,
                hierarchy_parent=[-1],
                hierarchy_altitude=[0.0],
                label_map_data=[[0]],
                image_data=[[[0, 0, 0]]],
                selected_regions_data=[[True]],
            )
        )

    def test_export_import_preserves_none_altitude(self) -> None:
        tree = TreeInformation(
            parent=np.array([2, 2, -1], dtype=np.int32),
            altitude=None,
            nodemap=np.array([[0, 1]], dtype=np.int32),
            img=np.array([[[0, 0, 0], [255, 255, 255]]], dtype=np.uint8),
            selected_nodes=np.array([], dtype=np.int32),
        )

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as file:
            path = file.name

        try:
            export_tree_information(tree, path)
            restored = import_tree_information(path)
        finally:
            Path(path).unlink(missing_ok=True)

        self.assertIsNone(restored.altitude)
        self.assertTrue(np.array_equal(restored.parent, tree.parent))

    def test_upload_tree_information_raises_on_missing_content(self) -> None:
        with self.assertRaises(ValueError):
            upload_tree_information(None)

    def test_upload_tree_information_raises_on_non_2d_nodemap(self) -> None:
        tree = TreeInformation(
            parent=np.array([1, -1], dtype=np.int32),
            altitude=np.array([0.0, 1.0], dtype=np.float64),
            nodemap=np.array([[[0, 1]]], dtype=np.int32),
            img=np.zeros((1, 2, 3), dtype=np.uint8),
            selected_nodes=np.array([0], dtype=np.int32),
        )
        content = _to_tree_upload_content(tree)

        with self.assertRaises(ValueError):
            upload_tree_information(content)

    def test_upload_tree_information_ignores_unknown_selected_nodes(self) -> None:
        tree = TreeInformation(
            parent=np.array([3, 3, 4, 4, -1], dtype=np.int32),
            altitude=np.array([0.0, 0.0, 0.0, 1.0, 2.0], dtype=np.float64),
            nodemap=np.array(
                [
                    [0, 1, 2],
                    [0, 1, 2],
                ],
                dtype=np.int32,
            ),
            img=np.zeros((2, 3, 3), dtype=np.uint8),
            selected_nodes=np.array([999], dtype=np.int32),
        )
        content = _to_tree_upload_content(tree)

        _, _, imported_selected_regions, _, _, _ = upload_tree_information(content)
        self.assertEqual(
            int(np.asarray(imported_selected_regions, dtype=bool).sum()),
            0,
        )

    def test_upload_tree_information_expands_internal_selected_nodes(self) -> None:
        tree = TreeInformation(
            parent=np.array([3, 3, 4, 4, -1], dtype=np.int32),
            altitude=np.array([0.0, 0.0, 0.0, 1.0, 2.0], dtype=np.float64),
            nodemap=np.array(
                [
                    [0, 1, 2],
                    [0, 1, 2],
                ],
                dtype=np.int32,
            ),
            img=np.zeros((2, 3, 3), dtype=np.uint8),
            selected_nodes=np.array([3], dtype=np.int32),
        )

        content = _to_tree_upload_content(tree)
        (
            imported_image,
            imported_label_map,
            imported_selected_regions,
            imported_border,
            imported_parent,
            imported_altitude,
        ) = upload_tree_information(content)

        self.assertEqual(np.asarray(imported_image).shape, (2, 3, 3))
        self.assertTrue(np.array_equal(np.asarray(imported_label_map), tree.nodemap))

        expected_selected = np.array(
            [
                [True, True, False],
                [True, True, False],
            ],
            dtype=bool,
        )
        self.assertTrue(
            np.array_equal(np.asarray(imported_selected_regions, dtype=bool), expected_selected)
        )

        self.assertEqual(np.asarray(imported_border, dtype=bool).shape, (2, 3))
        self.assertEqual(imported_parent, tree.parent.tolist())
        self.assertEqual(imported_altitude, tree.altitude.astype(float).tolist())


if __name__ == "__main__":
    unittest.main()
