'Manual examples of weak components, pairs and denominators.'

from pathlib import Path
import sys
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from connectivity import connectivity_metrics, summarize_states, validate_saved_state


class ConnectivityTests(unittest.TestCase):
    def graph(self):
        graph = nx.DiGraph()
        graph.add_nodes_from("ABCDE", active=True)
        graph.add_edges_from((("A", "B"), ("C", "B"), ("D", "E")))
        return graph

    def test_weak_components_and_manual_disconnected_pairs(self):
        result = connectivity_metrics(self.graph())
        self.assertEqual(result["component_sizes"], "3|2")
        self.assertEqual(result["weak_components"], 2)
        self.assertEqual(result["largest_component"], 3)
        self.assertEqual(result["largest_component_fraction_original"], 3 / 5)
        # Six of ten unordered pairs cross between groups of three and two.
        self.assertAlmostEqual(result["fragmentation"], 6 / 10)

    def test_failed_hub_splits_components_without_mutating_active_attributes(self):
        graph = self.graph()
        before = graph.copy()
        result = connectivity_metrics(graph, {"B"})
        self.assertEqual(result["active_firms"], 4)
        self.assertEqual(result["component_sizes"], "2|1|1")
        self.assertEqual(result["weak_components"], 3)
        self.assertEqual(result["largest_component_fraction_original"], 2 / 5)
        self.assertAlmostEqual(result["fragmentation"], 5 / 6)
        self.assertEqual(dict(graph.nodes(data=True)), dict(before.nodes(data=True)))
        self.assertEqual(set(graph.edges), set(before.edges))

    def test_isolates_and_connected_survivors_are_fragmentation_extremes(self):
        graph = self.graph()
        self.assertEqual(connectivity_metrics(graph, {"B", "D", "E"})["fragmentation"], 1)
        result = connectivity_metrics(graph, {"A", "B", "C"})
        self.assertEqual(result["fragmentation"], 0)
        self.assertEqual(result["active_firms"], 2)
        self.assertEqual(result["largest_component_fraction_original"], .4)

    def test_empty_and_single_survivor_leave_fragmentation_undefined(self):
        graph = self.graph()
        empty = connectivity_metrics(graph, set(graph))
        self.assertEqual((empty["active_firms"], empty["weak_components"], empty["largest_component"]), (0, 0, 0))
        self.assertEqual(empty["largest_component_fraction_original"], 0)
        self.assertIsNone(empty["fragmentation"])
        single = connectivity_metrics(graph, set("BCDE"))
        self.assertEqual((single["weak_components"], single["largest_component"]), (1, 1))
        self.assertEqual(single["largest_component_fraction_original"], .2)
        self.assertIsNone(single["fragmentation"])

    def test_unknown_failed_firm_and_invalid_reference_are_rejected(self):
        for graph, failed in ((self.graph(), {"Z"}), (nx.DiGraph(), ()), (nx.Graph([(1, 2)]), ())):
            with self.assertRaises(ValueError):
                connectivity_metrics(graph, failed)
        row = {"failed_firms": "A|B", "initial_firms": "A", "total_failures": "2",
               "initial_failures": "1", "additional_failures": "1", "shock_fraction": ".2"}
        self.assertEqual(validate_saved_state(self.graph(), row), {"A", "B"})
        for change in ({"failed_firms": "A|A"}, {"initial_firms": "C"}, {"total_failures": "3"}):
            with self.assertRaises(ValueError):
                validate_saved_state(self.graph(), {**row, **change})

    def test_equal_network_weights_and_undefined_fragmentation_denominators(self):
        states = []
        for network, failures in (("N01", (set(),)), ("N02", ({"B"}, {"B"}, set("BCDE")))):
            for repetition, failed in enumerate(failures, 1):
                states.append({"version": "original", "strategy": "random", "network_id": network,
                               "shock_fraction": .2, "repetition": repetition,
                               **connectivity_metrics(self.graph(), failed)})
        per_network, summaries = summarize_states(states)
        result = summaries[0]
        self.assertEqual(result["mean_active_firms"], (5 + 3) / 2)
        self.assertAlmostEqual(result["mean_fragmentation"], (.6 + 5 / 6) / 2)
        self.assertEqual(result["fragmentation_defined_cases"], 3)
        self.assertEqual(result["fragmentation_defined_networks"], 2)
        self.assertEqual(per_network[1]["fragmentation_defined_cases"], 2)
        states[0].update(connectivity_metrics(self.graph(), set(self.graph())))
        result = summarize_states(states)[1][0]
        self.assertEqual(result["fragmentation_defined_networks"], 1)
        self.assertAlmostEqual(result["mean_fragmentation"], 5 / 6)
        states = [{**states[0], "repetition": 1}]
        self.assertIsNone(summarize_states(states)[1][0]["mean_fragmentation"])
        with self.assertRaises(ValueError):
            summarize_states(states + states)
