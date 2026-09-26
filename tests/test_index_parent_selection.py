import unittest

import numpy as np

from src.ui.callbacks.index._select_region import select_region


class IndexParentSelectionTest(unittest.TestCase):
    def test_parent_selection_rejects_shape_mismatch(self) -> None:
        image_data = np.zeros((2, 2, 3), dtype=np.uint8).tolist()
        label_map = np.array([[0, 1], [2, 3]], dtype=int).tolist()
        selected_regions = np.array([[True, False]], dtype=bool).tolist()

        next_regions, message, is_open = select_region(
            click=None,
            borders=None,
            selected_regions=selected_regions,
            label_map=label_map,
            image_data=image_data,
            triggered_id="parent-region-button",
            parents=[4, 4, 5, 5, 6, 6, -1],
        )

        self.assertEqual(next_regions, selected_regions)
        self.assertIn("out of sync", message)
        self.assertTrue(is_open)

    def test_parent_selection_expands_partial_selection_to_lca_cluster(self) -> None:
        image_data = np.zeros((2, 3, 3), dtype=np.uint8).tolist()
        label_map = np.array([[0, 1, 2], [3, 3, 3]], dtype=int)
        selected_regions = np.array(
            [[True, False, True], [False, False, False]], dtype=bool
        ).tolist()

        next_regions, message, is_open = select_region(
            click=None,
            borders=None,
            selected_regions=selected_regions,
            label_map=label_map.tolist(),
            image_data=image_data,
            triggered_id="parent-region-button",
            parents=[4, 4, 4, 5, 5, -1],
        )

        self.assertEqual(message, "")
        self.assertFalse(is_open)
        self.assertEqual(
            next_regions,
            np.array([[True, True, True], [False, False, False]], dtype=bool).tolist(),
        )


if __name__ == "__main__":
    unittest.main()
