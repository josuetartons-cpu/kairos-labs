'Kairos figures 2-C1 from saved CSV files: no simulations or new attacks.'

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BG, INK, DIM, LINE = "#F7F4EE", "#1C1B22", "#6B6570", "#E4DFD3"
WINE, BLUE, NAVY, GOLD, GRAY = "#C5234A", "#176AD5", "#17264A", "#E2AD46", "#716778"
COLORS = dict(original=NAVY, redundant=BLUE, pool150="#8652B8", pool100=WINE)
LABELS = dict(original='Original · 200 eligible', redundant='With alternative',
              pool150='150 eligible', pool100='100 eligible')
FRACTIONS = [.01, .05, .1, .2]
STRATEGIES = ["random", "targeted_original_out_degree"]
SOURCES = {}
RECORDS = []
CAPTIONS = {"01": {"title": 'When a Piece Falls',
    "subtitle": 'An active alternative can stop propagation',
    "filename": "figure1_red_y_cascada",
    "notes": ['Example with eight firms and nine links. Arrows: supplier to customer; dashed links touch inactive firms.',
              'C is withdrawn in round 0; D and E fail in round 1; F in round 2. A, B, G and H survive: G retains H as supplier. One initial withdrawal and three additional failures.',
              'A non-source firm fails after losing all its suppliers; one active supplier is sufficient, without capacity constraints.',
              'Teaching example: not representative of typical damage in the 1,000-firm networks.']}}


def style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": DIM,
        "ytick.color": DIM, "axes.facecolor": BG, "figure.facecolor": BG,
        "axes.edgecolor": LINE, "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.titlesize": 13,
        "svg.fonttype": "path", "pdf.fonttype": 42})


def read(name):
    path = ROOT / "results" / name
    SOURCES[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select(rows, **criteria):
    result = [r for r in rows if all(r[k] == str(v) for k, v in criteria.items())]
    if len(result) != 1:
        raise ValueError(f"Missing or duplicate reference: {criteria}")
    return result[0]


def values(rows, metric, **criteria):
    return np.array([float(select(rows, shock_fraction=f, **criteria)[metric]) for f in FRACTIONS])


def canvas(number, title, subtitle, count=1):
    fig, axes = plt.subplots(1, count, figsize=(14.5, 7), squeeze=False)
    fig.subplots_adjust(left=.075, right=.96, top=.77, bottom=.17,
                        wspace=.30 if count < 3 else .42)
    fig.add_artist(Rectangle((.035, .915), .018, .035, transform=fig.transFigure,
                            facecolor=WINE, edgecolor="none"))
    fig.text(.065, .928, f"KAIROS / LABORATORY  ·  FIGURE {number}",
             fontsize=10, fontfamily="DejaVu Sans Mono", color=WINE)
    fig.text(.035, .856, title, fontsize=23, fontweight="bold")
    CAPTIONS[number] = dict(title=title, subtitle=subtitle)
    fig._kairos_number = number
    return fig, list(axes[0])


def clean(ax, ylabel=None):
    ax.grid(axis="y", color=LINE, linewidth=.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=8)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=12)


def severity(ax):
    ax.set_xticks([1, 5, 10, 20], ["1 %", "5 %", "10 %", "20 %"])
    ax.set_xlim(0, 21)
    ax.set_xlabel('Initially withdrawn firms', labelpad=13)


def footer(fig, notes):
    'Keep explanations in web captions rather than drawing them inside the figure.'
    CAPTIONS[fig._kairos_number]["notes"] = notes


def export(fig, name, data):
    paths = [ROOT / "figures" / f"{name}.{ext}" for ext in ("png", "svg", "pdf")]
    if any(p.exists() for p in paths):
        raise FileExistsError(f"Refusing overwrite: {name}")
    for p in paths:
        fig.savefig(p, dpi=180, facecolor=BG)
    CAPTIONS[fig._kairos_number]["filename"] = name
    plt.close(fig)
    RECORDS.append({"figure": name, "plotted_data": data})


