'One alternative supplier per customer; validate individual withdrawals.'

import csv
from collections import defaultdict
import json
from pathlib import Path
import random
import sys
from time import perf_counter

import networkx as nx

from individual import evaluate_firms, summarize_cases
from cascades import run_cascade
from experiments import cascade_record, summarize_shocks, summarize_networks, write_csv


def add_alternative_suppliers(graph, seed):
    'Copy the network and uniformly select a new previous-layer supplier.\n\n    Preserve firms, attributes and original links. Each customer must have\n    at least one candidate distinct from its current suppliers.\n    '
    if not graph.is_directed() or graph.is_multigraph():
        raise ValueError('A simple directed graph is required.')
    layers = {firm: attrs["layer"] for firm, attrs in graph.nodes(data=True)}
    if any(layers[b] != layers[a] + 1 for a, b in graph.edges):
        raise ValueError('Edges must come from the immediately preceding layer.')
    rng = random.Random(seed)
    redundant = graph.copy()
    for customer in sorted(graph):
        suppliers = set(graph.predecessors(customer))
        if not suppliers:
            continue
        candidates = sorted(firm for firm in graph
                            if layers[firm] == layers[customer] - 1
                            and firm not in suppliers)
        if not candidates:
            raise ValueError(f"{customer} has no alternative supplier available.")
        redundant.add_edge(rng.choice(candidates), customer)
    redundant.graph["redundancy_seed"] = seed
    return redundant


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def run_individual_validation():
    "Read the exact saved networks and write only this stage's outputs."
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "redundancy1000_"
    names = ("cases.csv", "edges.csv", "manifest.csv", "per_network.csv",
             "summary.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Redundancy results already exist; they will not be overwritten.')
    graphs = {f"N{i + 1:02d}": nx.DiGraph() for i in range(20)}
    for row in read_rows(output / "networks1000_nodes.csv"):
        graphs[row["network_id"]].add_node(
            row["firm"], layer=int(row["layer"]), size=int(row["size"]),
            active=row["active"] == "True")
    for row in read_rows(output / "networks1000_edges.csv"):
        graphs[row["network_id"]].add_edge(row["supplier"], row["customer"])
    reference_rows = read_rows(output / "individual1000_cases.csv")
    reference = {(r["network_id"], r["firm"]): r for r in reference_rows}
    expected = {(network_id, firm) for network_id, graph in graphs.items() for firm in graph}
    if len(reference_rows) != 20000 or len(reference) != 20000 or set(reference) != expected:
        raise ValueError('The reference census does not match the twenty networks.')
    cases, edges, manifest, per_network = [], [], [], []
    for index, (network_id, graph) in enumerate(graphs.items()):
        if len(graph) != 1000 or sum(graph.in_degree(f) == 0 for f in graph) != 200:
            raise ValueError('The reference must have 1,000 firms and 200 sources per network.')
        seed = 6000 + index  # Fixed before running the comparison.
        redundant = add_alternative_suppliers(graph, seed)
        records, _ = evaluate_firms(redundant)
        for row in records:
            if row["failed_firms"] != row["firm"] or row["total_failures"] != 1:
                raise AssertionError('An individual withdrawal produced propagation.')
            original = reference[network_id, row["firm"]]
            if any(int(original[key]) != graph.nodes[row["firm"]][key]
                   for key in ("layer", "size")):
                raise ValueError('Attributes do not match the original census.')
            cases.append({"network_id": network_id, **row,
                          "original_additional_failures": int(original["additional_failures"]),
                          "difference_additional_failures": row["additional_failures"] - int(original["additional_failures"])})
        edges.extend({"network_id": network_id, "supplier": a, "customer": b,
                      "added": not graph.has_edge(a, b)}
                     for a, b in sorted(redundant.edges))
        manifest.append({"network_id": network_id, "n": len(graph),
                         "original_edges": graph.number_of_edges(),
                         "redundant_edges": redundant.number_of_edges(),
                         "added_edges": redundant.number_of_edges() - graph.number_of_edges(),
                         "redundancy_seed": seed})
        per_network.append({"network_id": network_id, **summarize_cases(records)})
    summary = summarize_cases(cases)
    for name, rows in (("cases", cases), ("edges", edges), ("manifest", manifest),
                       ("per_network", per_network), ("summary", [summary])):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "added_alternative_suppliers_single_withdrawal_validation",
        "n": 1000, "networks": 20, "cases": len(cases),
        "redundancy_seed_rule": "6000 + network_index; index=0..19",
        "selection": "sorted_customers; uniform_choice_from_sorted_previous_layer_non_suppliers",
        "intervention": "one_new_supplier_per_non_source; preserve_original_edges_and_node_attributes",
        "node_reference": "networks1000_nodes.csv",
        "edge_reference": "networks1000_edges.csv",
        "case_reference": "individual1000_cases.csv",
        "weighting": "equal_case_weights; equal_network_weights_because_1000_cases_each",
        "difference": "redundant_minus_original_additional_failures",
        "cascade_rule": "unchanged_complete_substitution",
        "interpretation": "zero_secondary_failures_is_implied_by_minimum_two_distinct_suppliers",
        "limits": "no_joint_shocks; no_costs; no_equal_edge_count_concentration_comparison; no_real_economy_inference",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary)
    print(f"Additional links: {sum(r['added_edges'] for r in manifest)}")


