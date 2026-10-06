'Construction, HHI and saved-shock comparison for concentrated networks.'

import csv
from collections import defaultdict
import json
from pathlib import Path
import random
from statistics import mean
import sys
from time import perf_counter

import networkx as nx

from cascades import run_cascade
from experiments import cascade_record, summarize_shocks, summarize_networks, write_csv
from redundancy import read_rows


def build_concentrated_network(original, pool_size, seed):
    "Reassign suppliers while preserving each customer's in-degree.\n\n    Sample an eligible supplier pool uniformly in each layer 0..3.\n    Each customer selects distinct pool members without weights.\n    Return a copy and four pools without modifying the original.\n    "
    if not original.is_directed() or original.is_multigraph():
        raise ValueError('A simple directed graph is required.')
    layers = defaultdict(list)
    for firm, attrs in original.nodes(data=True):
        layers[attrs["layer"]].append(firm)
    if set(layers) != set(range(5)):
        raise ValueError('Five layers numbered 0..4 are required.')
    if any(original.nodes[b]["layer"] != original.nodes[a]["layer"] + 1
           for a, b in original.edges):
        raise ValueError('Each edge must come from the previous layer.')
    if not isinstance(pool_size, int) or isinstance(pool_size, bool) or pool_size < 1:
        raise ValueError('pool_size must be a positive integer.')
    if any(pool_size > len(layers[layer]) for layer in range(4)):
        raise ValueError('The pool exceeds the firms available in a layer.')
    if any(original.in_degree(firm) > pool_size for firm in original):
        raise ValueError('The pool cannot preserve distinct suppliers for each customer.')
    if any(original.in_degree(firm) == 0 for layer in range(1, 5) for firm in layers[layer]):
        raise ValueError('Only the first layer may contain sources.')
    rng = random.Random(seed)
    pools = {layer: sorted(rng.sample(sorted(layers[layer]), pool_size))
             for layer in range(4)}
    concentrated = original.copy()
    concentrated.remove_edges_from(list(concentrated.edges))
    for customer in sorted(original):
        count = original.in_degree(customer)
        if count:
            layer = original.nodes[customer]["layer"]
            concentrated.add_edges_from((supplier, customer)
                                        for supplier in rng.sample(pools[layer - 1], count))
    concentrated.graph.update(concentration_seed=seed, supplier_pool_size=pool_size)
    return concentrated, pools


def supplier_hhi(graph, supplier_layer):
    'HHI in [0,1] of link shares, including suppliers with zero clients.\n\n    Count relationships, not sales value or economic volume.\n    HHI is undefined for an edge-free transition, which is rejected.\n    '
    suppliers = [firm for firm, attrs in graph.nodes(data=True)
                 if attrs["layer"] == supplier_layer]
    counts = [sum(graph.nodes[customer]["layer"] == supplier_layer + 1
                  for customer in graph.successors(firm)) for firm in suppliers]
    total = sum(counts)
    if total == 0:
        raise ValueError('HHI is undefined for a transition without edges.')
    return {"supplier_layer": supplier_layer, "customer_layer": supplier_layer + 1,
            "edges": total, "potential_suppliers": len(suppliers),
            "suppliers_with_clients": sum(count > 0 for count in counts),
            "hhi": sum(count * count for count in counts) / (total * total)}


def read_original_networks(output):
    'Read the twenty exact references without generating new networks.'
    graphs = {f"N{i + 1:02d}": nx.DiGraph() for i in range(20)}
    nodes = read_rows(output / "networks1000_nodes.csv")
    edges = read_rows(output / "networks1000_edges.csv")
    seen = set()
    for row in nodes:
        key = row["network_id"], row["firm"]
        if key in seen:
            raise ValueError('Duplicate node in the reference.')
        seen.add(key)
        if row["active"] != "True":
            raise ValueError('The reference must initially be active.')
        graphs[row["network_id"]].add_node(row["firm"], layer=int(row["layer"]),
                                           size=int(row["size"]), active=True)
    seen = set()
    for row in edges:
        key = row["network_id"], row["supplier"], row["customer"]
        graph = graphs[row["network_id"]]
        if key in seen or row["supplier"] not in graph or row["customer"] not in graph:
            raise ValueError('Duplicate edge or unknown firm in the reference.')
        seen.add(key)
        graph.add_edge(row["supplier"], row["customer"])
    manifest = read_rows(output / "networks1000_manifest.csv")
    if len(manifest) != 20 or {r["network_id"] for r in manifest} != set(graphs):
        raise ValueError('The manifest must identify the twenty original networks.')
    for row in manifest:
        graph = graphs[row["network_id"]]
        if len(graph) != 1000 or graph.number_of_edges() != int(row["edges"]):
            raise ValueError('Counts do not match the reference.')
        if any(sum(attrs["layer"] == layer for _, attrs in graph.nodes(data=True)) != 200
               for layer in range(5)):
            raise ValueError('Five layers of 200 firms are required.')
    return graphs


