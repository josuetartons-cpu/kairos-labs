'Hand-calculated cases checking the agreed dynamics.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_example_network
from cascades import run_cascade


class CascadeTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_example_network()

    def test_no_shock_no_failures_including_sources(self):
        self.assertEqual(run_cascade(self.graph, []), [[]])

    def test_one_remaining_supplier_is_enough(self):
        self.assertEqual(run_cascade(self.graph, {"A"}), [["A"]])

    def test_simultaneous_rounds_and_surviving_alternative(self):
        self.assertEqual(
            run_cascade(self.graph, {"C"}),
            [["C"], ["D", "E"], ["F"]],
        )

    def test_sources_can_be_directly_shocked(self):
        self.assertEqual(
            run_cascade(self.graph, {"A", "B"}),
            [["A", "B"], ["C", "H"], ["D", "E"], ["F"], ["G"]],
        )

    def test_repeated_runs_preserve_original_network(self):
        nodes_before = [(n, attrs.copy()) for n, attrs in self.graph.nodes(data=True)]
        edges_before = list(self.graph.edges)
        run_cascade(self.graph, {"C"})
        self.assertEqual(list(self.graph.nodes(data=True)), nodes_before)
        self.assertEqual(list(self.graph.edges), edges_before)
        self.assertEqual(run_cascade(self.graph, {"A"}), [["A"]])

    def test_unknown_firm_is_rejected(self):
        with self.assertRaises(ValueError):
            run_cascade(self.graph, {"Z"})


if __name__ == "__main__":
    unittest.main()
