'Compare out-degree-targeted shocks with the existing random batches.'

import csv
import json
from pathlib import Path
import random
from time import perf_counter

from network import build_layered_network
from cascades import run_cascade
from experiments import cascade_record, summarize_shocks, summarize_networks, write_csv


def rank_by_out_degree(graph, tie_seed):
    'Pre-shock ranking; stable sorting preserves the shuffled order within ties.'
    firms = sorted(graph.nodes)
    random.Random(tie_seed).shuffle(firms)
    return sorted(firms, key=lambda firm: graph.out_degree(firm), reverse=True)


def read_random_reference(output):
    metadata = json.loads((output / "networks1000_metadata.json").read_text(encoding="utf-8"))
    if metadata["n"] != 1000 or metadata["network_count"] != 20 or metadata["repetitions_per_network_per_severity"] != 100:
        raise ValueError('The reference must be the approved batch of twenty 1,000-firm networks.')
    integer_fields = {"shock_seed", "repetitions", "initial_failures", "shocks_with_cascade"}
    with (output / "networks1000_per_network.csv").open(newline="", encoding="utf-8") as stream:
        rows = []
        for row in csv.DictReader(stream):
            rows.append({
                key: value if key == "network_id" else int(value) if key in integer_fields else float(value)
                for key, value in row.items()
            })
    expected = {(f"N{i + 1:02d}", fraction) for i in range(20) for fraction in (.01, .05, .10, .20)}
    actual = {(row["network_id"], row["shock_fraction"]) for row in rows}
    if len(rows) != 80 or actual != expected:
        raise ValueError('The reference must contain all eighty network/severity combinations.')
    return rows


def run_targeted_comparison():
    output = Path(__file__).resolve().parents[1] / "results"
    random_reference = read_random_reference(output)
    per_network = []
    executions = 0
    failure_records = 0
    started = perf_counter()
    shock_fields = ["network_id", "shock_fraction", "tie_seed", "repetition", "initial_firms", "initial_failures", "additional_failures", "total_failures", "functional_firms_pct", "amplification", "propagation_rounds", "failed_firms"]
    round_fields = ["network_id", "shock_fraction", "tie_seed", "repetition", "round", "firm"]

    # Stream each execution to avoid retaining millions of round records in memory.
    with (output / "targeted1000_shocks.csv").open("w", newline="", encoding="utf-8") as shocks_file, (output / "targeted1000_rounds.csv").open("w", newline="", encoding="utf-8") as rounds_file:
        shock_writer = csv.DictWriter(shocks_file, fieldnames=shock_fields)
        round_writer = csv.DictWriter(rounds_file, fieldnames=round_fields)
        shock_writer.writeheader()
        round_writer.writeheader()
        for network_index in range(20):
            network_id = f"N{network_index + 1:02d}"
            graph = build_layered_network(1000, 1000 + network_index, 2000 + network_index)
            grouped_results = {count: [] for count in (10, 50, 100, 200)}
            for repetition in range(1, 101):
                tie_seed = 4000 + 100 * network_index + repetition - 1
                ranking = rank_by_out_degree(graph, tie_seed)
                for count in (10, 50, 100, 200):
                    initial = set(ranking[:count])
                    rounds = run_cascade(graph, initial)
                    result = cascade_record(graph, initial, rounds, repetition)
                    grouped_results[count].append(result)
                    common = {"network_id": network_id, "shock_fraction": count / 1000, "tie_seed": tie_seed}
                    shock_writer.writerow({**common, **result})
                    executions += 1
                    for number, firms in enumerate(rounds):
                        for firm in firms:
                            round_writer.writerow({**common, "repetition": repetition, "round": number, "firm": firm})
                            failure_records += 1
            for count, results in grouped_results.items():
                summary = summarize_shocks(results, count / 1000, shock_seed=0)
                # This shock is not uniformly sampled; remove the inapplicable field.
                del summary["shock_seed"]
                per_network.append({"network_id": network_id, **summary})

    combined_per_network = [
        {"strategy": "random", **{k: v for k, v in r.items() if k != "shock_seed"}}
        for r in random_reference
    ] + [{"strategy": "targeted_out_degree", **r} for r in per_network]
    random_summary = summarize_networks(random_reference)
    targeted_summary = summarize_networks(per_network)
    summary_rows = [{"strategy": "random", **r} for r in random_summary] + [{"strategy": "targeted_out_degree", **r} for r in targeted_summary]
    comparison = []
    for random_row, targeted_row in zip(random_summary, targeted_summary):
        comparison.append({
            "shock_fraction": random_row["shock_fraction"],
            "initial_failures": random_row["initial_failures"],
            "random_mean_total_failures": random_row["mean_total_failures"],
            "targeted_mean_total_failures": targeted_row["mean_total_failures"],
            "difference_in_mean_total_failures": targeted_row["mean_total_failures"] - random_row["mean_total_failures"],
            "targeted_to_random_mean_total_ratio": targeted_row["mean_total_failures"] / random_row["mean_total_failures"],
            "random_mean_functional_firms_pct": random_row["mean_functional_firms_pct"],
            "targeted_mean_functional_firms_pct": targeted_row["mean_functional_firms_pct"],
            "random_mean_amplification": random_row["mean_amplification"],
            "targeted_mean_amplification": targeted_row["mean_amplification"],
        })
    write_csv(output / "targeted1000_per_network.csv", combined_per_network)
    write_csv(output / "targeted1000_summary.csv", summary_rows)
    write_csv(output / "targeted1000_comparison.csv", comparison)
    metadata = {
        "stage": "fixed_pre_shock_out_degree_targeting",
        "n": 1000, "networks": 20, "tie_rankings_per_network": 100,
        "initial_failures": [10, 50, 100, 200], "new_executions": executions,
        "failure_round_records": failure_records,
        "ranking": "original_out_degree_descending; shuffled_order_within_equal_degree",
        "tie_seed_rule": "4000 + 100 * network_index + repetition - 1",
        "tie_seed_range": [4000, 5999],
        "intensities": "nested_prefixes_of_same_ranking_within_targeted_repetition",
        "repetitions": "tie_break_uncertainty_only; cascade_deterministic; repeated_sets_possible",
        "random_reference": "networks1000_per_network.csv; same_networks_and_initial_counts",
        "comparison": "paired_by_network; not_paired_by_individual_shock; economic_size_not_matched",
        "network_files": ["networks1000_nodes.csv", "networks1000_edges.csv", "networks1000_manifest.csv", "networks1000_metadata.json"],
        "cascade_rule": "unchanged_complete_substitution",
    }
    (output / "targeted1000_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in comparison:
        print(row)
    print(f"New executions: {executions}; failure records: {failure_records}")
    print(f"Total time including round-record writing: {perf_counter() - started:.3f} s")


if __name__ == "__main__":
    run_targeted_comparison()