def run_construction():
    'Construct twenty variants and export diagnostics without cascades.'
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "concentration1000_"
    names = ("edges.csv", "pools.csv", "per_layer.csv", "per_network.csv",
             "summary.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Concentration results already exist; they will not be overwritten.')
    graphs = read_original_networks(output)
    edges, pools, per_layer, per_network = [], [], [], []
    for index, (key, original) in enumerate(graphs.items()):
        seed = 9000 + index
        concentrated, selected = build_concentrated_network(original, pool_size=100, seed=seed)
        if dict(original.in_degree()) != dict(concentrated.in_degree()):
            raise AssertionError("A customer's supplier count changed.")
        if dict(original.nodes(data=True)) != dict(concentrated.nodes(data=True)):
            raise AssertionError('Firms or attributes changed.')
        edges.extend({"network_id": key, "supplier": a, "customer": b}
                     for a, b in sorted(concentrated.edges))
        pools.extend({"network_id": key, "supplier_layer": layer, "firm": firm}
                     for layer, firms in selected.items() for firm in firms)
        diagnostics = {}
        for version, graph in (("original", original), ("concentrated", concentrated)):
            rows = [supplier_hhi(graph, layer) for layer in range(4)]
            diagnostics[version] = rows
            per_layer.extend({"network_id": key, "version": version,
                              "eligible_suppliers": 200 if version == "original" else 100,
                              **row} for row in rows)
        if any(a["edges"] != b["edges"] for a, b in zip(diagnostics["original"], diagnostics["concentrated"])):
            raise AssertionError('The edge count per transition changed.')
        original_hhi = mean(r["hhi"] for r in diagnostics["original"])
        concentrated_hhi = mean(r["hhi"] for r in diagnostics["concentrated"])
        per_network.append({"network_id": key, "concentration_seed": seed,
                            "pool_size": 100, "n": len(original), "edges": original.number_of_edges(),
                            "original_mean_hhi": original_hhi, "concentrated_mean_hhi": concentrated_hhi,
                            "difference_mean_hhi": concentrated_hhi - original_hhi})
    summary = {"networks": 20, "pool_size": 100,
               "original_mean_hhi": mean(r["original_mean_hhi"] for r in per_network),
               "concentrated_mean_hhi": mean(r["concentrated_mean_hhi"] for r in per_network),
               "min_concentrated_network_mean_hhi": min(r["concentrated_mean_hhi"] for r in per_network),
               "max_concentrated_network_mean_hhi": max(r["concentrated_mean_hhi"] for r in per_network),
               "networks_with_higher_hhi": sum(r["difference_mean_hhi"] > 0 for r in per_network)}
    for name, rows in (("edges", edges), ("pools", pools), ("per_layer", per_layer),
                       ("per_network", per_network), ("summary", [summary])):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "concentrated_supplier_pool_construction_and_benchmark_only",
        "n": 1000, "networks": 20, "pool_size": 100, "potential_suppliers_per_layer": 200,
        "concentration_seed_rule": "9000+i; i=0..19; N01..N20",
        "selection": "sample_sorted_layers_0_to_3_first; then_sorted_customers_sample_sorted_pool",
        "controls": "same_nodes_attributes_in_degree_per_customer_edges_per_transition; no_original_mutation",
        "hhi": "sum_supplier_squared_client_counts / transition_edge_count_squared; scale_0_to_1; zero_client_suppliers_included",
        "aggregation": "equal_weight_mean_of_four_transition_HHIs_per_network; equal_weight_mean_of_twenty_networks",
        "references": ["networks1000_nodes.csv", "networks1000_edges.csv", "networks1000_manifest.csv"],
        "node_reference": "networks1000_nodes.csv; attributes_unchanged",
        "new_shock_executions": 0,
        "future_shocks": "pending_review; same_saved_random_and_original_targeted_initial_sets; no_reranking",
        "limits": "relationships_not_sales; topology_and_supplier_identity_change; no_resilience_result_yet; no_costs",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Variants: {len(graphs)}; preserved links: {len(edges)}; new shocks: 0")
    print(f"Original mean HHI: {summary['original_mean_hhi']:.8f}")
    print(f"Concentrated mean HHI: {summary['concentrated_mean_hhi']:.8f}")
    print(f"Networks with higher HHI: {summary['networks_with_higher_hhi']}/20")


def compare_concentration_shock(original, concentrated, reference):
    'Validate the reference and apply the same shock; allow either more or less damage.\n\n    Rewiring does not preserve original supplier sets. Therefore, the\n    failure-set inclusion required when adding redundancy does not apply.\n    '
    firms = reference["initial_firms"].split("|")
    initial = set(firms)
    if len(initial) != len(firms) or len(initial) != int(reference["initial_failures"]):
        raise ValueError('The saved shock contains duplicates or an incorrect count.')
    repetition = int(reference["repetition"])
    baseline = cascade_record(original, initial, run_cascade(original, initial), repetition)
    for key, value in baseline.items():
        saved = reference[key]
        if (saved != value if isinstance(value, str) else float(saved) != value):
            raise ValueError(f"The reference does not match the original network: {key}.")
    rounds = run_cascade(concentrated, initial)
    result = cascade_record(concentrated, initial, rounds, repetition)
    return baseline, result, rounds


def read_concentrated_networks(output, originals):
    'Reconstruct saved graphs and check construction controls.'
    variants = {key: graph.copy() for key, graph in originals.items()}
    for graph in variants.values():
        graph.remove_edges_from(list(graph.edges))
    seen = set()
    for row in read_rows(output / "concentration1000_edges.csv"):
        key = row["network_id"], row["supplier"], row["customer"]
        graph = variants[row["network_id"]]
        if key in seen or row["supplier"] not in graph or row["customer"] not in graph:
            raise ValueError('Duplicate concentrated edge or unknown firm.')
        seen.add(key)
        graph.add_edge(row["supplier"], row["customer"])
    pools = defaultdict(set)
    for row in read_rows(output / "concentration1000_pools.csv"):
        pools[row["network_id"], int(row["supplier_layer"])].add(row["firm"])
    for key, graph in variants.items():
        original = originals[key]
        if dict(graph.in_degree()) != dict(original.in_degree()):
            raise ValueError('The supplier count per customer is not preserved.')
        for layer in range(4):
            eligible = pools[key, layer]
            if len(eligible) != 100 or any(firm not in original or original.nodes[firm]["layer"] != layer for firm in eligible):
                raise ValueError('One hundred eligible suppliers per layer are required.')
            if supplier_hhi(graph, layer)["edges"] != supplier_hhi(original, layer)["edges"]:
                raise ValueError('Edges per transition are not preserved.')
        for supplier, customer in graph.edges:
            layer = graph.nodes[supplier]["layer"]
            if graph.nodes[customer]["layer"] != layer + 1 or supplier not in pools[key, layer]:
                raise ValueError('An edge does not respect its layer or eligible pool.')
    return variants


def run_joint_comparison():
    '16,000 saved selections on the variants; no new draws.'
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "concentration1000_joint_"
    names = ("shocks.csv", "rounds.csv", "per_network.csv", "summary.csv", "comparison.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Concentration shocks already exist; they will not be overwritten.')
    originals = read_original_networks(output)
    variants = read_concentrated_networks(output, originals)
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
        saved.extend((strategy, row) for row in rows)
    cases, grouped = [], defaultdict(list)
    round_count = 0
    started = perf_counter()
    with (output / f"{prefix}rounds.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("strategy", "network_id", "shock_fraction", "repetition", "round", "firm"))
        writer.writeheader()
        for strategy, reference in saved:
            key, fraction = reference["network_id"], float(reference["shock_fraction"])
            baseline, result, rounds = compare_concentration_shock(originals[key], variants[key], reference)
            common = {"strategy": strategy, "network_id": key, "shock_fraction": fraction}
            cases.append({**common, "selection_seed": int(reference.get("shock_seed", reference.get("tie_seed"))),
                          **result, "original_total_failures": baseline["total_failures"],
                          "original_additional_failures": baseline["additional_failures"],
                          "original_propagation_rounds": baseline["propagation_rounds"],
                          "original_failed_firms": baseline["failed_firms"],
                          "difference_total_failures": result["total_failures"] - baseline["total_failures"]})
            grouped[strategy, key, fraction, "original"].append(baseline)
            grouped[strategy, key, fraction, "concentrated"].append(result)
            for number, firms in enumerate(rounds):
                writer.writerows({**common, "repetition": result["repetition"], "round": number, "firm": firm} for firm in firms)
                round_count += len(firms)
    per_network = []
    for (strategy, key, fraction, version), rows in sorted(grouped.items()):
        summary = summarize_shocks(rows, fraction, shock_seed=0)
        del summary["shock_seed"]
        per_network.append({"strategy": strategy, "version": version, "network_id": key,
                            **summary, "mean_propagation_rounds": mean(r["propagation_rounds"] for r in rows)})
    summaries = []
    for strategy, _ in sources:
        for version in ("original", "concentrated"):
            rows = [r for r in per_network if r["strategy"] == strategy and r["version"] == version]
            for summary in summarize_networks(rows):
                group = [r for r in rows if r["shock_fraction"] == summary["shock_fraction"]]
                summaries.append({"strategy": strategy, "version": version, **summary,
                                  "mean_propagation_rounds": mean(r["mean_propagation_rounds"] for r in group)})
    comparison = []
    for strategy, _ in sources:
        for fraction in (.01, .05, .10, .20):
            pair = {r["version"]: r for r in summaries if r["strategy"] == strategy and r["shock_fraction"] == fraction}
            base, variant = pair["original"], pair["concentrated"]
            group = [r for r in cases if r["strategy"] == strategy and r["shock_fraction"] == fraction]
            comparison.append({"strategy": strategy, "shock_fraction": fraction,
                               "initial_failures": base["initial_failures"],
                               "original_mean_total_failures": base["mean_total_failures"],
                               "concentrated_mean_total_failures": variant["mean_total_failures"],
                               "original_mean_additional_failures": base["mean_additional_failures"],
                               "concentrated_mean_additional_failures": variant["mean_additional_failures"],
                               "difference_mean_total_failures": variant["mean_total_failures"] - base["mean_total_failures"],
                               "original_mean_functional_firms_pct": base["mean_functional_firms_pct"],
                               "concentrated_mean_functional_firms_pct": variant["mean_functional_firms_pct"],
                               "original_mean_amplification": base["mean_amplification"],
                               "concentrated_mean_amplification": variant["mean_amplification"],
                               "original_mean_propagation_rounds": base["mean_propagation_rounds"],
                               "concentrated_mean_propagation_rounds": variant["mean_propagation_rounds"],
                               "cases_with_more_failures": sum(r["difference_total_failures"] > 0 for r in group),
                               "cases_with_fewer_failures": sum(r["difference_total_failures"] < 0 for r in group),
                               "cases_with_equal_failures": sum(r["difference_total_failures"] == 0 for r in group)})
    for name, rows in (("shocks", cases), ("per_network", per_network), ("summary", summaries), ("comparison", comparison)):
        write_csv(output / f"{prefix}{name}.csv", rows)
    metadata = {
        "stage": "paired_saved_shocks_on_saved_concentrated_networks",
        "n": 1000, "networks": 20, "pool_size": 100,
        "new_executions": len(cases), "baseline_replays_for_validation": len(cases),
        "failure_round_records": round_count,
        "network_references": ["networks1000_nodes.csv", "networks1000_edges.csv", "concentration1000_edges.csv", "concentration1000_pools.csv"],
        "shock_references": [filename for _, filename in sources],
        "pairing": "same_network_initial_firms_and_repetition_within_strategy; not_paired_between_strategies",
        "targeting": "fixed_original_out_degree_selections; no_reranking_on_variant",
        "randomness": "no_new_draws; saved_concentration_seeds_9000_to_9019",
        "aggregation": "mean_within_100_shocks_then_equal_weight_across_20_networks",
        "difference": "concentrated_minus_original_total_failures",
        "depth": "rounds_after_initial_shock; logical_steps_not_time",
        "limits": "one_concentrated_variant_per_reference; identities_and_paths_change; no_HHI_only_causal_effect; no_costs",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"{prefix}metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in comparison:
        print(f"{row['strategy']} {100 * row['shock_fraction']:.0f}%: "
              f"F original={row['original_mean_total_failures']:.4f}; "
              f"concentrated F={row['concentrated_mean_total_failures']:.4f}; "
              f"difference={row['difference_mean_total_failures']:+.4f}")
    print(f"New executions: {len(cases)}; failure records: {round_count}")
    print(f"Local time: {perf_counter() - started:.3f} s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint", action="store_true", help='Apply saved original selections to concentrated variants')
    args = parser.parse_args()
    if args.joint:
        run_joint_comparison()
    else:
        run_construction()
