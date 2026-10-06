'Check pilot-generator assumptions and reproducibility.'

from pathlib import Path
import sys
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_layered_network
from cascades import run_cascade


class GeneratorTests(unittest.TestCase):
    def test_structure_and_initial_functionality(self):
        graph = build_layered_network()
        self.assertEqual(len(graph), 100)
        for layer in range(5):
            self.assertEqual(sum(attrs["layer"] == layer for _, attrs in graph.nodes(data=True)), 20)
        sources = {firm for firm in graph if graph.in_degree(firm) == 0}
        self.assertEqual(len(sources), 20)
        for firm, attrs in graph.nodes(data=True):
            self.assertTrue(attrs["active"])
            self.assertIn(attrs["size"], (1, 2, 4))
            if attrs["layer"] == 0:
                self.assertIn(firm, sources)
            else:
                self.assertIn(graph.in_degree(firm), (1, 2, 3))
        for supplier, customer in graph.edges:
            self.assertEqual(graph.nodes[customer]["layer"], graph.nodes[supplier]["layer"] + 1)
        self.assertTrue(nx.is_directed_acyclic_graph(graph))
        self.assertEqual(run_cascade(graph, []), [[]])

    def test_same_seeds_reproduce_full_graph(self):
        first = build_layered_network()
        second = build_layered_network()
        self.assertEqual(list(first.nodes(data=True)), list(second.nodes(data=True)))
        self.assertEqual(list(first.edges), list(second.edges))
        self.assertEqual(first.graph, second.graph)

    def test_size_seed_does_not_change_topology(self):
        first = build_layered_network(size_seed=43)
        second = build_layered_network(size_seed=99)
        self.assertEqual(list(first.edges), list(second.edges))
        self.assertNotEqual(nx.get_node_attributes(first, "size"), nx.get_node_attributes(second, "size"))

    def test_topology_seed_does_not_change_sizes(self):
        first = build_layered_network(topology_seed=42)
        second = build_layered_network(topology_seed=99)
        self.assertEqual(nx.get_node_attributes(first, "size"), nx.get_node_attributes(second, "size"))
        self.assertNotEqual(set(first.edges), set(second.edges))

    def test_incompatible_network_sizes_are_rejected(self):
        for n in (0, 10, 99, 100.0):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    build_layered_network(n=n)


if __name__ == "__main__":
    unittest.main()
