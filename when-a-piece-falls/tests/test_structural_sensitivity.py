'Approved parameter, controls and aggregation of three versions.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_layered_network
from structural_sensitivity import build_sensitivity_variant, summarize_versions


class StructuralSensitivityTests(unittest.TestCase):
    def test_150_eligible_fixed_seed_and_original_controls(self):
        original = build_layered_network(1000, 1000, 2000)
        before = original.copy()
        variant, pools = build_sensitivity_variant(original, 0)
        self.assertEqual(variant.graph["concentration_seed"], 10000)
        self.assertTrue(all(len(firms) == len(set(firms)) == 150 for firms in pools.values()))
        self.assertEqual(dict(variant.in_degree()), dict(original.in_degree()))
        self.assertEqual(variant.number_of_edges(), original.number_of_edges())
        self.assertEqual(dict(variant.nodes(data=True)), dict(original.nodes(data=True)))
        self.assertEqual(set(original.edges), set(before.edges))
        for a, b in variant.edges:
            layer = original.nodes[a]["layer"]
            self.assertIn(a, pools[layer])
            self.assertEqual(original.nodes[b]["layer"], layer + 1)
        repeated, _ = build_sensitivity_variant(original, 0)
        self.assertEqual(set(variant.edges), set(repeated.edges))

    def rows(self):
        base = {"strategy": "random", "shock_fraction": .01, "initial_failures": 1,
                "mean_additional_failures": 0, "mean_functional_firms_pct": 99,
                "mean_amplification": 1, "min_total_failures": 1, "max_total_failures": 9,
                "shocks_with_cascade": 0, "mean_propagation_rounds": 2}
        return [{**base, "version": version, "network_id": network,
                 "mean_total_failures": value, "repetitions": repetitions}
                for version, values in (("original", (5, 9)), ("pool100", (1, 9)), ("pool150", (3, 3)))
                for network, value, repetitions in (("N01", values[0], 1), ("N02", values[1], 9))]

    def test_equal_network_weights_and_separate_versions(self):
        summary = summarize_versions(self.rows())
        self.assertEqual({r["version"]: r["mean_total_failures"] for r in summary},
                         {"original": 7, "pool100": 5, "pool150": 3})
        self.assertTrue(all(r["mean_propagation_rounds"] == 2 for r in summary))

    def test_missing_version_or_duplicate_summary_is_rejected(self):
        rows = self.rows()
        with self.assertRaises(ValueError):
            summarize_versions(rows[:-1])
        with self.assertRaises(ValueError):
            summarize_versions(rows + [rows[0]])
