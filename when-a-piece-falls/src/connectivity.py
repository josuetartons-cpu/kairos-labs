'Weak connectivity of benchmarks and saved final states; no cascades.'

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

import networkx as nx

from concentration import read_original_networks, read_concentrated_networks
from redundancy import read_rows, read_saved_network_pairs


METRICS = ("active_firms", "weak_components", "largest_component",
           "largest_component_fraction_original", "fragmentation")
VERSIONS = ("original", "redundant", "pool100", "pool150")
STRATEGIES = ("random", "targeted_original_out_degree")
FRACTIONS = (.01, .05, .10, .20)


def connectivity_metrics(graph, failed_firms=()):
    'Measure the survivor-induced subgraph without modifying the reference.\n\n    Ignore direction only when grouping components. Fragmentation is the\n    fraction of distinct survivor pairs in different components. With fewer\n    than two survivors it is undefined (None, blank CSV cell). N always\n    denotes the nonempty original network size.\n    '
    if not graph.is_directed() or graph.is_multigraph() or not len(graph):
        raise ValueError('A nonempty simple directed original network is required.')
    failed = set(failed_firms)
    if not failed.issubset(graph):
        raise ValueError('The saved state contains unknown firms.')
    active = len(graph) - len(failed)
    sizes = sorted((len(component) for component in nx.weakly_connected_components(
        graph.subgraph(set(graph) - failed))), reverse=True)
    largest = sizes[0] if sizes else 0
    fragmentation = (1 - sum(n * (n - 1) for n in sizes) / (active * (active - 1))
                     if active >= 2 else None)
    return {"original_firms": len(graph), "active_firms": active,
            "weak_components": len(sizes), "largest_component": largest,
            "largest_component_fraction_original": largest / len(graph),
            "fragmentation": fragmentation,
            "component_sizes": "|".join(map(str, sizes))}


def summarize_states(states):
    'Average within each network, then weight networks equally without zero imputation.\n\n    For fragmentation, exclude undefined cases within networks and networks\n    without defined cases when aggregating. Report both denominators.\n    '
    grouped = defaultdict(list)
    seen = set()
    for row in states:
        key = (row["version"], row["strategy"], row["network_id"], row["shock_fraction"])
        case_key = (*key, row["repetition"])
        if case_key in seen:
            raise ValueError('Duplicate final state.')
        seen.add(case_key)
        grouped[key].append(row)
    per_network = []
    for (version, strategy, network, fraction), rows in sorted(grouped.items()):
        defined = [r["fragmentation"] for r in rows if r["fragmentation"] is not None]
        per_network.append({"version": version, "strategy": strategy,
                            "network_id": network, "shock_fraction": fraction,
                            "cases": len(rows), "fragmentation_defined_cases": len(defined),
                            **{f"mean_{key}": mean(r[key] for r in rows) for key in METRICS[:-1]},
                            "mean_fragmentation": mean(defined) if defined else None})
    groups = defaultdict(list)
    for row in per_network:
        groups[row["version"], row["strategy"], row["shock_fraction"]].append(row)
    summary = []
    for (version, strategy, fraction), rows in sorted(groups.items()):
        defined = [r["mean_fragmentation"] for r in rows if r["mean_fragmentation"] is not None]
        summary.append({"version": version, "strategy": strategy, "shock_fraction": fraction,
                        "networks": len(rows), "cases": sum(r["cases"] for r in rows),
                        "fragmentation_defined_cases": sum(r["fragmentation_defined_cases"] for r in rows),
                        "fragmentation_defined_networks": len(defined),
                        **{f"mean_{key}": mean(r[f"mean_{key}"] for r in rows) for key in METRICS[:-1]},
                        "mean_fragmentation": mean(defined) if defined else None})
    return per_network, summary