def compare_saved_shock(original, redundant, reference):
    'Reuse the saved shock, validate the reference and compare final failures.\n\n    Do not redraw firms or rerank them. Reproduce the original cascade\n    to verify that the CSV belongs to the network being used.\n    '
    firms = reference["initial_firms"].split("|")
    initial = set(firms)
    if len(firms) != len(initial) or len(initial) != int(reference["initial_failures"]):
        raise ValueError('The saved shock contains duplicates or an incorrect count.')
    repetition = int(reference["repetition"])
    baseline_rounds = run_cascade(original, initial)
    baseline = cascade_record(original, initial, baseline_rounds, repetition)
    for key, value in baseline.items():
        saved = reference[key]
        if isinstance(value, str):
            matches = saved == value
        else:
            matches = float(saved) == value
        if not matches:
            raise ValueError(f"The reference does not match the original network: {key}.")
    rounds = run_cascade(redundant, initial)
    result = cascade_record(redundant, initial, rounds, repetition)
    original_failed = set(baseline["failed_firms"].split("|"))
    redundant_failed = set(result["failed_firms"].split("|"))
    if not redundant_failed.issubset(original_failed):
        raise AssertionError('Adding substitutes produced new final failures.')
    return baseline, result, rounds


def read_saved_network_pairs(output):
    'Reconstruct both versions from their files without new random draws.'
    original = {f"N{i + 1:02d}": nx.DiGraph() for i in range(20)}
    for row in read_rows(output / "networks1000_nodes.csv"):
        original[row["network_id"]].add_node(
            row["firm"], layer=int(row["layer"]), size=int(row["size"]),
            active=row["active"] == "True")
    for row in read_rows(output / "networks1000_edges.csv"):
        graph = original[row["network_id"]]
        if row["supplier"] not in graph or row["customer"] not in graph:
            raise ValueError('An original edge contains unknown firms.')
        graph.add_edge(row["supplier"], row["customer"])
    redundant = {key: graph.copy() for key, graph in original.items()}
    for graph in redundant.values():
        graph.remove_edges_from(list(graph.edges))
    for row in read_rows(output / "redundancy1000_edges.csv"):
        graph = redundant[row["network_id"]]
        if row["supplier"] not in graph or row["customer"] not in graph:
            raise ValueError('A redundant edge contains unknown firms.')
        graph.add_edge(row["supplier"], row["customer"])
    for key, graph in original.items():
        variant = redundant[key]
        if len(graph) != 1000 or sum(graph.in_degree(f) == 0 for f in graph) != 200:
            raise ValueError('Twenty networks of 1,000 firms and 200 sources are required.')
        if not set(graph.edges).issubset(variant.edges):
            raise ValueError('The variant is missing original edges.')
        for firm in graph:
            added = set(variant.predecessors(firm)) - set(graph.predecessors(firm))
            if len(added) != int(graph.in_degree(firm) > 0):
                raise ValueError('Each non-source must have one new alternative.')
        if any(variant.nodes[b]["layer"] != variant.nodes[a]["layer"] + 1
               for a, b in variant.edges):
            raise ValueError('Redundant edges do not respect the layers.')
    return original, redundant


