'Deterministic cascade with complete substitution and synchronous rounds.'


def run_cascade(graph, initial_failures):
    'Return new failures by round, starting with the shock in round 0.\n\n    The initially active benchmark uses comparable firm identifiers\n    (A-H in the example). The graph is not modified. Sources are exempt\n    from supply failure but may be withdrawn directly. An empty shock\n    returns [[]]. There is no recovery and no new links.\n    '
    suppliers = {
        firm: set(graph.predecessors(firm))
        for firm in graph.nodes
    }
    failed = set(initial_failures)
    if not failed.issubset(suppliers):
        raise ValueError('The shock contains firms that do not exist in the network.')
    rounds = [sorted(failed)]

    while True:
        new_failures = set()
        for firm, original_suppliers in suppliers.items():
            if firm in failed:
                continue
            if original_suppliers and original_suppliers.issubset(failed):
                new_failures.add(firm)

        if not new_failures:
            break
        failed.update(new_failures)
        rounds.append(sorted(new_failures))

    return rounds


if __name__ == "__main__":
    from network import build_example_network

    graph = build_example_network()
    rounds = run_cascade(graph, {"C"})
    for number, firms in enumerate(rounds):
        print(f"Round {number}: {', '.join(firms) or 'ninguna'}")
    failed = {firm for firms in rounds for firm in firms}
    print(f"Survivors: {', '.join(sorted(set(graph.nodes) - failed))}")
