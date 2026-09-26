import unittest

from src.ui.callbacks.index._plot_dendrogram import plot_dendrogram


class PlotDendrogramSelectedLeavesTest(unittest.TestCase):
    def test_highlights_selected_leaf_and_immediate_parent(self):
        parents = [3, 3, 4, 4, -1]
        altitude = [0.0, 0.0, 0.0, 2.0, 3.0]

        fig = plot_dendrogram(parents, altitude, selected_labels=[0, 1])
        leaf_trace = fig.data[-1]
        marker_colors = leaf_trace.marker.color

        self.assertIn("#FF0000", marker_colors)
        self.assertIn("darkblue", marker_colors)

        line_traces = fig.data[:-1]
        highlighted_edges = [
            trace.line.color for trace in line_traces if trace.line.color == "#FF0000"
        ]
        self.assertTrue(highlighted_edges)

    def test_selecting_internal_node_highlights_descendant_leaves(self):
        parents = [3, 3, 4, 4, -1]
        altitude = [0.0, 0.0, 0.0, 2.0, 3.0]

        fig = plot_dendrogram(parents, altitude, selected_labels=[3])
        leaf_trace = fig.data[-1]
        marker_colors = list(leaf_trace.marker.color)
        marker_text = list(leaf_trace.text)

        color_by_label = dict(zip(marker_text, marker_colors, strict=False))

        self.assertEqual(color_by_label.get("Region 0"), "#FF0000")
        self.assertEqual(color_by_label.get("Region 1"), "#FF0000")
        self.assertEqual(color_by_label.get("Region 2"), "darkblue")

    def test_partial_siblings_do_not_highlight_their_parent_region(self):
        # Node 4 has three leaves: 0, 1, 2. Selecting only 0 and 1 must not
        # promote node 4 as a selected region in the dendrogram.
        parents = [4, 4, 4, 5, 5, -1]
        altitude = [0.0, 0.0, 0.0, 0.0, 2.0, 3.0]

        fig = plot_dendrogram(parents, altitude, selected_labels=[0, 1])
        highlighted_edges = [
            trace for trace in fig.data[:-1] if trace.line.color == "#FF0000"
        ]

        self.assertEqual(len(highlighted_edges), 0)

    def test_single_selected_leaf_highlights_only_the_leaf(self):
        parents = [3, 3, 4, 4, -1]
        altitude = [0.0, 0.0, 0.0, 2.0, 3.0]

        fig = plot_dendrogram(parents, altitude, selected_labels=[0])
        leaf_trace = fig.data[-1]
        marker_colors = list(leaf_trace.marker.color)

        self.assertEqual(marker_colors.count("#FF0000"), 1)

        highlighted_edges = [
            trace for trace in fig.data[:-1] if trace.line.color == "#FF0000"
        ]
        self.assertEqual(len(highlighted_edges), 0)

    def test_stops_highlighting_at_the_lowest_common_ancestor(self):
        parents = [3, 3, 4, 4, -1]
        altitude = [0.0, 0.0, 0.0, 2.0, 3.0]

        fig = plot_dendrogram(parents, altitude, selected_labels=[0, 1])
        highlighted_edges = [
            trace for trace in fig.data[:-1] if trace.line.color == "#FF0000"
        ]

        self.assertEqual(len(highlighted_edges), 2)


if __name__ == "__main__":
    unittest.main()