def run_joint_comparison():
    'Compare 16,000 saved shocks; stream round records without accumulating them.'
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "redundancy1000_joint_"
    names = ("shocks.csv", "rounds.csv", "per_network.csv", "summary.csv",
             "comparison.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Joint results already exist; they will not be overwritten.')
    original, redundant = read_saved_network_pairs(output)
    sources = (("random", "networks1000_shocks.csv"),
               ("targeted_original_out_degree", "targeted1000_shocks.csv"))
    saved = []
    expected = {(key, fraction, repetition) for key in original
                for fraction in (.01, .05, .10, .20) for repetition in range(1, 101)}
    for strategy, filename in sources:
        rows = read_rows(output / filename)
        keys = {(r["network_id"], float(r["shock_fraction"]), int(r["repetition"])) for r in rows}
        if len(rows) != 8000 or keys != expected:
            raise ValueError('8,000 original shocks per strategy are required.')
        for row in rows:
            if int(row["initial_failures"]) != round(1000 * float(row["shock_fraction"])):
                raise ValueError('Severity does not match the initial count.')
        saved.extend((strategy, row) for row in rows)
    shock_rows, grouped = [], defaultdict(list)
    round_count = 0
    started = perf_counter()
    with (output / f"{prefix}rounds.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("strategy", "network_id", "shock_fraction", "repetition", "round", "firm"))
        writer.writeheader()
        for strategy, row in saved:
            key, fraction = row["network_id"], float(row["shock_fraction"])
            baseline, result, rounds = compare_saved_shock(original[key], redundant[key], row)
            common = {"strategy": strategy, "network_id": key, "shock_fraction": fraction}
            shock_rows.append({**common, "selection_seed": int(row.get("shock_seed", row.get("tie_seed"))),
                               **result,
                               "original_total_failures": baseline["total_failures"],
                               "original_additional_failures": baseline["additional_failures"],
                               "original_failed_firms": baseline["failed_firms"],
                               "difference_total_failures": result["total_failures"] - baseline["total_failures"]})
            grouped[strategy, key, fraction, "original"].append(baseline)
            grouped[strategy, key, fraction, "redundant"].append(result)
            for number, firms in enumerate(rounds):
                writer.writerows({**common, "repetition": result["repetition"], "round": number, "firm": firm} for firm in firms)
                round_count += len(firms)
    per_network = []
    for (strategy, key, fraction, version), rows in sorted(grouped.items()):
        summary = summarize_shocks(rows, fraction, shock_seed=0)
        del summary["shock_seed"]
        per_network.append({"strategy": strategy, "version": version, "network_id": key, **summary})
    summaries = []
    for strategy, _ in sources:
        for version in ("original", "redundant"):
            rows = [r for r in per_network if r["strategy"] == strategy and r["version"] == version]
            summaries.extend({"strategy": strategy, "version": version, **r} for r in summarize_networks(rows))
    comparison = []
    for strategy, _ in sources:
        for fraction in (.01, .05, .10, .20):
            pair = {r["version"]: r for r in summaries if r["strategy"] == strategy and r["shock_fraction"] == fraction}
            base, variant = pair["original"], pair["redundant"]
            comparison.append({"strategy": strategy, "shock_fraction": fraction,
                               "initial_failures": base["initial_failures"],
                               "original_mean_total_failures": base["mean_total_failures"],
                               "redundant_mean_total_failures": variant["mean_total_failures"],
                               "original_mean_additional_failures": base["mean_additional_failures"],
                               "redundant_mean_additional_failures": variant["mean_additional_failures"],
                               "difference_mean_total_failures": variant["mean_total_failures"] - base["mean_total_failures"],
                               "redundant_mean_functional_firms_pct": variant["mean_functional_firms_pct"],
                               "redundant_mean_amplification": variant["mean_amplification"],
                               "redundant_mean_cascade_frequency_pct": variant["mean_cascade_frequency_pct"]})
    for name, rows in (("shocks", shock_rows), ("per_network", per_network),
                       ("summary", summaries), ("comparison", comparison)):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "paired_saved_joint_shocks_on_saved_redundant_networks",
        "n": 1000, "networks": 20, "new_executions": len(shock_rows),
        "baseline_replays_for_validation": len(shock_rows), "failure_round_records": round_count,
        "shock_references": [filename for _, filename in sources],
        "network_references": ["networks1000_nodes.csv", "networks1000_edges.csv", "redundancy1000_edges.csv"],
        "pairing": "same_network_same_initial_firms_same_repetition_within_strategy",
        "strategies": "random_and_targeted_original_out_degree; not_paired_between_strategies",
        "ranking": "reuse_original_targeted_selection; no_reranking_on_redundant_network",
        "randomness": "no_new_draws; existing_alternative_supplier_seeds_6000_to_6019",
        "aggregation": "mean_within_network_then_equal_weight_across_20_networks",
        "difference": "redundant_minus_original_total_failures; equal_to_additional_difference",
        "validation": "all_baselines_reproduced; redundant_final_failures_subset_of_original",
        "limits": "one_redundancy_realization_per_network; no_costs_or_capacity; no_equal_edge_count_control; no_real_economy_inference",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in comparison:
        print(f"{row['strategy']} {100 * row['shock_fraction']:.0f}%: "
              f"F original={row['original_mean_total_failures']:.4f}; "
              f"redundant F={row['redundant_mean_total_failures']:.4f}; "
              f"redundant C={row['redundant_mean_additional_failures']:.4f}")
    print(f"New executions: {len(shock_rows)}; failure records: {round_count}")
    print(f"Simulation, validation and writing time: {perf_counter() - started:.3f} s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint", action="store_true", help='Reuse saved joint shocks on saved variants')
    args = parser.parse_args()
    if args.joint:
        run_joint_comparison()
    else:
        run_individual_validation()
