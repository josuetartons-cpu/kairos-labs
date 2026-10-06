'Approved teaching figure: withdraw C from the manual eight-firm network.'

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from network import build_example_network
from cascades import run_cascade
from plot_results import style, BG, INK, DIM, LINE, WINE, BLUE, NAVY, GOLD


def main():
    style()
    root = Path(__file__).resolve().parents[1]
    output = root / "figures"
    output.mkdir(exist_ok=True)
    stem = output / "figure1_red_y_cascada"
    targets = [stem.with_suffix(ext) for ext in (".png", ".svg", ".pdf", ".json")]
    if any(path.exists() for path in targets):
        raise FileExistsError('Figure 1 already exists; preserve the reviewed version.')
    graph = build_example_network()
    rounds = run_cascade(graph, {"C"})
    assert rounds == [["C"], ["D", "E"], ["F"]]
    failed = {firm for group in rounds for firm in group}
    assert set(graph) - failed == set("ABGH")
    # Positions are fixed manually and do not represent economic distances.
    pos = {"A": (0, 1), "B": (0, -1), "C": (1, .5),
           "D": (2, 1), "E": (2, 0), "F": (3, .5),
           "G": (4, 0), "H": (2, -1)}
    colors = {"active": BLUE, "shock": "#811838", "cascade": WINE}
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2))
    fig.subplots_adjust(left=.035, right=.975, top=.77, bottom=.20, wspace=.18)
    fig.text(.035, .977, 'KAIROS / LABORATORY  ·  FIGURE 01', fontsize=9,
             fontfamily="DejaVu Sans Mono", color=WINE)
    fig.suptitle('When a Piece Falls', x=.035, y=.93, ha="left",
                 fontsize=23, fontweight="bold", color=INK)
    titles = ['1 · Initial network', '2 · Withdrawal of C', '3 · Final cascade']
    for index, ax in enumerate(axes):
        ax.set_title(titles[index], loc="left", fontsize=14, fontweight="bold", pad=22)
        shown_failed = set() if index == 0 else ({"C"} if index == 1 else failed)
        for edge in graph.edges:
            inactive = any(firm in shown_failed for firm in edge)
            alternate = index == 2 and edge == ("H", "G")
            nx.draw_networkx_edges(graph, pos, ax=ax, edgelist=[edge],
                node_size=1250, arrowsize=17, arrowstyle="-|>",
                edge_color=BLUE if alternate else (LINE if inactive else NAVY),
                width=2.8 if alternate else 1.4,
                style="dashed" if inactive else "solid", connectionstyle="arc3,rad=0")
        node_colors = [colors["shock"] if firm == "C" and index else
                       colors["cascade"] if firm in shown_failed else colors["active"]
                       for firm in graph]
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=1250,
                               node_color=node_colors, edgecolors="white", linewidths=2)
        nx.draw_networkx_labels(graph, pos, ax=ax, font_color="white",
                                font_size=13, font_weight="bold")
        if index:
            ax.text(1, .12, 'withdrawn · r0', ha="center", fontsize=9, color=colors["shock"])
        if index == 2:
            for firm, number in (("D", 1), ("E", 1), ("F", 2)):
                x, y = pos[firm]
                ax.text(x, y-.38, f"failed · r{number}", ha="center", fontsize=9,
                        color=colors["cascade"])
        ax.set_xlim(-.45, 4.5)
        ax.set_ylim(-1.55, 1.5)
        ax.axis("off")
    handles = [Line2D([], [], marker="o", linestyle="", color=color, markersize=10, label=label)
               for color, label in ((colors["active"], 'Operational'),
                                    (colors["shock"], 'Initial withdrawal'),
                                    (colors["cascade"], 'Failure after losing all suppliers'))]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(.03, .045),
               ncol=3, frameon=False, fontsize=10)
    for path in targets[:3]:
        fig.savefig(path, dpi=180, facecolor=BG)
    plt.close(fig)
    metadata = {"initial_failures": ["C"], "rounds": rounds,
                "survivors": sorted(set(graph)-failed), "total_failures": len(failed),
                "additional_failures": len(failed)-1,
                "edges": sorted(graph.edges), "positions": pos,
                "purpose": 'Teaching example selected to show propagation and survival through substitution.',
                "networkx": nx.__version__, "matplotlib": matplotlib.__version__,
                "palette_reference": "Kairos colors intensified at Josue's request",
                "captions_file": "figure_captions.md", "background": BG}
    targets[3].write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print('Figure 1: C (r0), D/E (r1), F (r2); survivors A/B/G/H.')


if __name__ == "__main__":
    main()
