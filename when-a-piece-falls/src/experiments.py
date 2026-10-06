'Pilot: repeated random shocks on a single fixed network.'

import csv
import json
from pathlib import Path
import random
from statistics import mean, median
import sys
from time import perf_counter

import networkx as nx

from network import build_layered_network
from cascades import run_cascade


def select_random_shock(graph, count, rng):
    'Uniform sampling without replacement within a shock.'
    if not isinstance(count, int) or not 1 <= count <= len(graph):
        raise ValueError('count must be an integer between 1 and the number of firms.')
    return set(rng.sample(sorted(graph.nodes), count))


def cascade_record(graph, initial, rounds, repetition):
    'The same metrics for random and targeted shocks.'
    failed = {firm for new_failures in rounds for firm in new_failures}
    return {
        "repetition": repetition,
        "initial_firms": "|".join(sorted(initial)),
        "initial_failures": len(initial),
        "additional_failures": len(failed) - len(initial),
        "total_failures": len(failed),
        "functional_firms_pct": 100 * (len(graph) - len(failed)) / len(graph),
        "amplification": len(failed) / len(initial),
        "propagation_rounds": len(rounds) - 1,
        "failed_firms": "|".join(sorted(failed)),
    }


def run_repeated_shocks(graph, count=1, repetitions=100, shock_seed=44):
    'Reset failures for each repetition; keep the original network fixed.'
    if not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError('repetitions must be a positive integer.')
    rng = random.Random(shock_seed)
    results = []
    round_records = []

    for repetition in range(1, repetitions + 1):
        initial = select_random_shock(graph, count, rng)
        rounds = run_cascade(graph, initial)
        results.append(cascade_record(graph, initial, rounds, repetition))
        for round_number, new_failures in enumerate(rounds):
            for firm in new_failures:
                round_records.append({
                    "repetition": repetition,
                    "round": round_number,
                    "firm": firm,
                })

    return results, round_records


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_pilot():
    graph = build_layered_network(n=100, topology_seed=42, size_seed=43)
    started = perf_counter()
    results, rounds = run_repeated_shocks(graph, count=1, repetitions=100, shock_seed=44)
    elapsed = perf_counter() - started
    output = Path(__file__).resolve().parents[1] / "results"
    output.mkdir(exist_ok=True)
    write_csv(output / "pilot_random_shocks.csv", results)
    write_csv(output / "pilot_random_rounds.csv", rounds)
    write_csv(output / "pilot_nodes.csv", [
        {"firm": firm, **attrs} for firm, attrs in sorted(graph.nodes(data=True))
    ])
    write_csv(output / "pilot_edges.csv", [
        {"supplier": supplier, "customer": customer}
        for supplier, customer in sorted(graph.edges)
    ])
    metadata = {
        "stage": "pilot_single_fixed_network",
        "n": len(graph),
        "layers": 5,
        "topology_seed": 42,
        "size_seed": 43,
        "shock_seed": 44,
        "initial_failures_per_shock": 1,
        "shock_fraction": 0.01,
        "repetitions": 100,
        "sampling": "uniform_without_replacement_within_shock; fresh_draw_between_shocks",
        "cascade_rule": "all_original_suppliers_failed; sources_exempt_from_supply_failure",
        "python": sys.version.split()[0],
        "networkx": nx.__version__,
    }
    (output / "pilot_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    first = results[0]
    firm = first["initial_firms"]
    print(f"First shock: {firm}, layer={graph.nodes[firm]['layer']}, size={graph.nodes[firm]['size']}")
    print(f"First result: {first}")
    print(f"First shock history: {[r for r in rounds if r['repetition'] == 1]}")
    totals = [row["total_failures"] for row in results]
    print(f"Repetitions: {len(results)}; distinct initial firms: {len({r['initial_firms'] for r in results})}")
    print(f"Without additional failures: {sum(r['additional_failures'] == 0 for r in results)}")
    print(f"Total failures: mean={mean(totals):.4f}, median={median(totals)}, minimum={min(totals)}, maximum={max(totals)}")
    print(f"Mean survival: {mean(r['functional_firms_pct'] for r in results):.4f}%")
    print(f"Time for 100 cascade executions and in-memory records: {elapsed:.6f} s")
    print(f"Results: {output}")


def summarize_shocks(results, shock_fraction, shock_seed):
    'Descriptive summary; does not estimate uncertainty across networks.'
    totals = [float(row["total_failures"]) for row in results]
    additional = [float(row["additional_failures"]) for row in results]
    return {
        "shock_fraction": shock_fraction,
        "shock_seed": shock_seed,
        "repetitions": len(results),
        "initial_failures": int(results[0]["initial_failures"]),
        "mean_additional_failures": mean(additional),
        "mean_total_failures": mean(totals),
        "median_total_failures": median(totals),
        "min_total_failures": min(totals),
        "max_total_failures": max(totals),
        "mean_functional_firms_pct": mean(float(r["functional_firms_pct"]) for r in results),
        "mean_amplification": mean(float(r["amplification"]) for r in results),
        "shocks_with_cascade": sum(value > 0 for value in additional),
    }


def run_severity_comparison():
    'Three new batches (5, 10 and 20 percent), preserving the previous 1 percent batch.'
    graph = build_layered_network(n=100, topology_seed=42, size_seed=43)
    output = Path(__file__).resolve().parents[1] / "results"
    metadata = json.loads((output / "pilot_metadata.json").read_text(encoding="utf-8"))
    expected = {
        "n": 100, "topology_seed": 42, "size_seed": 43,
        "shock_seed": 44, "initial_failures_per_shock": 1, "repetitions": 100,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError('The reference batch does not match the agreed pilot.')
    with (output / "pilot_random_shocks.csv").open(newline="", encoding="utf-8") as stream:
        reference = list(csv.DictReader(stream))
    if len(reference) != 100 or any(int(row["initial_failures"]) != 1 for row in reference):
        raise ValueError('The reference CSV must contain 100 single-firm shocks.')

    scenarios = ((5, 45), (10, 46), (20, 47))
    combined_results = []
    combined_rounds = []
    summaries = [summarize_shocks(reference, 0.01, 44)]
    started = perf_counter()
    for count, seed in scenarios:
        results, rounds = run_repeated_shocks(
            graph, count=count, repetitions=100, shock_seed=seed
        )
        fraction = count / len(graph)
        combined_results.extend({"shock_fraction": fraction, "shock_seed": seed, **r} for r in results)
        combined_rounds.extend({"shock_fraction": fraction, "shock_seed": seed, **r} for r in rounds)
        summaries.append(summarize_shocks(results, fraction, seed))
    elapsed = perf_counter() - started

    write_csv(output / "pilot_severity_shocks.csv", combined_results)
    write_csv(output / "pilot_severity_rounds.csv", combined_rounds)
    write_csv(output / "pilot_severity_summary.csv", summaries)
    comparison_metadata = {
        "stage": "pilot_severity_comparison_single_fixed_network",
        "n": 100, "topology_seed": 42, "size_seed": 43,
        "new_scenarios": [{"initial_failures": count, "shock_seed": seed, "repetitions": 100} for count, seed in scenarios],
        "reference": "pilot_random_shocks.csv; 1%; seed=44; 100 repetitions",
        "new_executions": 300,
        "sampling": "uniform_without_replacement_within_shock; fresh_draw_between_shocks",
        "comparison": "separate_seed_per_severity; not_paired_or_nested",
        "cascade_rule": "all_original_suppliers_failed; sources_exempt_from_supply_failure",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / "pilot_severity_metadata.json").write_text(
        json.dumps(comparison_metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for summary in summaries:
        print(summary)
    print(f"Time for 300 executions and in-memory summaries: {elapsed:.6f} s")
    print('The previous 1 percent batch was read as reference and not overwritten.')


def summarize_networks(per_network):
    'Weight networks equally and report the range of network means.'
    summaries = []
    for fraction in sorted({r["shock_fraction"] for r in per_network}):
        group = [r for r in per_network if r["shock_fraction"] == fraction]
        network_means = [r["mean_total_failures"] for r in group]
        summaries.append({
            "shock_fraction": fraction,
            "networks": len(group),
            "initial_failures": group[0]["initial_failures"],
            "mean_additional_failures": mean(r["mean_additional_failures"] for r in group),
            "mean_total_failures": mean(network_means),
            "min_network_mean_total_failures": min(network_means),
            "max_network_mean_total_failures": max(network_means),
            "mean_functional_firms_pct": mean(r["mean_functional_firms_pct"] for r in group),
            "mean_amplification": mean(r["mean_amplification"] for r in group),
            "mean_cascade_frequency_pct": mean(100 * r["shocks_with_cascade"] / r["repetitions"] for r in group),
            "min_single_shock_total_failures": min(r["min_total_failures"] for r in group),
            "max_single_shock_total_failures": max(r["max_total_failures"] for r in group),
        })
    return summaries


def simulate_network_batch(n=100, network_count=20, repetitions=100):
    'Vary networks from the same generator while preserving rules and severities.'
    if not isinstance(n, int) or n < 100 or n % 100 != 0:
        raise ValueError('n must be a multiple of 100 to use exact percentages.')
    if not isinstance(network_count, int) or network_count < 1:
        raise ValueError('network_count must be a positive integer.')
    batch = {key: [] for key in ("shocks", "rounds", "per_network", "nodes", "edges", "manifest")}
    percentages = (1, 5, 10, 20)

    for network_index in range(network_count):
        network_id = f"N{network_index + 1:02d}"
        topology_seed = 1000 + network_index
        size_seed = 2000 + network_index
        graph = build_layered_network(n, topology_seed, size_seed)
        batch["manifest"].append({
            "network_id": network_id, "n": n,
            "edges": graph.number_of_edges(),
            "topology_seed": topology_seed, "size_seed": size_seed,
        })
        batch["nodes"].extend({"network_id": network_id, "firm": firm, **attrs} for firm, attrs in sorted(graph.nodes(data=True)))
        batch["edges"].extend({"network_id": network_id, "supplier": a, "customer": b} for a, b in sorted(graph.edges))

        for scenario_index, percentage in enumerate(percentages):
            count = n * percentage // 100
            shock_seed = 3000 + 4 * network_index + scenario_index
            results, rounds = run_repeated_shocks(graph, count, repetitions, shock_seed)
            scenario = {"network_id": network_id, "shock_fraction": percentage / 100, "shock_seed": shock_seed}
            batch["shocks"].extend({**scenario, **row} for row in results)
            batch["rounds"].extend({**scenario, **row} for row in rounds)
            batch["per_network"].append({
                "network_id": network_id,
                **summarize_shocks(results, percentage / 100, shock_seed),
            })

    batch["summary"] = summarize_networks(batch["per_network"])
    return batch


def run_network_batch(n=100):
    'Run twenty networks of the requested size without changing the rules.'
    started = perf_counter()
    batch = simulate_network_batch(n=n, network_count=20, repetitions=100)
    elapsed = perf_counter() - started
    output = Path(__file__).resolve().parents[1] / "results"
    output.mkdir(exist_ok=True)
    for key in ("shocks", "rounds", "per_network", "nodes", "edges", "manifest", "summary"):
        write_csv(output / f"networks{n}_{key}.csv", batch[key])
    metadata = {
        "stage": "multiple_networks_same_layered_generator",
        "n": n, "network_count": 20, "repetitions_per_network_per_severity": 100,
        "shock_percentages": [1, 5, 10, 20], "executions": 8000,
        "topology_seed_rule": "1000 + network_index", "size_seed_rule": "2000 + network_index",
        "shock_seed_rule": "3000 + 4 * network_index + scenario_index",
        "indices": "network_index=0..19; scenario_index=0..3 in [1,5,10,20] order",
        "aggregation": "mean within each network, then equal-weight mean across networks",
        "ranges": "network_mean_range is not a confidence interval",
        "generator": "five_equal_layers; previous_layer_suppliers; counts_uniform_1_2_3",
        "cascade_rule": "all_original_suppliers_failed; sources_exempt_from_supply_failure",
        "sampling": "uniform_without_replacement_within_shock; fresh_draw_between_shocks",
        "comparison": "separate_seed_per_network_and_severity; not_paired_or_nested",
        "python": sys.version.split()[0], "networkx": nx.__version__,
    }
    (output / f"networks{n}_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for row in batch["summary"]:
        print(row)
    print(f"Networks: {len(batch['manifest'])}; executions: {len(batch['shocks'])}; failure records: {len(batch['rounds'])}")
    print(f"Generation, simulation and in-memory summary time: {elapsed:.6f} s")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--severity", action="store_true", help='Compare 5, 10 and 20 percent shocks in the pilot')
    modes.add_argument("--networks", action="store_true", help='Compare twenty networks of the specified size')
    parser.add_argument("--n", type=int, choices=(100, 1000), default=100, help='Firms per network; used with --networks')
    args = parser.parse_args()
    if args.n != 100 and not args.networks:
        parser.error('--n 1000 requires --networks')
    if args.networks:
        run_network_batch(n=args.n)
    elif args.severity:
        run_severity_comparison()
    else:
        run_pilot()
