'Exact directed betweenness and saved individual damage; no cascades.'

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

import networkx as nx

from concentration import read_original_networks
from network import build_example_network
from redundancy import read_rows


def directed_betweenness(graph):
    'Count directed shortest paths without weights, endpoints or sampling.'
    if not graph.is_directed() or graph.is_multigraph():
        raise ValueError('A simple directed graph is required.')
    raw = nx.betweenness_centrality(graph, k=None, normalized=False,
                                  weight=None, endpoints=False)
    denominator = (len(graph) - 1) * (len(graph) - 2)
    return {firm: {"betweenness_raw": raw[firm],
                   "betweenness_normalized": raw[firm] / denominator if len(graph) > 2 else 0.0}
            for firm in sorted(graph)}


def join_saved_damage(graph, saved, centrality):
    'Join the existing census and check identities, attributes and counts.'
    records, seen = [], set()
    for row in saved:
        firm = row["firm"]
        if firm not in graph or firm in seen:
            raise ValueError('Unknown or duplicate firm in the census.')
        seen.add(firm)
        if (int(row["in_degree"]) != graph.in_degree(firm)
                or int(row["out_degree"]) != graph.out_degree(firm)
                or int(row["size"]) != graph.nodes[firm]["size"]
                or int(row["layer"]) != graph.nodes[firm]["layer"]):
            raise ValueError('The census does not match the network attributes.')
        failed_list = row["failed_firms"].split("|")
        failed = set(failed_list)
        total, additional = int(row["total_failures"]), int(row["additional_failures"])
        if (int(row["initial_failures"]) != 1 or total != 1 + additional
                or firm not in failed or not failed.issubset(graph)
                or len(failed) != len(failed_list) or len(failed) != total):
            raise ValueError('Inconsistent saved failures.')
        records.append({"firm": firm, "layer": graph.nodes[firm]["layer"],
                        "size": graph.nodes[firm]["size"],
                        "in_degree": graph.in_degree(firm), "out_degree": graph.out_degree(firm),
                        **centrality[firm], "additional_failures": additional,
                        "total_failures": total,
                        "propagation_rounds": int(row["propagation_rounds"])})
    if seen != set(graph):
        raise ValueError('The census does not include all firms.')
    return sorted(records, key=lambda row: row["firm"])


def summarize(rows):
    return {"firms": len(rows),
            "zero_betweenness_firms": sum(r["betweenness_raw"] == 0 for r in rows),
            "cascade_cases": sum(r["additional_failures"] > 0 for r in rows),
            "mean_betweenness_raw": mean(r["betweenness_raw"] for r in rows),
            "mean_total_failures": mean(r["total_failures"] for r in rows),
            "max_total_failures": max(r["total_failures"] for r in rows)}


def write_new_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark():
    output = Path(__file__).resolve().parents[1] / "results"
    names = ["betweenness_example.csv", "betweenness1000_firms.csv",
             "betweenness1000_per_network.csv", "betweenness1000_groups.csv",
             "betweenness1000_metadata.json"]
    if any((output / name).exists() for name in names):
        raise FileExistsError('Betweenness results already exist; they will not be overwritten.')
    started = perf_counter()
    example = build_example_network()
    example_rows = [{"firm": firm, "in_degree": example.in_degree(firm),
                     "out_degree": example.out_degree(firm), **values}
                    for firm, values in directed_betweenness(example).items()]
    graphs = read_original_networks(output)
    saved = read_rows(output / "individual1000_cases.csv")
    if {r["network_id"] for r in saved} != set(graphs):
        raise ValueError('The census must cover the twenty original networks.')
    firms, per_network = [], []
    for network_id, graph in sorted(graphs.items()):
        rows = join_saved_damage(graph, [r for r in saved if r["network_id"] == network_id],
                                 directed_betweenness(graph))
        firms.extend({"network_id": network_id, **row} for row in rows)
        per_network.append({"network_id": network_id, **summarize(rows)})
    groups = []
    for field in ("layer", "betweenness_status"):
        values = range(5) if field == "layer" else ("zero", "positive")
        for value in values:
            rows = [r for r in firms if (r[field] == value if field == "layer"
                    else (r["betweenness_raw"] == 0) == (value == "zero"))]
            if rows:
                groups.append({"group_by": field, "value": value, **summarize(rows)})
    for name, rows in zip(names[:4], (example_rows, firms, per_network, groups)):
        write_new_csv(output / name, rows)
    inputs = ["networks1000_nodes.csv", "networks1000_edges.csv",
              "networks1000_manifest.csv", "individual1000_cases.csv"]
    metadata = {
        "stage": "exact_directed_betweenness_original_benchmarks", "networks": 20,
        "firms": len(firms), "example_firms": 8, "new_cascades": 0,
        "method": "NetworkX exact Brandes; directed; k=None; weight=None; endpoints=False",
        "raw": "sum_of_fractions_of_shortest_directed_paths_through_node_excluding_endpoints",
        "normalization": "raw / ((n-1)*(n-2)); zero_for_n_less_than_3",
        "unreachable_pairs": "contribute_zero; normalization_uses_all_possible_pairs",
        "groups": "pooled_firms_with_equal_weight; network_group_counts_can_differ",
        "per_network": "full_1000_firm_census_each; networks_not_independent_shocks",
        "limits": "not_supply_flow_or_cascade_impact; sources_and_sinks_have_zero; size_unused",
        "scope": "original_benchmarks_only; no_new_attacks_or_variants",
        "input_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in inputs},
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    with (output / names[4]).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print("Ejemplo:", example_rows)
    print("Grupos:", groups)
    print('First damage maximum:', max(firms, key=lambda r: r["total_failures"]))
    print('First betweenness maximum:', max(firms, key=lambda r: r["betweenness_raw"]))
    print(f"Time: {perf_counter() - started:.3f} s; no new cascades.")


if __name__ == "__main__":
    run_benchmark()