def read_pool150(output, originals):
    'Reconstruct the saved sensitivity variant without generating edges.'
    variants = {key: graph.copy() for key, graph in originals.items()}
    for graph in variants.values():
        graph.remove_edges_from(list(graph.edges))
    seen = set()
    for row in read_rows(output / "concentration1000_sensitivity_edges.csv"):
        key, a, b = row["network_id"], row["supplier"], row["customer"]
        graph = variants[key]
        if (key, a, b) in seen or a not in graph or b not in graph:
            raise ValueError('Duplicate pool150 edge or unknown firm.')
        seen.add((key, a, b))
        graph.add_edge(a, b)
    pools = defaultdict(set)
    for row in read_rows(output / "concentration1000_sensitivity_pools.csv"):
        key, layer, firm = row["network_id"], int(row["supplier_layer"]), row["firm"]
        if key not in originals or layer not in range(4) or firm in pools[key, layer]:
            raise ValueError('Invalid or duplicate pool150 pool.')
        pools[key, layer].add(firm)
    for key, graph in variants.items():
        original = originals[key]
        if dict(graph.in_degree()) != dict(original.in_degree()):
            raise ValueError('Pool150 changed supplier counts per customer.')
        for layer in range(4):
            eligible = pools[key, layer]
            if len(eligible) != 150 or any(f not in graph or graph.nodes[f]["layer"] != layer for f in eligible):
                raise ValueError('Pool150 must have 150 eligible suppliers per layer.')
        if any(graph.nodes[b]["layer"] != graph.nodes[a]["layer"] + 1
               or a not in pools[key, graph.nodes[a]["layer"]] for a, b in graph.edges):
            raise ValueError('Pool150 edge outside its layer or eligible pool.')
    return variants


def validate_saved_state(graph, row):
    'Check saved counts and selections without running the cascade rule.'
    failed_list = row["failed_firms"].split("|") if row["failed_firms"] else []
    initial_list = row["initial_firms"].split("|") if row["initial_firms"] else []
    failed, initial = set(failed_list), set(initial_list)
    if (len(failed) != len(failed_list) or len(initial) != len(initial_list)
            or not initial.issubset(failed) or not failed.issubset(graph)
            or len(failed) != int(row["total_failures"])
            or len(initial) != int(row["initial_failures"])
            or len(failed) - len(initial) != int(row["additional_failures"])
            or len(initial) != round(len(graph) * float(row["shock_fraction"]))):
        raise ValueError('Inconsistent saved selection or final state.')
    return failed