def figure2():
    rows = read("targeted1000_summary.csv")
    fig, (ax,) = canvas("02", 'Damage depends on which firms are withdrawn',
                       'Same initial severity; random selection or ranking by customer count in the original network.')
    data = []
    for strategy, color, marker, label in [("random", BLUE, "o", 'At random'),
            ("targeted_out_degree", WINE, "s", 'By number of customers')]:
        y = values(rows, "mean_total_failures", strategy=strategy)
        low = values(rows, "min_network_mean_total_failures", strategy=strategy)
        high = values(rows, "max_network_mean_total_failures", strategy=strategy)
        assert np.all(low <= y) and np.all(y <= high)
        ax.errorbar(np.array(FRACTIONS)*100, y, yerr=[y-low, high-y],
                    color=color, marker=marker, lw=2.5, capsize=5, label=label)
        ax.annotate(f"{y[-1]:.1f}", (20, y[-1]), xytext=(-12, 12),
                    textcoords="offset points", ha="right", color=color, fontweight="bold")
        data.append(dict(strategy=strategy, mean=y.tolist(), min=low.tolist(), max=high.tolist()))
    ax.plot(np.array(FRACTIONS)*100, np.array(FRACTIONS)*1000, "--", color=GRAY,
            linewidth=1.5, label='Initial withdrawals only')
    clean(ax, 'Mean total failures\n(including initial withdrawals)')
    severity(ax); ax.set_ylim(0, 580)
    ax.legend(loc="upper left", frameon=False)
    footer(fig, ['20 networks of 1,000 firms; 100 repetitions per network, strategy and severity.',
        'Bars: minimum and maximum of the 20 network means; these are not confidence intervals.',
        'Strategies withdraw different sets. Cascade rounds are deterministic; firms are synthetic.'])
    export(fig, "figure2_severidad_y_estrategia", data)


def figure3():
    rows = read("redundancy1000_joint_summary.csv")
    fig, axes = canvas("03", 'An alternative reduces propagation',
        'Add one distinct supplier per non-source firm while preserving exactly the same shocks.', 2)
    data=[]
    for ax, strategy, title in zip(axes, STRATEGIES, ['Random withdrawals', 'Withdrawals by original customer counts']):
        for version, marker in [("original", "s"), ("redundant", "o")]:
            y=values(rows, "mean_additional_failures", strategy=strategy, version=version)
            ax.plot(np.array(FRACTIONS)*100, y, marker=marker, lw=2.5,
                    color=COLORS[version], label="Original" if version=="original" else 'With alternative')
            ax.annotate(f"{y[-1]:.1f}", (20, y[-1]), xytext=(-8, 10), textcoords="offset points",
                        color=COLORS[version], ha="right", fontweight="bold")
            data.append(dict(strategy=strategy,version=version,mean_additional=y.tolist()))
        ax.set_title(title, loc="left", pad=18); clean(ax); severity(ax); ax.set_ylim(0, 340)
        ax.legend(loc="upper left", frameon=False)
    axes[0].set_ylabel('Mean additional failures\n(excluding initial withdrawals)', labelpad=12)
    footer(fig, ['20 networks x 100 repetitions per strategy and severity. Alternatives: assignment R1.',
        'The intervention adds 800 links per network. Costs, production and capacity are not estimated.',
        'Under this rule, adding suppliers cannot worsen a cascade; magnitudes depend on the network and shock.'])
    export(fig, "figure3_redundancia", data)


def figure4():
    rows=read("concentration1000_sensitivity_summary.csv")
    benchmark=read("concentration1000_sensitivity_benchmark.csv")
    fig, axes=canvas("04", 'Concentrating links has no uniform effect',
        'Same total links and suppliers per customer; supplier identities and paths change.', 3)
    versions=["original","pool150","pool100"]
    hhi=[mean(float(r["hhi"]) for r in benchmark if r["version"]==v) for v in versions]
    assert len(benchmark)==240 and hhi[0]<hhi[1]<hhi[2]
    axes[0].bar(range(3), hhi, color=[COLORS[v] for v in versions], width=.55)
    axes[0].set_xticks(range(3), ["200\n(original)","150","100"])
    axes[0].set_xlabel('Eligible suppliers per layer', labelpad=12)
    axes[0].set_title('Link concentration', loc="left", pad=18)
    axes[0].set_ylim(0,.0155); clean(axes[0], 'Mean HHI')
    for i,y in enumerate(hhi): axes[0].text(i,y+.0005,f"{y:.4f}",ha="center",fontsize=10)
    data=[dict(version=v,hhi=y) for v,y in zip(versions,hhi)]
    for ax,strategy,title in zip(axes[1:],STRATEGIES,['Random shock','Original targeted shock']):
        for v,marker,ls in zip(versions,["o","^","s"],["-","--",":"]):
            y=values(rows,"mean_additional_failures",strategy=strategy,version=v)
            ax.plot(np.array(FRACTIONS)*100,y,marker=marker,ls=ls,lw=2.1,color=COLORS[v],
                    label="Original" if v=="original" else LABELS[v])
            data.append(dict(version=v,strategy=strategy,mean_additional=y.tolist()))
        ax.set_title(title,loc="left",pad=18); severity(ax); clean(ax); ax.set_ylim(0,340)
        ax.set_ylabel('Mean additional failures',labelpad=8)
        ax.legend(loc="upper left",frameon=False,fontsize=9)
    footer(fig,['HHI: sum of squared link shares; average across four transitions per network and twenty networks.',
        'Identical shocks across versions. The targeted ranking is fixed on the original and is not adapted to the new network.',
        'Limited sensitivity: one realization per level and network. This does not isolate a causal effect of HHI.'])
    export(fig,"figure4_concentracion",data)


