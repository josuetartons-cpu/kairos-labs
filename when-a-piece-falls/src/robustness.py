'Sensitivity to two new alternative-supplier assignments; saved shocks.'

import csv
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

import networkx as nx

from experiments import summarize_shocks, summarize_networks, write_csv
from redundancy import (add_alternative_suppliers, compare_saved_shock,
                        read_rows, read_saved_network_pairs)


def build_assignment(original, assignment, network_index):
    'Each variant starts from the original network without accumulating alternatives.'
    bases = {"R2": 7000, "R3": 8000}
    if assignment not in bases or not 0 <= network_index < 20:
        raise ValueError('Assignment R2/R3 and network index 0..19 are required.')
    seed = bases[assignment] + network_index
    return add_alternative_suppliers(original, seed)


def summarize_assignments(per_network):
    'Assignment means and descriptive ranges across R1/R2/R3.\n\n    Each network has equal weight within an assignment. The global range\n    covers three means of twenty networks; network-level ranges are\n    exported separately.\n    '
    groups = defaultdict(list)
    for row in per_network:
        groups[row["assignment"], row["strategy"]].append(row)
    summaries = []
    for (assignment, strategy), rows in sorted(groups.items()):
        summaries.extend({"assignment": assignment, "strategy": strategy, **r}
                         for r in summarize_networks(rows))
    by_network = defaultdict(list)
    for row in per_network:
        by_network[row["strategy"], row["network_id"], row["shock_fraction"]].append(row)
    network_ranges = []
    for (strategy, key, fraction), rows in sorted(by_network.items()):
        if len(rows) != 3 or {r["assignment"] for r in rows} != {"R1", "R2", "R3"}:
            raise ValueError('Each network/severity/strategy must have R1/R2/R3.')
        baselines = {r["original_mean_total_failures"] for r in rows}
        if len(baselines) != 1:
            raise ValueError('Assignments must share the same reference.')
        totals = [r["mean_total_failures"] for r in rows]
        baseline = rows[0]["original_mean_total_failures"]
        network_ranges.append({
            "strategy": strategy, "network_id": key, "shock_fraction": fraction,
            "original_mean_total_failures": baseline,
            "min_assignment_mean_total_failures": min(totals),
            "max_assignment_mean_total_failures": max(totals),
            "assignment_mean_total_span": max(totals) - min(totals),
            "all_assignment_means_below_original": all(value < baseline for value in totals),
        })
    comparison = []
    for strategy in sorted({r["strategy"] for r in summaries}):
        for fraction in sorted({r["shock_fraction"] for r in summaries}):
            rows = [r for r in summaries if r["strategy"] == strategy and r["shock_fraction"] == fraction]
            if len(rows) != 3:
                raise ValueError('Three summaries per strategy/severity are required.')
            networks = [r for r in network_ranges if r["strategy"] == strategy and r["shock_fraction"] == fraction]
            totals = [r["mean_total_failures"] for r in rows]
            comparison.append({
                "strategy": strategy, "shock_fraction": fraction,
                "initial_failures": rows[0]["initial_failures"],
                "original_mean_total_failures": mean(r["original_mean_total_failures"] for r in networks),
                "R1_mean_total_failures": next(r["mean_total_failures"] for r in rows if r["assignment"] == "R1"),
                "R2_mean_total_failures": next(r["mean_total_failures"] for r in rows if r["assignment"] == "R2"),
                "R3_mean_total_failures": next(r["mean_total_failures"] for r in rows if r["assignment"] == "R3"),
                "min_assignment_mean_total_failures": min(totals),
                "max_assignment_mean_total_failures": max(totals),
                "max_network_assignment_mean_span": max(r["assignment_mean_total_span"] for r in networks),
                "networks_with_all_assignment_means_below_original": sum(r["all_assignment_means_below_original"] for r in networks),
            })
    return summaries, network_ranges, comparison


