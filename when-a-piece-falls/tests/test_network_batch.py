'Network identifiers and aggregation preserving the unit of analysis.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from experiments import simulate_network_batch, summarize_networks


class NetworkBatchTests(unittest.TestCase):
    def test_small_batch_has_separate_networks_scenarios_and_runs(self):
        batch = simulate_network_batch(network_count=2, repetitions=3)
        self.assertEqual(len(batch["manifest"]), 2)
        self.assertEqual(len(batch["nodes"]), 200)
        self.assertEqual(len(batch["per_network"]), 8)
        self.assertEqual(len(batch["shocks"]), 24)
        self.assertEqual(len(batch["summary"]), 4)
        keys = {(r["network_id"], r["shock_fraction"], r["repetition"]) for r in batch["shocks"]}
        self.assertEqual(len(keys), 24)
        self.assertEqual(len(batch["rounds"]), sum(r["total_failures"] for r in batch["shocks"]))
        self.assertEqual(len({r["topology_seed"] for r in batch["manifest"]}), 2)
        for row in batch["summary"]:
            self.assertEqual(row["networks"], 2)

    def test_equal_network_weight_despite_different_repetition_counts(self):
        base = {
            "shock_fraction": .01, "initial_failures": 1,
            "mean_additional_failures": 0, "mean_functional_firms_pct": 99,
            "mean_amplification": 1, "min_total_failures": 1, "max_total_failures": 5,
        }
        first = {**base, "mean_total_failures": 1, "repetitions": 1, "shocks_with_cascade": 0}
        second = {**base, "mean_total_failures": 5, "repetitions": 9, "shocks_with_cascade": 9}
        summary = summarize_networks([first, second])[0]
        self.assertEqual(summary["mean_total_failures"], 3)
        self.assertEqual(summary["mean_cascade_frequency_pct"], 50)
        self.assertEqual(summary["min_network_mean_total_failures"], 1)
        self.assertEqual(summary["max_network_mean_total_failures"], 5)

    def test_batch_is_reproducible(self):
        self.assertEqual(
            simulate_network_batch(network_count=2, repetitions=2),
            simulate_network_batch(network_count=2, repetitions=2),
        )

    def test_incompatible_n_and_network_count_are_rejected(self):
        with self.assertRaises(ValueError):
            simulate_network_batch(n=150, network_count=1, repetitions=1)
        with self.assertRaises(ValueError):
            simulate_network_batch(network_count=0, repetitions=1)

    def test_thousand_firms_use_percentage_counts_and_correct_denominator(self):
        batch = simulate_network_batch(n=1000, network_count=1, repetitions=1)
        self.assertEqual(len(batch["nodes"]), 1000)
        self.assertEqual(sum(row["layer"] == 0 for row in batch["nodes"]), 200)
        self.assertEqual([r["initial_failures"] for r in batch["shocks"]], [10, 50, 100, 200])
        for row in batch["shocks"]:
            self.assertEqual(len(set(row["initial_firms"].split("|"))), row["initial_failures"])
            self.assertEqual(row["functional_firms_pct"], 100 * (1000 - row["total_failures"]) / 1000)


if __name__ == "__main__":
    unittest.main()
