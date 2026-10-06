'Approved sensitivity: pools of 100 versus 150 eligible suppliers.'

import csv
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

import networkx as nx

from concentration import (build_concentrated_network, compare_concentration_shock,
                           read_concentrated_networks, read_original_networks, supplier_hhi)
from experiments import summarize_shocks, summarize_networks, write_csv
from redundancy import read_rows


def build_sensitivity_variant(original, index):
    'Start from the original with 150 eligible suppliers and a fixed seed, not from pool100.'
    if not isinstance(index, int) or not 0 <= index < 20:
        raise ValueError('Network index 0..19 is required.')
    return build_concentrated_network(original, 150, 10000 + index)


def summarize_versions(per_network):
    'Equal network weights; three versions per strategy, network and severity.'
    keys = {(r["strategy"], r["network_id"], r["shock_fraction"], r["version"]) for r in per_network}
    if len(keys) != len(per_network):
        raise ValueError('Duplicate per-network summaries.')
    conditions = {(r["strategy"], r["network_id"], r["shock_fraction"]) for r in per_network}
    for strategy, key, fraction in conditions:
        versions = {r["version"] for r in per_network if (r["strategy"], r["network_id"], r["shock_fraction"]) == (strategy, key, fraction)}
        if versions != {"original", "pool100", "pool150"}:
            raise ValueError('Each condition must include original, pool100 and pool150.')
    summaries = []
    for strategy in sorted({r["strategy"] for r in per_network}):
        for version in ("original", "pool100", "pool150"):
            rows = [r for r in per_network if r["strategy"] == strategy and r["version"] == version]
            for summary in summarize_networks(rows):
                group = [r for r in rows if r["shock_fraction"] == summary["shock_fraction"]]
                summaries.append({"strategy": strategy, "version": version, **summary,
                                  "mean_propagation_rounds": mean(r["mean_propagation_rounds"] for r in group)})
    return summaries


