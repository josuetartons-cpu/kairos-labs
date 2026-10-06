'Check separate assignments and descriptive aggregation.'

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from network import build_layered_network
from robustness import build_assignment, summarize_assignments


class RobustnessTests(unittest.TestCase):
    def test_assignments_start_from_original_with_fixed_seeds_and_one_extra_supplier(self):
        original = build_layered_network()
        before = original.copy()
        variants = [build_assignment(original, assignment, 2) for assignment in ("R2", "R3")]
        self.assertEqual([g.graph["redundancy_seed"] for g in variants], [7002, 8002])
        self.assertNotEqual(set(variants[0].edges), set(variants[1].edges))
        self.assertEqual(set(variants[0].edges), set(build_assignment(original, "R2", 2).edges))
        for variant in variants:
            self.assertEqual(dict(variant.nodes(data=True)), dict(original.nodes(data=True)))
            self.assertEqual(variant.number_of_edges() - original.number_of_edges(), 80)
            self.assertTrue(set(original.edges).issubset(variant.edges))
            for firm in original:
                self.assertEqual(variant.in_degree(firm) - original.in_degree(firm), int(original.in_degree(firm) > 0))
        self.assertEqual(set(original.edges), set(before.edges))
        self.assertEqual(original.graph, before.graph)

    def rows(self):
        base = {"strategy": "random", "shock_fraction": .01, "initial_failures": 1,
                "mean_additional_failures": 0, "mean_functional_firms_pct": 99,
                "mean_amplification": 1, "min_total_failures": 1,
                "max_total_failures": 9, "shocks_with_cascade": 0,
                "original_mean_total_failures": 10}
        return [{**base, "assignment": assignment, "network_id": network,
                 "mean_total_failures": value, "repetitions": repetitions}
                for assignment, values in (("R1", (1, 9)), ("R2", (3, 3)), ("R3", (5, 1)))
                for network, value, repetitions in (("N01", values[0], 1), ("N02", values[1], 9))]

    def test_equal_network_weights_and_global_range_distinct_from_network_range(self):
        summary, networks, comparison = summarize_assignments(self.rows())
        self.assertEqual({r["assignment"]: r["mean_total_failures"] for r in summary},
                         {"R1": 5, "R2": 3, "R3": 3})
        self.assertEqual(comparison[0]["min_assignment_mean_total_failures"], 3)
        self.assertEqual(comparison[0]["max_assignment_mean_total_failures"], 5)
        self.assertEqual(comparison[0]["max_network_assignment_mean_span"], 8)
        self.assertEqual(comparison[0]["networks_with_all_assignment_means_below_original"], 2)
        self.assertEqual(len(networks), 2)

    def test_missing_assignment_or_different_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize_assignments(self.rows()[:-1])
        rows = self.rows()
        rows[0]["original_mean_total_failures"] = 11
        with self.assertRaises(ValueError):
            summarize_assignments(rows)
