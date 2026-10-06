'Structural controls and HHI checked against manual distributions.'

from pathlib import Path
import sys
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concentration import build_concentrated_network, supplier_hhi, compare_concentration_shock
from network import build_layered_network
from cascades import run_cascade
from experiments import cascade_record


class ConcentrationTests(unittest.TestCase):
    def test_rewiring_preserves_nodes_attributes_in_degrees_and_layer_edge_counts(self):
        original = build_layered_network()
        before = original.copy()
        variant, pools = build_concentrated_network(original, 10, 9000)
        self.assertEqual(dict(variant.nodes(data=True)), dict(original.nodes(data=True)))
        self.assertEqual(dict(variant.in_degree()), dict(original.in_degree()))
        self.assertEqual(variant.number_of_edges(), original.number_of_edges())
        for layer in range(4):
            self.assertEqual(len(pools[layer]), 10)
            self.assertEqual(supplier_hhi(variant, layer)["edges"], supplier_hhi(original, layer)["edges"])
        for supplier, customer in variant.edges:
            layer = variant.nodes[supplier]["layer"]
            self.assertEqual(variant.nodes[customer]["layer"], layer + 1)
            self.assertIn(supplier, pools[layer])
        self.assertEqual(set(original.edges), set(before.edges))
        self.assertEqual(original.graph, before.graph)
        self.assertEqual(dict(original.nodes(data=True)), dict(before.nodes(data=True)))

    def test_seed_reproduces_pools_and_edges_and_another_seed_changes_assignment(self):
        original = build_layered_network()
        first, pools = build_concentrated_network(original, 10, 9000)
        second, repeated = build_concentrated_network(original, 10, 9000)
        other, other_pools = build_concentrated_network(original, 10, 9001)
        self.assertEqual(pools, repeated)
        self.assertEqual(set(first.edges), set(second.edges))
        self.assertNotEqual(pools, other_pools)
        self.assertNotEqual(set(first.edges), set(other.edges))

    def test_hhi_manual_uniform_and_concentrated_with_unused_suppliers(self):
        uniform = nx.DiGraph()
        uniform.add_nodes_from("ABCD", layer=0)
        uniform.add_nodes_from("WXYZ", layer=1)
        uniform.add_edges_from(zip("ABCD", "WXYZ"))
        concentrated = uniform.copy()
        concentrated.remove_edges_from(list(concentrated.edges))
        concentrated.add_edges_from((("A", "W"), ("A", "X"), ("B", "Y"), ("B", "Z")))
        self.assertEqual(supplier_hhi(uniform, 0)["hhi"], .25)
        result = supplier_hhi(concentrated, 0)
        self.assertEqual(result["hhi"], .5)
        self.assertEqual(result["potential_suppliers"], 4)
        self.assertEqual(result["suppliers_with_clients"], 2)
        self.assertEqual(result["edges"], 4)

    def test_invalid_pool_and_nonadjacent_edge_are_rejected(self):
        original = build_layered_network()
        before = set(original.edges)
        for size in (0, 1, 21, 10.5, True):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    build_concentrated_network(original, size, 9000)
        self.assertEqual(set(original.edges), before)
        original.add_edge("E000", "E040")
        with self.assertRaises(ValueError):
            build_concentrated_network(original, 10, 9000)

    def test_hhi_without_relationships_is_undefined(self):
        graph = nx.DiGraph()
        graph.add_node("A", layer=0)
        with self.assertRaises(ValueError):
            supplier_hhi(graph, 0)


class ConcentrationShockTests(unittest.TestCase):
    def example(self):
        original = nx.DiGraph()
        original.add_edges_from((("A", "D"), ("B", "E"), ("C", "F")))
        variant = original.copy()
        variant.remove_edges_from(list(variant.edges))
        variant.add_edges_from((("A", "D"), ("A", "E"), ("A", "F")))
        return original, variant

    def reference(self, graph, initial):
        return {key: str(value) for key, value in
                cascade_record(graph, initial, run_cascade(graph, initial), 9).items()}

    def test_same_shock_can_increase_or_reduce_damage_without_mutating_graphs(self):
        original, variant = self.example()
        before = set(original.edges), set(variant.edges)
        for firm, expected in (("A", 4), ("B", 1)):
            with self.subTest(firm=firm):
                baseline, result, _ = compare_concentration_shock(original, variant, self.reference(original, {firm}))
                self.assertEqual(baseline["total_failures"], 2)
                self.assertEqual(result["total_failures"], expected)
                self.assertEqual(result["initial_firms"], firm)
                self.assertEqual(result["repetition"], 9)
        self.assertEqual((set(original.edges), set(variant.edges)), before)

    def test_equal_damage_and_manual_concentrated_rounds(self):
        original, variant = self.example()
        _, result, rounds = compare_concentration_shock(original, variant, self.reference(original, {"A"}))
        self.assertEqual(rounds, [["A"], ["D", "E", "F"]])
        self.assertEqual(result["additional_failures"], 3)
        baseline, result, _ = compare_concentration_shock(original, variant, self.reference(original, {"F"}))
        self.assertEqual(result["total_failures"], baseline["total_failures"])

    def test_inconsistent_saved_selection_or_result_is_rejected(self):
        original, variant = self.example()
        reference = self.reference(original, {"A"})
        for change in ({"initial_firms": "A|A"}, {"total_failures": "5"}, {"failed_firms": "A|E"}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    compare_concentration_shock(original, variant, {**reference, **change})