def figure5():
    firms=read("betweenness1000_firms.csv")
    groups=read("betweenness1000_groups.csv")
    assert len(firms)==20000 and len({(r["network_id"],r["firm"]) for r in firms})==20000
    fig,axes=canvas("05",'Betweenness and withdrawal damage differ',
        '20,000 saved individual withdrawals: one per firm in each of the twenty original networks.',2)
    ax=axes[0]
    for layers,color,label,marker in [([1,2,3],GRAY,'Intermediate layers',"."),([4],BLUE,'Last layer',"s"),([0],WINE,'Sources',"o")]:
        subset=[r for r in firms if int(r["layer"]) in layers]
        ax.scatter([float(r["betweenness_raw"]) for r in subset],
                   [int(r["total_failures"]) for r in subset],
                   s=10 if marker=="." else 20,alpha=.25 if marker=="." else .65,
                   marker=marker,color=color,label=label,rasterized=True)
    max_damage=max(firms,key=lambda r:int(r["total_failures"]))
    max_between=max(firms,key=lambda r:float(r["betweenness_raw"]))
    assert max_damage["network_id"]=="N02" and max_damage["firm"]=="E030"
    assert max_between["network_id"]=="N20" and max_between["firm"]=="E461"
    ax.annotate("N02 · E030",(0,13),xytext=(42,11.8),
                arrowprops=dict(arrowstyle="-",color=WINE),fontsize=10,color=WINE)
    ax.annotate("N20 · E461",(float(max_between["betweenness_raw"]),4),
                xytext=(155,6.5),arrowprops=dict(arrowstyle="-",color=NAVY),fontsize=10,color=NAVY)
    ax.set_xlim(-8,242); ax.set_ylim(.4,14)
    ax.set_xlabel('Raw directed betweenness',labelpad=13)
    ax.set_title('Network position and individual damage',loc="left",pad=18)
    clean(ax,'Total failures\n(including the initial withdrawal)')
    ax.legend(loc="upper center",bbox_to_anchor=(.52,.76),frameon=False,fontsize=9)
    layer_rows=[select(groups,group_by="layer",value=i) for i in range(5)]
    y=[float(r["mean_total_failures"])-1 for r in layer_rows]
    axes[1].bar(range(5),y,color=[WINE,GRAY,GRAY,GRAY,BLUE],width=.6)
    axes[1].set_xticks(range(5),['0\nsources',"1","2","3",'4\nno customers'])
    axes[1].set_xlabel('Layer of the withdrawn firm',labelpad=13)
    axes[1].set_ylim(0,.62); clean(axes[1],'Mean additional failures')
    axes[1].set_title('Zero betweenness mixes different positions',loc="left",pad=18,fontsize=12)
    for i,v in enumerate(y): axes[1].text(i,v+.016,f"{v:.3f}",ha="center",fontsize=10)
    footer(fig,['Sources and last-layer firms have zero betweenness: path endpoints are excluded.',
        'Left: overlapping points, with no fitted trend. Right: 4,000 firms per layer.',
        'Ties select the first network/firm identifier. Descriptive comparison; no causal or real-firm calibration claim.'])
    export(fig,"figure5_intermediacion_y_dano",[dict(max_damage=max_damage,max_betweenness=max_between),dict(layer_means_additional=y)])


