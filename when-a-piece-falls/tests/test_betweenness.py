'Manual betweenness, direction and joining the previous census.'

from pathlib import Path
import sys
import unittest

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from betweenness import directed_betweenness, join_saved_damage


class BetweennessTests(unittest.TestCase):
    def test_directed_chain_excludes_endpoints_and_preserves_graph(self):
        graph = nx.DiGraph([("A", "B"), ("B", "C")])
        graph.nodes["B"]["active"] = True
        before = graph.copy()
        rows = directed_betweenness(graph)
        self.assertEqual(rows["B"], {"betweenness_raw": 1.0, "betweenness_normalized": .5})
        self.assertEqual(rows["A"]["betweenness_raw"], 0)
        self.assertEqual(rows["C"]["betweenness_raw"], 0)
        self.assertEqual(set(graph.edges), set(before.edges))
        self.assertEqual(dict(graph.nodes(data=True)), dict(before.nodes(data=True)))

    def test_diamond_shares_paths_and_isolates_enter_denominator(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        graph.add_node("E")
        rows = directed_betweenness(graph)
        for firm in ("B", "C"):
            self.assertEqual(rows[firm]["betweenness_raw"], .5)
            self.assertEqual(rows[firm]["betweenness_normalized"], .5/12)
        self.assertEqual(rows["E"]["betweenness_raw"], 0)

    def test_sources_can_have_customers_but_zero_betweenness(self):
        graph = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "D")])
        self.assertEqual(graph.out_degree("A"), 2)
        self.assertEqual(directed_betweenness(graph)["A"]["betweenness_raw"], 0)
        with self.assertRaises(ValueError):
            directed_betweenness(graph.to_undirected())

    def test_join_rejects_missing_duplicate_and_wrong_degree(self):
        graph = nx.DiGraph()
        graph.add_node("A", layer=0, size=1)
        saved = {"firm": "A", "layer": "0", "size": "1", "in_degree": "0",
                 "out_degree": "0", "initial_failures": "1", "total_failures": "1",
                 "additional_failures": "0", "failed_firms": "A", "propagation_rounds": "0"}
        centrality = directed_betweenness(graph)
        self.assertEqual(join_saved_damage(graph, [saved], centrality)[0]["total_failures"], 1)
        for rows in ([], [saved, saved], [{**saved, "out_degree": "1"}]):
            with self.assertRaises(ValueError):
                join_saved_damage(graph, rows, centrality)
