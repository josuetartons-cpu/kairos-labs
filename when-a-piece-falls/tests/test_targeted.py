'Check the structural criterion, ties and nested targeted shocks.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_example_network, build_layered_network
from cascades import run_cascade
from experiments import cascade_record
from targeted import rank_by_out_degree


class TargetedTests(unittest.TestCase):
    def test_highest_original_out_degree_comes_first(self):
        graph = build_example_network()
        ranking = rank_by_out_degree(graph, 4000)
        self.assertEqual(set(ranking[:2]), {"B", "C"})
        self.assertEqual(set(ranking[-1:]), {"G"})
        self.assertEqual(len(set(ranking)), 8)
        degrees = [graph.out_degree(firm) for firm in ranking]
        self.assertEqual(degrees, sorted(degrees, reverse=True))

    def test_seed_reproduces_ties_and_alternative_seed_changes_tie_order(self):
        graph = build_example_network()
        self.assertEqual(rank_by_out_degree(graph, 4000), rank_by_out_degree(graph, 4000))
        self.assertNotEqual(rank_by_out_degree(graph, 4000), rank_by_out_degree(graph, 4001))

    def test_manual_targeted_pair_causes_seven_failures(self):
        graph = build_example_network()
        initial = set(rank_by_out_degree(graph, 4000)[:2])
        rounds = run_cascade(graph, initial)
        self.assertEqual(rounds, [["B", "C"], ["D", "E", "H"], ["F"], ["G"]])
        record = cascade_record(graph, initial, rounds, 1)
        self.assertEqual(record["total_failures"], 7)
        self.assertEqual(record["additional_failures"], 5)

    def test_larger_shocks_are_nested_within_fixed_ranking(self):
        graph = build_layered_network(1000, 1000, 2000)
        ranking = rank_by_out_degree(graph, 4000)
        previous = set()
        for count in (10, 50, 100, 200):
            selected = set(ranking[:count])
            self.assertEqual(len(selected), count)
            self.assertTrue(previous.issubset(selected))
            self.assertGreaterEqual(min(graph.out_degree(f) for f in selected), max(graph.out_degree(f) for f in set(graph) - selected))
            previous = selected


if __name__ == "__main__":
    unittest.main()
