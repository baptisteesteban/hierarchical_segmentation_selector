import unittest

from src.compute import LCA
from src.ui.callbacks.index._select_region import select_parent_cluster


def _naive_lca(parents: list[int], u: int, v: int) -> int:
    ancestors: set[int] = set()
    cur = u
    while cur != -1:
        ancestors.add(cur)
        cur = parents[cur]

    cur = v
    while cur != -1:
        if cur in ancestors:
            return cur
        cur = parents[cur]

    raise AssertionError("No LCA found in a valid rooted tree")


class LCATest(unittest.TestCase):
    def test_basic_tree(self) -> None:
        parents = [3, 3, 4, 4, -1]
        lca = LCA(parents)

        self.assertEqual(lca.root, 4)
        self.assertEqual(lca(0, 1), 3)
        self.assertEqual(lca(0, 2), 4)
        self.assertEqual(lca(3, 1), 3)
        self.assertEqual(lca(4, 0), 4)

    def test_single_node(self) -> None:
        lca = LCA([-1])
        self.assertEqual(lca(0, 0), 0)

    def test_chain(self) -> None:
        parents = [1, 2, 3, -1]
        lca = LCA(parents)

        self.assertEqual(lca(0, 1), 1)
        self.assertEqual(lca(0, 2), 2)
        self.assertEqual(lca(0, 3), 3)
        self.assertEqual(lca(2, 3), 3)

    def test_matches_naive_on_larger_tree(self) -> None:
        parents = [
            15,
            15,
            16,
            16,
            17,
            17,
            18,
            18,
            19,
            19,
            20,
            20,
            21,
            21,
            22,
            23,
            23,
            24,
            24,
            25,
            25,
            26,
            26,
            27,
            27,
            28,
            28,
            29,
            29,
            -1,
        ]
        lca = LCA(parents)

        test_pairs = [
            (0, 1),
            (0, 4),
            (2, 3),
            (6, 13),
            (7, 14),
            (8, 11),
            (3, 26),
            (0, 29),
            (15, 22),
            (27, 28),
        ]

        for u, v in test_pairs:
            self.assertEqual(lca(u, v), _naive_lca(parents, u, v))

    def test_is_ancestor(self) -> None:
        parents = [3, 3, 4, 4, -1]
        lca = LCA(parents)

        self.assertTrue(lca.is_ancestor(4, 0))
        self.assertTrue(lca.is_ancestor(3, 1))
        self.assertFalse(lca.is_ancestor(0, 3))

    def test_select_parent_cluster_uses_lca(self) -> None:
        parents = [3, 3, 4, 4, -1]

        self.assertEqual(select_parent_cluster([0], parents), {0, 1})
        self.assertEqual(select_parent_cluster([0, 1], parents), {0, 1, 2})
        self.assertEqual(select_parent_cluster([2], parents), {0, 1, 2})

    def test_select_parent_cluster_rejects_internal_nodes(self) -> None:
        parents = [3, 3, 4, 4, -1]

        with self.assertRaises(ValueError):
            select_parent_cluster([3], parents)

    def test_select_parent_cluster_rejects_out_of_bounds(self) -> None:
        parents = [3, 3, 4, 4, -1]

        with self.assertRaises(ValueError):
            select_parent_cluster([99], parents)

    def test_select_parent_cluster_does_not_overshoot_from_partial_lca(self) -> None:
        # LCA(0, 2) is node 4 with descendants {0, 1, 2}; the parent (node 5)
        # adds leaf 3 and must not be selected on the first parent action.
        parents = [4, 4, 4, 5, 5, -1]

        self.assertEqual(select_parent_cluster([0, 2], parents), {0, 1, 2})

    def test_invalid_empty(self) -> None:
        with self.assertRaises(ValueError):
            LCA([])

    def test_invalid_multiple_roots(self) -> None:
        with self.assertRaises(ValueError):
            LCA([-1, -1, 1])

    def test_invalid_parent_index(self) -> None:
        with self.assertRaises(ValueError):
            LCA([3, -1, 1])

    def test_invalid_cycle(self) -> None:
        with self.assertRaises(ValueError):
            LCA([1, 0, -1])

    def test_invalid_disconnected(self) -> None:
        with self.assertRaises(ValueError):
            LCA([2, -1, -1])

    def test_query_out_of_bounds(self) -> None:
        lca = LCA([3, 3, 4, 4, -1])

        with self.assertRaises(ValueError):
            lca(-1, 0)
        with self.assertRaises(ValueError):
            lca(0, 99)


if __name__ == "__main__":
    unittest.main()