def run_robustness():
    '32,000 new cases; R1 is read without rerunning it.'
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "redundancy1000_robustness_"
    names = ("shocks.csv", "rounds.csv", "edges.csv", "manifest.csv", "per_network.csv",
             "summary.csv", "network_ranges.csv", "comparison.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Robustness results already exist; they will not be overwritten.')
    originals, _ = read_saved_network_pairs(output)
    sources = (("random", "networks1000_shocks.csv"),
               ("targeted_original_out_degree", "targeted1000_shocks.csv"))
    saved = []
    expected = {(key, fraction, repetition) for key in originals
                for fraction in (.01, .05, .10, .20) for repetition in range(1, 101)}
    for strategy, filename in sources:
        rows = read_rows(output / filename)
        keys = {(r["network_id"], float(r["shock_fraction"]), int(r["repetition"])) for r in rows}
        if len(rows) != 8000 or keys != expected:
            raise ValueError('8,000 original shocks per strategy are required.')
        if any(int(r["initial_failures"]) != round(1000 * float(r["shock_fraction"])) for r in rows):
            raise ValueError('Severity does not match the initial count.')
        saved.extend((strategy, row) for row in rows)
    # R1: reuse its summaries without duplicating or overwriting its batch.
    per_network = []
    for row in read_rows(output / "redundancy1000_joint_per_network.csv"):
        if row["version"] != "redundant":
            continue
        parsed = {key: value if key in ("strategy", "network_id") else float(value)
                  for key, value in row.items() if key != "version"}
        per_network.append({"assignment": "R1", **parsed})
    baseline_means = {}
    for strategy, filename in sources:
        grouped = defaultdict(list)
        for row in read_rows(output / filename):
            grouped[row["network_id"], float(row["shock_fraction"])].append(int(row["total_failures"]))
        baseline_means.update({(strategy, key, fraction): mean(totals)
                               for (key, fraction), totals in grouped.items()})
    for row in per_network:
        row["original_mean_total_failures"] = baseline_means[row["strategy"], row["network_id"], row["shock_fraction"]]
    if len(per_network) != 160:
        raise ValueError('R1 must contain 160 redundant per-network summaries.')
    cases, edges, manifest = [], [], []
    round_count = 0
    started = perf_counter()
    with (output / f"{prefix}rounds.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("assignment", "strategy", "network_id", "shock_fraction", "repetition", "round", "firm"))
        writer.writeheader()
        for assignment in ("R2", "R3"):
            variants = {}
            for index, (key, original) in enumerate(originals.items()):
                variant = build_assignment(original, assignment, index)
                variants[key] = variant
                manifest.append({"assignment": assignment, "network_id": key,
                                 "redundancy_seed": variant.graph["redundancy_seed"],
                                 "n": len(variant), "original_edges": original.number_of_edges(),
                                 "added_edges": variant.number_of_edges() - original.number_of_edges()})
                edges.extend({"assignment": assignment, "network_id": key,
                              "supplier": a, "customer": b, "added": not original.has_edge(a, b)}
                             for a, b in sorted(variant.edges))
            grouped = defaultdict(list)
            for strategy, reference in saved:
                key, fraction = reference["network_id"], float(reference["shock_fraction"])
                baseline, result, rounds = compare_saved_shock(originals[key], variants[key], reference)
                common = {"assignment": assignment, "strategy": strategy, "network_id": key, "shock_fraction": fraction}
                cases.append({**common, "selection_seed": int(reference.get("shock_seed", reference.get("tie_seed"))),
                              **result, "original_total_failures": baseline["total_failures"],
                              "difference_total_failures": result["total_failures"] - baseline["total_failures"]})
                grouped[strategy, key, fraction].append(result)
                for number, firms in enumerate(rounds):
                    writer.writerows({**common, "repetition": result["repetition"], "round": number, "firm": firm} for firm in firms)
                    round_count += len(firms)
            for (strategy, key, fraction), rows in sorted(grouped.items()):
                summary = summarize_shocks(rows, fraction, shock_seed=0)
                del summary["shock_seed"]
                per_network.append({"assignment": assignment, "strategy": strategy, "network_id": key,
                                    **summary, "original_mean_total_failures": baseline_means[strategy, key, fraction]})
    summaries, network_ranges, comparison = summarize_assignments(per_network)
    for name, rows in (("shocks", cases), ("edges", edges), ("manifest", manifest),
                       ("per_network", per_network), ("summary", summaries),
                       ("network_ranges", network_ranges), ("comparison", comparison)):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "sensitivity_to_alternative_supplier_assignment",
        "n": 1000, "original_networks": 20, "assignments_per_network": 3,
        "new_executions": len(cases), "baseline_replays_for_validation": len(cases),
        "failure_round_records": round_count,
        "seed_rules": {"R1": "6000+i; saved", "R2": "7000+i", "R3": "8000+i"},
        "network_index": "i=0..19; N01..N20",
        "intervention": "one_alternative_per_non_source; each_assignment_starts_from_original",
        "R1_references": ["redundancy1000_edges.csv", "redundancy1000_joint_per_network.csv"],
        "shock_references": [filename for _, filename in sources],
        "pairing": "same_original_network_and_initial_firms_across_assignments; original_targeted_ranking_fixed",
        "aggregation": "100_shocks_per_network_then_equal_weight_across_20_networks_per_assignment",
        "ranges": "descriptive_min_max_of_three_assignments; not_confidence_intervals",
        "limits": "assignment_sensitivity_only; same_topology_family_cascade_rule_and_shocks; no_costs_capacity_or_real_economy_inference",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in comparison:
        print(f"{row['strategy']} {100 * row['shock_fraction']:.0f}%: "
              f"F original={row['original_mean_total_failures']:.4f}; "
              f"R1={row['R1_mean_total_failures']:.4f}; "
              f"R2={row['R2_mean_total_failures']:.4f}; R3={row['R3_mean_total_failures']:.4f}")
    print(f"New executions: {len(cases)}; failure records: {round_count}")
    print(f"Local time: {perf_counter() - started:.3f} s")


if __name__ == "__main__":
    run_robustness()
