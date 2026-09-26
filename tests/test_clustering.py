import unittest

from src.compute._clustering import _validate_parent_table


class ClusteringValidationTest(unittest.TestCase):
    def test_validate_parent_table_accepts_single_root_tree(self) -> None:
        _validate_parent_table([3, 3, 4, 4, -1])

    def test_validate_parent_table_rejects_multiple_roots(self) -> None:
        with self.assertRaises(ValueError):
            _validate_parent_table([-1, -1, 1])


if __name__ == "__main__":
    unittest.main()