def run_sensitivity():
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "concentration1000_sensitivity_"
    names = ("edges.csv", "pools.csv", "benchmark.csv", "shocks.csv", "rounds.csv",
             "per_network.csv", "summary.csv", "comparison.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Structural-sensitivity results already exist; they will not be overwritten.')
    originals = read_original_networks(output)
    pool100 = read_concentrated_networks(output, originals)
    variants, edges, pools, benchmark = {}, [], [], []
    for index, (key, original) in enumerate(originals.items()):
        variant, selected = build_sensitivity_variant(original, index)
        variants[key] = variant
        if dict(variant.nodes(data=True)) != dict(original.nodes(data=True)) or dict(variant.in_degree()) != dict(original.in_degree()):
            raise AssertionError('A node, attribute or supplier-count control changed.')
        edges.extend({"network_id": key, "supplier": a, "customer": b} for a, b in sorted(variant.edges))
        pools.extend({"network_id": key, "supplier_layer": layer, "firm": firm}
                     for layer, firms in selected.items() for firm in firms)
        for version, graph in (("original", original), ("pool100", pool100[key]), ("pool150", variant)):
            for layer in range(4):
                row = supplier_hhi(graph, layer)
                if row["edges"] != supplier_hhi(original, layer)["edges"]:
                    raise AssertionError('The edge count per transition changed.')
                benchmark.append({"network_id": key, "version": version,
                                  "eligible_suppliers": {"original": 200, "pool100": 100, "pool150": 150}[version], **row})
    saved100_rows = read_rows(output / "concentration1000_joint_shocks.csv")
    def case_key(r):
        return r["strategy"], r["network_id"], float(r["shock_fraction"]), int(r["repetition"])
    saved100 = {case_key(r): r for r in saved100_rows}
    sources = (("random", "networks1000_shocks.csv"),
               ("targeted_original_out_degree", "targeted1000_shocks.csv"))
    expected = {(key, fraction, repetition) for key in originals
                for fraction in (.01, .05, .10, .20) for repetition in range(1, 101)}
    saved = []
    for strategy, filename in sources:
        rows = read_rows(output / filename)
        keys = {(r["network_id"], float(r["shock_fraction"]), int(r["repetition"])) for r in rows}
        if len(rows) != 8000 or keys != expected:
            raise ValueError('8,000 original selections per strategy are required.')
        if any(int(r["initial_failures"]) != round(1000 * float(r["shock_fraction"])) for r in rows):
            raise ValueError('Severity does not match the initial count.')
        saved.extend((strategy, r) for r in rows)
    expected100 = {(strategy, *key) for strategy, _ in sources for key in expected}
    if len(saved100_rows) != 16000 or set(saved100) != expected100:
        raise ValueError('The pool100 reference must contain 16,000 selections.')
    per_network = []
    integer_fields = {"repetitions", "initial_failures", "shocks_with_cascade"}
    for row in read_rows(output / "concentration1000_joint_per_network.csv"):
        per_network.append({key: ("pool100" if value == "concentrated" else value) if key == "version"
                            else value if key in ("strategy", "network_id")
                            else int(value) if key in integer_fields else float(value)
                            for key, value in row.items()})
    if len(per_network) != 320:
        raise ValueError('References must contain 320 per-network summaries.')
    cases, grouped = [], {}
    round_count = 0
    started = perf_counter()
    with (output / f"{prefix}rounds.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("strategy", "network_id", "shock_fraction", "repetition", "round", "firm"))
        writer.writeheader()
        for strategy, reference in saved:
            key, fraction = reference["network_id"], float(reference["shock_fraction"])
            old100 = saved100[strategy, key, fraction, int(reference["repetition"])]
            if old100["initial_firms"] != reference["initial_firms"] or old100["original_total_failures"] != reference["total_failures"]:
                raise ValueError('Pool100 does not match the same original shock.')
            baseline, result, rounds = compare_concentration_shock(originals[key], variants[key], reference)
            common = {"strategy": strategy, "network_id": key, "shock_fraction": fraction}
            cases.append({**common, "selection_seed": int(reference.get("shock_seed", reference.get("tie_seed"))),
                          **result, "original_total_failures": baseline["total_failures"],
                          "original_propagation_rounds": baseline["propagation_rounds"],
                          "pool100_total_failures": int(old100["total_failures"]),
                          "pool100_propagation_rounds": int(old100["propagation_rounds"]),
                          "difference_vs_original": result["total_failures"] - baseline["total_failures"],
                          "difference_vs_pool100": result["total_failures"] - int(old100["total_failures"])})
            grouped.setdefault((strategy, key, fraction), []).append(result)
            for number, firms in enumerate(rounds):
                writer.writerows({**common, "repetition": result["repetition"], "round": number, "firm": firm} for firm in firms)
                round_count += len(firms)
    for (strategy, key, fraction), rows in sorted(grouped.items()):
        summary = summarize_shocks(rows, fraction, shock_seed=0)
        del summary["shock_seed"]
        per_network.append({"strategy": strategy, "version": "pool150", "network_id": key,
                            **summary, "mean_propagation_rounds": mean(r["propagation_rounds"] for r in rows)})
    summaries = summarize_versions(per_network)
    hhi = {version: mean(mean(r["hhi"] for r in benchmark if r["version"] == version and r["network_id"] == key)
                         for key in originals) for version in ("original", "pool100", "pool150")}
    comparison = []
    for strategy, _ in sources:
        for fraction in (.01, .05, .10, .20):
            pair = {r["version"]: r for r in summaries if r["strategy"] == strategy and r["shock_fraction"] == fraction}
            group = [r for r in cases if r["strategy"] == strategy and r["shock_fraction"] == fraction]
            comparison.append({"strategy": strategy, "shock_fraction": fraction,
                               "initial_failures": pair["original"]["initial_failures"],
                               **{f"{version}_mean_total_failures": pair[version]["mean_total_failures"] for version in pair},
                               **{f"{version}_mean_hhi": hhi[version] for version in pair},
                               "difference_mean_150_vs_100": pair["pool150"]["mean_total_failures"] - pair["pool100"]["mean_total_failures"],
                               "cases_150_with_more_failures_than_100": sum(r["difference_vs_pool100"] > 0 for r in group),
                               "cases_150_with_fewer_failures_than_100": sum(r["difference_vs_pool100"] < 0 for r in group),
                               "cases_150_with_equal_failures_to_100": sum(r["difference_vs_pool100"] == 0 for r in group)})
    for name, rows in (("edges", edges), ("pools", pools), ("benchmark", benchmark), ("shocks", cases),
                       ("per_network", per_network), ("summary", summaries), ("comparison", comparison)):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "structural_sensitivity_supplier_pool_100_vs_150",
        "n": 1000, "networks": 20, "new_pool_size": 150, "baseline_pool_size": 100,
        "seed_rule": "10000+i; i=0..19; N01..N20",
        "new_executions": len(cases), "baseline_replays_for_validation": len(cases), "failure_round_records": round_count,
        "reference_files": ["networks1000_nodes.csv", "networks1000_edges.csv", "concentration1000_edges.csv", "concentration1000_joint_shocks.csv", "concentration1000_joint_per_network.csv"],
        "shock_references": [filename for _, filename in sources],
        "pairing": "same_original_network_and_initial_firms; fixed_original_targeted_selection",
        "construction": "same_uniform_pool_method; new_seeds; pools_and_edges_not_required_to_be_nested",
        "controls": "same_nodes_attributes_layers_in_degree_per_customer_and_edges_per_transition",
        "aggregation": "100_shocks_within_network_then_equal_weight_across_20_networks_per_version; HHI_equal_weight_across_transitions_and_networks",
        "scope": "two_pool_sizes_and_one_assignment_each; does_not_isolate_parameter_from_assignment_randomness",
        "limits": "no_general_robustness_or_HHI_only_causal_effect; no_adapted_targeting; no_costs",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print('Mean HHI:', "; ".join(f"{version}={value:.8f}" for version, value in hhi.items()))
    for row in comparison:
        print(f"{row['strategy']} {100 * row['shock_fraction']:.0f}%: "
              f"F original={row['original_mean_total_failures']:.4f}; "
              f"F pool100={row['pool100_mean_total_failures']:.4f}; F pool150={row['pool150_mean_total_failures']:.4f}")
    print(f"New executions: {len(cases)}; failure records: {round_count}")
    print(f"Local simulation, validation and writing time: {perf_counter() - started:.3f} s")


if __name__ == "__main__":
    run_sensitivity()
