'Check preservation, alternatives and the expected individual result.'

from pathlib import Path
import sys
import unittest
from itertools import combinations

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_layered_network
from redundancy import add_alternative_suppliers, compare_saved_shock
from individual import evaluate_firms
from cascades import run_cascade
from experiments import cascade_record


class RedundancyTests(unittest.TestCase):
    def test_preserves_original_and_adds_one_distinct_previous_layer_supplier(self):
        graph = build_layered_network()
        before = graph.copy()
        redundant = add_alternative_suppliers(graph, 6000)
        self.assertEqual(dict(graph.nodes(data=True)), dict(before.nodes(data=True)))
        self.assertEqual(set(graph.edges), set(before.edges))
        self.assertEqual(graph.graph, before.graph)
        self.assertEqual(dict(redundant.nodes(data=True)), dict(graph.nodes(data=True)))
        self.assertTrue(set(graph.edges).issubset(redundant.edges))
        self.assertEqual(redundant.number_of_edges() - graph.number_of_edges(), 80)
        for firm in graph:
            original = set(graph.predecessors(firm))
            added = set(redundant.predecessors(firm)) - original
            self.assertEqual(len(added), int(bool(original)))
            for supplier in added:
                self.assertEqual(graph.nodes[supplier]["layer"], graph.nodes[firm]["layer"] - 1)

    def test_same_seed_reproduces_and_different_seed_changes_alternatives(self):
        graph = build_layered_network()
        first = add_alternative_suppliers(graph, 6000)
        self.assertEqual(set(first.edges), set(add_alternative_suppliers(graph, 6000).edges))
        self.assertNotEqual(set(first.edges), set(add_alternative_suppliers(graph, 6001).edges))

    def test_every_single_withdrawal_has_only_the_initial_failure(self):
        graph = add_alternative_suppliers(build_layered_network(), 6000)
        cases, rounds = evaluate_firms(graph)
        self.assertEqual(len(cases), 100)
        self.assertEqual(len(rounds), 100)
        for row in cases:
            self.assertEqual(row["failed_firms"], row["firm"])
            self.assertEqual(row["additional_failures"], 0)
            self.assertEqual(row["propagation_rounds"], 0)

    def test_missing_candidate_is_rejected_without_mutating_original(self):
        graph = build_layered_network()
        customer = "E020"
        graph.add_edges_from((firm, customer) for firm in graph if graph.nodes[firm]["layer"] == 0)
        before = set(graph.edges)
        with self.assertRaises(ValueError):
            add_alternative_suppliers(graph, 6000)
        self.assertEqual(set(graph.edges), before)


class JointRedundancyTests(unittest.TestCase):
    def example(self):
        original = nx.DiGraph()
        original.add_edges_from((("A", "C"), ("B", "D"), ("C", "E")))
        redundant = original.copy()
        redundant.add_edges_from((("B", "C"), ("A", "D"), ("D", "E")))
        return original, redundant

    def reference(self, graph, firms):
        return {key: str(value) for key, value in
                cascade_record(graph, firms, run_cascade(graph, firms), 7).items()}

    def test_saved_joint_shock_keeps_exact_selection_and_can_still_propagate(self):
        original, redundant = self.example()
        reference = self.reference(original, {"A", "B"})
        baseline, result, rounds = compare_saved_shock(original, redundant, reference)
        self.assertEqual(rounds, [["A", "B"], ["C", "D"], ["E"]])
        self.assertEqual(result["initial_firms"], "A|B")
        self.assertEqual(result["repetition"], 7)
        self.assertEqual(result["total_failures"], 5)
        self.assertEqual(result["additional_failures"], 3)
        self.assertEqual(baseline["total_failures"], 5)

    def test_monotonic_final_failures_for_every_nonempty_shock_in_manual_network(self):
        original, redundant = self.example()
        before = (set(original.edges), set(redundant.edges))
        for count in range(1, 6):
            for shock in combinations(sorted(original), count):
                baseline, result, _ = compare_saved_shock(original, redundant, self.reference(original, set(shock)))
                self.assertTrue(set(result["failed_firms"].split("|")).issubset(baseline["failed_firms"].split("|")))
        self.assertEqual((set(original.edges), set(redundant.edges)), before)
        _, result, rounds = compare_saved_shock(original, redundant, self.reference(original, {"A", "E"}))
        self.assertEqual(rounds, [["A", "E"]])
        self.assertEqual(result["total_failures"], 2)

    def test_invalid_saved_reference_is_rejected(self):
        original, redundant = self.example()
        reference = self.reference(original, {"A", "B"})
        for change in ({"initial_firms": "A|A"}, {"total_failures": "4"}, {"failed_firms": "A|B"}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    compare_saved_shock(original, redundant, {**reference, **change})
