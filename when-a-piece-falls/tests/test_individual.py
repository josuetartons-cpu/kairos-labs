'Check the census, manual damage and the mechanical exclusion of size.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_example_network
from individual import evaluate_firms, summarize_cases


class IndividualTests(unittest.TestCase):
    def example(self):
        graph = build_example_network()
        for firm in graph:
            graph.nodes[firm]["size"] = 1
        return graph

    def test_exhaustive_manual_damage_and_fresh_cases(self):
        graph = self.example()
        original = graph.copy()
        cases, rounds = evaluate_firms(graph)
        self.assertEqual({r["firm"]: r["total_failures"] for r in cases},
                         {"A": 1, "B": 2, "C": 4, "D": 1, "E": 1, "F": 1, "G": 1, "H": 1})
        self.assertEqual(len(cases), 8)
        self.assertEqual(len(rounds), 12)
        self.assertEqual(dict(graph.nodes(data=True)), dict(original.nodes(data=True)))
        self.assertEqual(set(graph.edges), set(original.edges))
        c_rounds = [r for r in rounds if r["shocked_firm"] == "C"]
        self.assertEqual([(r["round"], r["firm"]) for r in c_rounds], [(0, "C"), (1, "D"), (1, "E"), (2, "F")])

    def test_size_relabeling_preserves_damage(self):
        graph = self.example()
        before, _ = evaluate_firms(graph)
        for firm in graph:
            graph.nodes[firm]["size"] = 4
        after, _ = evaluate_firms(graph)
        self.assertEqual([r["failed_firms"] for r in before], [r["failed_firms"] for r in after])

    def test_summary_counts_includes_initial_failure(self):
        cases, _ = evaluate_firms(self.example())
        summary = summarize_cases(cases)
        self.assertEqual(summary["cases"], 8)
        self.assertEqual(summary["mean_total_failures"], 1.5)
        self.assertEqual(summary["mean_additional_failures"], .5)
        self.assertEqual(summary["cascade_frequency_pct"], 25)
        self.assertEqual(summary["max_total_failures"], 4)
