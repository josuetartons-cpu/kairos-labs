'Individual-withdrawal census on the twenty approved networks.'

import csv
import json
from pathlib import Path
from statistics import mean

from network import build_layered_network
from cascades import run_cascade
from experiments import cascade_record, write_csv


def evaluate_firms(graph):
    'Each case starts from the original network; shocks do not accumulate.'
    records = []
    round_records = []
    for case, firm in enumerate(sorted(graph.nodes), start=1):
        rounds = run_cascade(graph, {firm})
        metrics = cascade_record(graph, {firm}, rounds, case)
        del metrics["repetition"]  # Exhaustive enumeration, not random repetitions.
        del metrics["initial_firms"]
        records.append({
            "firm": firm, "layer": graph.nodes[firm].get("layer", ""),
            "size": graph.nodes[firm]["size"],
            "in_degree": graph.in_degree(firm), "out_degree": graph.out_degree(firm),
            **metrics,
        })
        for number, failed in enumerate(rounds):
            for failed_firm in failed:
                round_records.append({"shocked_firm": firm, "round": number, "firm": failed_firm})
    return records, round_records


def summarize_cases(rows):
    return {
        "cases": len(rows),
        "mean_total_failures": mean(r["total_failures"] for r in rows),
        "mean_additional_failures": mean(r["additional_failures"] for r in rows),
        "max_total_failures": max(r["total_failures"] for r in rows),
        "cascade_frequency_pct": 100 * sum(r["additional_failures"] > 0 for r in rows) / len(rows),
    }


def run_individual_census():
    output = Path(__file__).resolve().parents[1] / "results"
    all_cases, all_rounds, per_network = [], [], []
    for index in range(20):
        network_id = f"N{index + 1:02d}"
        graph = build_layered_network(1000, 1000 + index, 2000 + index)
        cases, rounds = evaluate_firms(graph)
        all_cases.extend({"network_id": network_id, **r} for r in cases)
        all_rounds.extend({"network_id": network_id, **r} for r in rounds)
        per_network.append({"network_id": network_id, **summarize_cases(cases)})
    groups = []
    for field in ("size", "out_degree"):
        for value in sorted({r[field] for r in all_cases}):
            subset = [r for r in all_cases if r[field] == value]
            groups.append({"group_by": field, "value": value, **summarize_cases(subset)})
    summary = summarize_cases(all_cases)
    write_csv(output / "individual1000_cases.csv", all_cases)
    write_csv(output / "individual1000_rounds.csv", all_rounds)
    write_csv(output / "individual1000_per_network.csv", per_network)
    write_csv(output / "individual1000_groups.csv", groups)
    write_csv(output / "individual1000_summary.csv", [summary])
    metadata = {
        "stage": "exhaustive_single_firm_withdrawal", "n": 1000, "networks": 20,
        "cases": len(all_cases), "failure_round_records": len(all_rounds),
        "topology_seed_rule": "1000 + network_index", "size_seed_rule": "2000 + network_index",
        "network_index": "0..19", "initial_failures_per_case": 1,
        "sampling": "all_firms_once_per_network; no_shock_rng; deterministic_cascades",
        "overall_weighting": "equal_case_weights; equal_network_weights_because_1000_cases_each",
        "group_weighting": "pooled_firms_in_each_group; network_group_counts_can_differ",
        "size": "independent_synthetic_label_1_2_4; unused_by_cascade_rule",
        "comparison_warning": "previous_1_percent_shocks_removed_10_firms_not_1",
        "network_reference": "networks1000_nodes.csv; networks1000_edges.csv",
        "cascade_rule": "unchanged_complete_substitution",
    }
    (output / "individual1000_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary)
    for group in groups:
        print(group)
    worst = max(all_cases, key=lambda r: r["total_failures"])
    print('First maximum in network/firm order:', worst)


if __name__ == "__main__":
    run_individual_census()