def run_connectivity():
    output = Path(__file__).resolve().parents[1] / "results"
    prefix = "connectivity1000_"
    names = ("benchmark.csv", "benchmark_summary.csv", "states.csv",
             "per_network.csv", "summary.csv", "metadata.json")
    if any((output / (prefix + name)).exists() for name in names):
        raise FileExistsError('Connectivity results already exist; they will not be overwritten.')
    started = perf_counter()
    originals = read_original_networks(output)
    _, redundant = read_saved_network_pairs(output)
    graphs = {"original": originals, "redundant": redundant,
              "pool100": read_concentrated_networks(output, originals),
              "pool150": read_pool150(output, originals)}
    benchmark = [{"version": version, "network_id": key, **connectivity_metrics(graph)}
                 for version in VERSIONS for key, graph in graphs[version].items()]
    benchmark_summary = [{"version": version, "networks": len(originals),
                          **{f"mean_{metric}": mean(r[metric] for r in benchmark if r["version"] == version)
                             for metric in METRICS}}
                         for version in VERSIONS]
    original_sources = (("random", "networks1000_shocks.csv"),
                        ("targeted_original_out_degree", "targeted1000_shocks.csv"))
    sources = {"original": original_sources,
               "redundant": ((None, "redundancy1000_joint_shocks.csv"),),
               "pool100": ((None, "concentration1000_joint_shocks.csv"),),
               "pool150": ((None, "concentration1000_sensitivity_shocks.csv"),)}
    expected = {(strategy, key, fraction, repetition) for strategy in STRATEGIES
                for key in originals for fraction in FRACTIONS for repetition in range(1, 101)}
    states, references = [], {}
    for version in VERSIONS:
        seen = set()
        for strategy_override, filename in sources[version]:
            for row in read_rows(output / filename):
                strategy = strategy_override or row["strategy"]
                key = strategy, row["network_id"], float(row["shock_fraction"]), int(row["repetition"])
                if key not in expected or key in seen:
                    raise ValueError('Unexpected or duplicate selection in final states.')
                seen.add(key)
                graph = graphs[version][key[1]]
                failed = validate_saved_state(graph, row)
                seed = int(row.get("selection_seed", row.get("shock_seed", row.get("tie_seed"))))
                selection = (frozenset(row["initial_firms"].split("|")), seed)
                if version == "original":
                    references[key] = selection
                elif selection != references[key]:
                    raise ValueError('The variant does not preserve the original selection.')
                states.append({"version": version, "strategy": strategy, "network_id": key[1],
                               "shock_fraction": key[2], "repetition": key[3], "selection_seed": seed,
                               "initial_failures": int(row["initial_failures"]), "total_failures": len(failed),
                               **connectivity_metrics(graph, failed)})
        if seen != expected:
            raise ValueError('This version is missing final states.')
        print(f"{version}: 20 benchmarks y {len(seen):,} final states measured.", flush=True)
    per_network, summary = summarize_states(states)
    for name, rows in (("benchmark", benchmark), ("benchmark_summary", benchmark_summary),
                       ("states", states), ("per_network", per_network), ("summary", summary)):
        with (output / f"{prefix}{name}.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    inputs = ["networks1000_nodes.csv", "networks1000_edges.csv", "networks1000_manifest.csv",
              "redundancy1000_edges.csv", "concentration1000_edges.csv", "concentration1000_pools.csv",
              "concentration1000_sensitivity_edges.csv", "concentration1000_sensitivity_pools.csv",
              *[name for items in sources.values() for _, name in items]]
    metadata = {
        "stage": "weak_connectivity_of_saved_benchmarks_and_final_states",
        "benchmarks": len(benchmark), "final_states": len(states), "new_cascades": 0,
        "versions": list(VERSIONS), "networks_per_version": 20, "n": 1000,
        "strategies": list(STRATEGIES), "shock_fractions": list(FRACTIONS),
        "survivors": "original_nodes_minus_saved_failed_firms; node_active_attribute_not_used",
        "connectivity": "weak; direction_ignored_only_for_components; isolates_count_as_one",
        "largest_component_fraction_original": "largest_component / original_n",
        "fragmentation": "1 - sum(n_j*(n_j-1)) / (A*(A-1)); fraction_of_disconnected_survivor_pairs",
        "undefined_fragmentation": "A<2: None, blank_csv_cell; no_zero_imputation",
        "empty_survivors": "A=0,K=0,L=0,L/N=0; fragmentation_undefined",
        "aggregation": "mean_within_network_then_equal_weight_across_networks; undefined_fragmentation_cases_excluded; networks_without_defined_cases_excluded_for_fragmentation_only; report_denominators",
        "component_sizes": "descending_sizes_separated_by_pipe; empty_for_zero_survivors",
        "selection": "saved_selections; original_out_degree_targeting_without_reranking; no_new_draws",
        "excluded": "individual_censuses_and_redundancy_R2_R3",
        "limits": "structural_description_not_production_or_supply_viability; no_costs_or_efficiency; no_real_economy_inference",
        "input_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in inputs},
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    with (output / f"{prefix}metadata.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(f"Completed: 80 benchmarks, 64,000 states; no new cascades. {perf_counter() - started:.3f} s")
    for row in benchmark_summary:
        print(f"{row['version']}: K={row['mean_weak_components']:.2f}; "
              f"L={row['mean_largest_component']:.2f}; fragmentation={row['mean_fragmentation']:.6f}")


if __name__ == "__main__":
    run_connectivity()
