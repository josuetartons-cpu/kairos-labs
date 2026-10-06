'Check selections, shock resets and metrics against manual cases.'

from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_example_network
from experiments import select_random_shock, run_repeated_shocks, summarize_shocks


class ExperimentTests(unittest.TestCase):
    def test_selection_has_exact_count_without_duplicates(self):
        graph = build_example_network()
        shock = select_random_shock(graph, 3, random.Random(44))
        self.assertEqual(len(shock), 3)
        self.assertTrue(shock.issubset(graph.nodes))

    def test_repetitions_match_manually_known_outcomes(self):
        graph = build_example_network()
        before = (list(graph.nodes(data=True)), list(graph.edges))
        results, rounds = run_repeated_shocks(graph, repetitions=100)
        expected_failed = {
            "A": {"A"}, "B": {"B", "H"}, "C": {"C", "D", "E", "F"},
            "D": {"D"}, "E": {"E"}, "F": {"F"}, "G": {"G"}, "H": {"H"},
        }
        self.assertEqual(len(results), 100)
        for row in results:
            expected = expected_failed[row["initial_firms"]]
            self.assertEqual(set(row["failed_firms"].split("|")), expected)
            self.assertEqual(row["total_failures"], len(expected))
            self.assertEqual(row["additional_failures"], len(expected) - 1)
            self.assertEqual(row["amplification"], len(expected))
            self.assertEqual(row["functional_firms_pct"], 100 * (8 - len(expected)) / 8)
            actual_rounds = [r for r in rounds if r["repetition"] == row["repetition"]]
            self.assertEqual(len(actual_rounds), len(expected))
        self.assertEqual((list(graph.nodes(data=True)), list(graph.edges)), before)

    def test_same_seed_reproduces_results_and_rounds(self):
        graph = build_example_network()
        self.assertEqual(run_repeated_shocks(graph), run_repeated_shocks(graph))

    def test_full_shock_is_one_round_and_zero_survival(self):
        results, rounds = run_repeated_shocks(build_example_network(), count=8, repetitions=1)
        self.assertEqual(results[0]["total_failures"], 8)
        self.assertEqual(results[0]["additional_failures"], 0)
        self.assertEqual(results[0]["functional_firms_pct"], 0)
        self.assertTrue(all(r["round"] == 0 for r in rounds))

    def test_invalid_counts_and_repetitions(self):
        graph = build_example_network()
        for count in (0, 9, 1.5):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    select_random_shock(graph, count, random.Random(44))
        with self.assertRaises(ValueError):
            run_repeated_shocks(graph, repetitions=0)

    def test_summary_agrees_with_complete_shock(self):
        results, _ = run_repeated_shocks(build_example_network(), count=8, repetitions=3)
        summary = summarize_shocks(results, shock_fraction=1.0, shock_seed=44)
        self.assertEqual(summary["repetitions"], 3)
        self.assertEqual(summary["initial_failures"], 8)
        self.assertEqual(summary["mean_total_failures"], 8)
        self.assertEqual(summary["mean_additional_failures"], 0)
        self.assertEqual(summary["mean_amplification"], 1)
        self.assertEqual(summary["mean_functional_firms_pct"], 0)
        self.assertEqual(summary["shocks_with_cascade"], 0)

    def test_twenty_firm_shocks_keep_all_initial_failures(self):
        from network import build_layered_network

        results, _ = run_repeated_shocks(build_layered_network(), count=20, repetitions=10, shock_seed=47)
        for row in results:
            initial = set(row["initial_firms"].split("|"))
            failed = set(row["failed_firms"].split("|"))
            self.assertEqual(len(initial), 20)
            self.assertTrue(initial.issubset(failed))
            self.assertEqual(row["total_failures"], len(failed))
            self.assertGreaterEqual(row["amplification"], 1)


if __name__ == "__main__":
    unittest.main()
