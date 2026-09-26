import unittest

import numpy as np

from src.ui.pages._index import _selected_labels_from_mask


class IndexParentSelectionTest(unittest.TestCase):
    def test_selected_labels_from_mask_rejects_shape_mismatch(self) -> None:
        selected_mask = np.array([[True, False]], dtype=bool)
        label_map = np.array([[0, 1], [2, 3]], dtype=int)

        with self.assertRaises(ValueError):
            _selected_labels_from_mask(selected_mask, label_map)

    def test_selected_labels_from_mask_extracts_unique_labels(self) -> None:
        selected_mask = np.array([[True, False], [True, True]], dtype=bool)
        label_map = np.array([[0, 1], [2, 2]], dtype=int)

        self.assertEqual(_selected_labels_from_mask(selected_mask, label_map), [0, 2])


if __name__ == "__main__":
    unittest.main()