def figure6():
    rows=read("connectivity1000_summary.csv")
    benchmark=read("connectivity1000_benchmark_summary.csv")
    fig,axes=canvas("C1",'Operational survival is not connectivity',
        'Fragmentation among surviving firms; weak components ignore arrow direction.',2)
    data=[]
    for ax,strategy,title in zip(axes,STRATEGIES,['Random withdrawals','Withdrawals by original customer counts']):
        for v,marker,ls in zip(["original","redundant","pool150","pool100"],["s","o","^","D"],["-","-","--",":"]):
            baseline=float(select(benchmark,version=v)["mean_fragmentation"])
            y=[baseline]+values(rows,"mean_fragmentation",strategy=strategy,version=v).tolist()
            assert all(0<=value<=1 for value in y)
            ax.plot([0,1,5,10,20],y,marker=marker,ls=ls,lw=2.1,color=COLORS[v],label="Original" if v=="original" else LABELS[v])
            data.append(dict(strategy=strategy,version=v,fragmentation=y))
        ax.set_title(title,loc="left",pad=18); clean(ax); ax.set_ylim(0,1)
        ax.set_xlim(-.5,21); ax.set_xticks([0,1,5,10,20],['Before',"1 %","5 %","10 %","20 %"])
        # Separate the zero and one labels without changing the numerical scale.
        ax.get_xticklabels()[0].set_horizontalalignment("right")
        ax.get_xticklabels()[1].set_horizontalalignment("left")
        ax.set_xlabel('Initially withdrawn firms',labelpad=13)
        ax.legend(loc="upper left",frameon=False,fontsize=9)
    axes[0].set_ylabel('Mean fragmentation\n0 = one component; 1 = all isolated',labelpad=12)
    footer(fig,['Fragmentation is the probability that two distinct survivors belong to different components.',
        'Versions start with different connectivity; the Before point avoids attributing all differences to the shock.',
        'Same shocks across versions. Weak connectivity does not measure productive flows or supply sufficiency.'])
    export(fig,"figureC1_conectividad",data)


def main():
    style()
    (ROOT/"figures").mkdir(exist_ok=True)
    names=["figure2_severidad_y_estrategia","figure3_redundancia","figure4_concentracion",
           "figure5_intermediacion_y_dano","figureC1_conectividad"]
    targets=[ROOT/"figures"/f"{name}.{ext}" for name in names for ext in ("png","svg","pdf")]
    metadata_path = ROOT/"figures"/"figures_metadata.json"
    captions_path = ROOT/"figures"/"figure_captions.md"
    targets.extend([metadata_path, captions_path])
    if any(p.exists() for p in targets):
        raise FileExistsError('Figures for this stage already exist; use a clean copy to reproduce.')
    for function in [figure2,figure3,figure4,figure5,figure6]:
        function()
    metadata={"source_sha256":SOURCES,"figures":RECORDS,
        "palette_reference":"Kairos Laboratory base palette, intensified at Josue's request on October 5, 2026",
        "palette":dict(bg=BG,ink=INK,dim=DIM,line=LINE,wine=WINE,blue=BLUE,navy=NAVY,gold=GOLD,gray=GRAY,pool150=COLORS["pool150"]),
        "fonts":'DejaVu Sans / Mono: portable alternatives to Space Grotesk and IBM Plex Mono',
        "matplotlib":matplotlib.__version__,"numpy":np.__version__,
        "aggregation":'Saved means: equal network weights and 100 repetitions per network. Figure 5 groups firms by layer.',
        "simulations_run":0,"status":'Drafts for review'}
    metadata["captions_file"] = "figure_captions.md"
    metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sections = ['# Figure captions', "Captions kept separate from images at Josue's request. Preserve methodological notes when publishing."]
    for number, caption in CAPTIONS.items():
        sections += [f"## Figure {number}: {caption['title']}", f"File: `{caption['filename']}`", caption["subtitle"]]
        sections.extend(caption["notes"])
    captions_path.write_text("\n\n".join(sections)+"\n", encoding="utf-8")
    print('Five figures exported; no simulations. Data and SHA-256 in figures_metadata.json.')


if __name__=="__main__":
    main()
