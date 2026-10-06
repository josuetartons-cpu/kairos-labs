'Manual example and layered pilot network generator. No shocks.'

import random
from collections import Counter

import networkx as nx


def build_example_network():
    'A supplier -> customer arrow represents substitutable supply.'
    graph = nx.DiGraph()
    graph.add_nodes_from("ABCDEFGH", active=True)
    graph.add_edges_from([
        ("A", "C"),
        ("B", "C"),
        ("C", "D"),
        ("C", "E"),
        ("D", "F"),
        ("E", "F"),
        ("F", "G"),
        ("B", "H"),
        ("H", "G"),
    ])
    return graph


def describe_network(graph):
    'Display suppliers, customers and original degrees; do not simulate failures.'
    print(f"Firms: {graph.number_of_nodes()}")
    print(f"Links: {graph.number_of_edges()}")
    for firm in sorted(graph.nodes):
        suppliers = sorted(graph.predecessors(firm))
        customers = sorted(graph.successors(firm))
        print(
            f"{firm}: suppliers={suppliers}, customers={customers}, "
            f"in_degree={graph.in_degree(firm)}, out_degree={graph.out_degree(firm)}"
        )


def build_layered_network(n=100, topology_seed=42, size_seed=43):
    'Five equal layers; one, two or three suppliers from the previous layer.\n\n    Sizes 1, 2 and 4 are illustrative indices, not capacity or production.\n    Separate seeds control topology and size. No shocks.\n    '
    if not isinstance(n, int) or n < 15 or n % 5 != 0:
        raise ValueError('n must be an integer, a multiple of 5, and at least 15.')

    topology_rng = random.Random(topology_seed)
    size_rng = random.Random(size_seed)
    graph = nx.DiGraph()
    layers = []
    firms_per_layer = n // 5

    for layer in range(5):
        firms = []
        for index in range(layer * firms_per_layer, (layer + 1) * firms_per_layer):
            firm = f"E{index:03d}"
            graph.add_node(
                firm, layer=layer, size=size_rng.choice((1, 2, 4)), active=True
            )
            firms.append(firm)
        layers.append(firms)

    for layer in range(1, 5):
        for customer in layers[layer]:
            count = topology_rng.choice((1, 2, 3))
            suppliers = topology_rng.sample(layers[layer - 1], count)
            for supplier in suppliers:
                graph.add_edge(supplier, customer)

    graph.graph.update(
        n=n, layers=5, topology_seed=topology_seed, size_seed=size_seed
    )
    return graph


def describe_pilot(graph):
    'Compact diagnostics of the generated benchmark; do not apply shocks.'
    non_sources = [firm for firm in graph if graph.in_degree(firm) > 0]
    print(f"Firms: {graph.number_of_nodes()}")
    print(f"Links: {graph.number_of_edges()}")
    print(f"Firms per layer: {dict(sorted(Counter(nx.get_node_attributes(graph, 'layer').values()).items()))}")
    print(f"Sources: {graph.number_of_nodes() - len(non_sources)}")
    print(f"Suppliers of non-source firms: {dict(sorted(Counter(graph.in_degree(firm) for firm in non_sources).items()))}")
    print(f"Synthetic sizes: {dict(sorted(Counter(nx.get_node_attributes(graph, 'size').values()).items()))}")
    print(f"Seeds: topology={graph.graph['topology_seed']}, size={graph.graph['size_seed']}")
    print(f"Acyclic: {nx.is_directed_acyclic_graph(graph)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true", help='Generate the approved 100-firm pilot')
    args = parser.parse_args()
    if args.pilot:
        describe_pilot(build_layered_network())
    else:
        describe_network(build_example_network())
