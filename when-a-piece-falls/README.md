# When a Piece Falls

Kairos Laboratory · Network science experiment

**Question:** How can a small disruption propagate through supply dependencies, and why does withdrawing one firm cause more damage than withdrawing another?

A transparent synthetic model with saved results, reproducible seeds, tests and six research figures. This is an investigation of network mechanisms, not a calibrated economy or a prediction about real firms. Original Spanish title: *Cuando cae una pieza*.

**Status — October 5, 2026:** analyses and figures complete; 61 tests passed. A full clean end-to-end reproduction and the accessible/technical research articles remain pending. Restoring saved data does not replace reproducing the simulation. V1 closes after the six research questions below are addressed with explicit limitations and clean reproduction is verified; a system-wide collapse is not required.

The study examines propagation, random versus targeted shocks, systemic importance, redundancy, concentration and the limits of an efficiency comparison, and sensitivity to structural choices. Results are interpreted within this model; claims of general robustness require more than the sensitivity checks performed here.

## Start here

From the `when-a-piece-falls/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/restore_results.py
python -m unittest discover -s tests -v
```

Verified with Python 3.12.14, NetworkX 3.6.1, Matplotlib 3.10.8 and NumPy 2.3.5. On Windows, use the equivalent virtual-environment activation command.

Restoration uses only the standard library, validates compressed and original SHA-256 hashes, skips matching existing files and refuses to overwrite different files. It runs no simulations. Twelve large CSVs are stored losslessly in `results/archives/`; restoration returns them to `results/`. Their local copies are excluded from Git.

## Files

| Path | Contents |
|---|---|
| `src/` | Model, experiments, diagnostics, plotting and archive restoration |
| `tests/` | Twelve test files; 61 tests at the last validation |
| `results/` | 90 reference outputs, including lossless archives and file manifests |
| `figures/` | Six English research figures in PNG, SVG and PDF, plus plotting metadata |
| `requirements.txt` | Pinned dependencies |

This README is the single guide to methods, results and reproduction. Spanish website images are delivered separately under `pieza-cae/`.

## Model

A directed edge `A -> B` means that A supplies B. Nodes are synthetic firms. Networks have five equal layers, links from the immediately preceding layer, and no cycles. In the 1,000-firm benchmark each layer contains 200 firms; layer 0 consists of sources. Each non-source independently selects one, two or three distinct suppliers with equal probability, uniformly within the preceding layer.

Suppliers are **complete substitutes**: one active original supplier is sufficient to keep a customer operational. A non-source fails if all its original suppliers have failed. Sources do not fail endogenously through supply loss, but can be withdrawn directly. Failures are synchronous, irreversible and deterministic conditional on the network and initial withdrawals. Propagation stops when a round produces no new failures. Rounds are logical steps, not calibrated time.

Synthetic sizes 1, 2 and 4 are assigned independently of topology and are not used by the failure rule. They are labels, not output, employment, sales or capacity. The model therefore cannot establish that economic size is irrelevant in real supply networks.

There are no capacity constraints, prices, inventories, adaptation, recovery, costs or substitution delays. The experiment measures continuity and damage, not welfare, profitability or economic efficiency.

## Experimental design

- **Original networks:** twenty 1,000-firm networks. Topology seeds `1000+i` and size seeds `2000+i`, with `i=0..19`. Earlier eight-firm and 100-firm stages are preserved for teaching and scale checks, not pooled with the final networks.
- **Random shocks:** 1%, 5%, 10% and 20% initial withdrawals; 100 repetitions per network and severity. Within-shock sampling is uniform without replacement. Random shocks are freshly drawn; severity sets are not nested. Final random-batch seeds are `3000+4*i+scenario_index`, with scenario indices 0–3 in severity order.
- **Targeted shocks:** rank by original out-degree (customer count), with randomized tie-breaking. Each ranking is formed before withdrawal; its severity prefixes are nested. Seeds are `4000 + 100*i + repetition - 1`. Random and targeted shocks are not paired case by case.
- **Individual census:** withdraw each firm once from each original network: 20,000 deterministic cases. Every case starts from the unchanged benchmark.
- **Redundancy:** add one distinct alternative supplier to every non-source from the previous layer, preserving original links and attributes. This adds 800 edges per network. R1 uses seeds `6000+i`; R2 and R3 use `7000+i` and `8000+i`, independently starting from the original. Joint-shock comparisons reuse the exact saved withdrawal sets and original targeted ranking.
- **Concentration:** reassign suppliers through uniformly selected eligible pools of 100 or 150 firms per supplier layer, with seeds `9000+i` and `10000+i`. Preserve firms, attributes, supplier count per customer and total edges per transition. Supplier identities, paths and initial connectivity change. Pools across levels are not required to be nested. Reuse the original shocks without reranking variants.
- **Diagnostics:** weak connectivity on benchmarks and saved final states; exact directed betweenness on the original networks and teaching example. No new betweenness-targeted attacks were added.

Network means receive equal weight. Repeated shocks on one network are not independent economies. Assignment ranges are descriptive, not confidence intervals. The concentration sensitivity has one realization per level and network; it does not isolate the parameter from assignment randomness.

## Metrics

| Metric | Definition |
|---|---|
| Initial failures | Firms withdrawn by the shock |
| Additional failures | Subsequent failures caused by loss of all suppliers |
| Total failures | Initial plus additional failures |
| Functional firms (%) | 100 times survivors divided by original firm count; not output or GDP |
| Amplification | Total failures divided by initial failures |
| Propagation rounds | Nonempty failure rounds after round 0 |
| Supplier HHI | Sum of squared supplier shares in a transition's links; not sales concentration |
| Largest weak component | Largest component in the survivor-induced graph when direction is ignored |
| Fragmentation | `1 - sum(n_j*(n_j-1))/(A*(A-1))`, for component sizes `n_j` and A survivors |
| Directed betweenness | Fractions of directed shortest paths through a node, excluding endpoints |

Fragmentation is undefined for fewer than two survivors; it is not imputed as zero. Largest-component shares use the original network size as denominator. HHI is averaged equally over four transitions per network and then over twenty networks. Betweenness uses exact NetworkX Brandes (`k=None`, unweighted, no endpoints), with normalized values equal to raw values divided by `(n-1)*(n-2)` for `n>2`. Unreachable pairs contribute zero, while all possible pairs remain in the normalization denominator.

## Main findings

| Comparison | Saved finding |
|---|---|
| Individual withdrawals | 22.76% produced additional failures; mean total failures 1.35105; maximum 13 |
| Original, 20% random shock | Mean total failures 277.111 |
| Original, 20% targeted shock | Mean total failures 493.463 |
| R1 redundancy, 20% random shock | Mean total failures 211.8555 |
| R1 redundancy, 20% original-targeted shock | Mean total failures 258.0075 |
| Concentration, 20% original-targeted shock | Pool100: 310.973; pool150: 310.7295 mean total failures |
| Mean link HHI | Original: 0.007435957; pool150: about 0.00906122; pool100: 0.012469023 |

No individual withdrawal collapsed an entire original network. The maximum-damage case, N02/E030, had raw directed betweenness zero and caused 13 total failures. The maximum-betweenness case, N20/E461, had raw betweenness 225.833333 and caused four total failures. Sources and sinks have zero betweenness by definition here, so zero betweenness does not imply low supply importance.

Adding alternatives eliminated individual-shock propagation, as the rule mechanically guarantees once every non-source has at least two distinct suppliers. Joint shocks still produced cascades. Across three assignments, mean total damage at 20% original-targeted withdrawal ranged from 257.463 to 258.0075, with larger local differences across assignments within some networks. This is limited assignment sensitivity, not general robustness.

Concentration effects were not uniform: random-shock averages were close across levels, while damage under fixed original-targeted sets was lower after rewiring. This does not show protection against attacks reranked on the modified networks. Nor does it identify an isolated causal effect of HHI. Adding redundancy also changes edge count, so that comparison alone does not isolate structure at equal link counts.

The model cannot quantify an efficiency-resilience trade-off because costs and output are absent. It demonstrates properties of a specified synthetic mechanism, not causal or predictive effects in real economies.

## Reading the saved results

| Prefix / file family | Purpose |
|---|---|
| `pilot_*` | Fixed 100-firm pilot, original 1% random batch and separate 5/10/20% severity batches |
| `networks100_*` | Twenty-network 100-firm scale check |
| `networks1000_*` | Final twenty 1,000-firm references and random shocks |
| `targeted1000_*` | Original out-degree targeting and random/targeted comparison |
| `individual1000_*` | 20,000 individual withdrawals, rounds and descriptive groups |
| `redundancy1000_*` | R1 construction, individual validation and summaries |
| `redundancy1000_joint_*` | Fixed original joint shocks on R1; paired variant comparison |
| `redundancy1000_robustness_*` | R2/R3 assignments, fixed shocks and assignment ranges |
| `concentration1000_*` | Pool100 construction, eligible suppliers and HHI |
| `concentration1000_joint_*` | Fixed original shocks on pool100 |
| `concentration1000_sensitivity_*` | Pool150, same controls and three-version comparisons |
| `connectivity1000_*` | Benchmarks and survivor-state weak connectivity across four versions |
| `betweenness_example.csv` | Exact eight-node directed betweenness |
| `betweenness1000_*` | Exact original-network betweenness joined to the saved individual census |

Files named `summary` contain aggregate results; `per_network` retain network-level means; `shocks` identify initial/final selections; `rounds` record failure timing; `nodes`/`edges`/`manifest` identify exact saved graphs; `metadata` specify methods, versions, sources and stage-specific limitations. Historical metadata describes the stage at its execution time, not necessarily the project's current completion status.

`results/RESULTS_MANIFEST.json` describes the 90 output files. Twelve large detailed CSVs are stored under `results/archives/`, with compressed and original-byte hashes in `archives/manifest.json`. Run `python src/restore_results.py` before reading those detailed CSVs. The archive utility never changes numerical data or creates new observations.


Network/strategy summaries average 100 cases per network and weight twenty networks equally. Individual groups pool firms sharing network structure. Undefined fragmentation cases are excluded with their denominators recorded; no inferential confidence intervals or p-values are implied. Historical metadata describes each stage at its execution time.

## Reproduce from scratch

Use a separate copy of the source, documentation and tests, with empty `results/` and no existing figure outputs. Do not restore historical results into that clean copy. Activate the virtual environment and install pinned dependencies, then run from the project root:

```bash
python -m unittest discover -s tests -v
python src/network.py
python src/cascades.py
python src/experiments.py
python src/experiments.py --severity
python src/experiments.py --networks --n 100
python src/experiments.py --networks --n 1000
python src/targeted.py
python src/individual.py
python src/redundancy.py
python src/redundancy.py --joint
python src/robustness.py
python src/concentration.py
python src/concentration.py --joint
python src/structural_sensitivity.py
python src/connectivity.py
python src/betweenness.py
python src/figure1.py
python src/plot_results.py
```

Order matters because later stages read previous exports. The initial commands preserve the pilot and 100-firm development stages. Final comparisons use twenty 1,000-firm networks. No extra model settings or economic mechanics are introduced by this sequence.

Compare generated CSVs, network edges, withdrawals and metrics with the reference package's `results/RESULTS_MANIFEST.json`. Translation changed human-readable metadata values; compare scientific fields rather than requiring literal metadata-byte identity. Timing/version fields and image bytes may vary by environment. Record the actual environment and any discrepancies.

This documented sequence has been reviewed against entry points but has not yet been executed completely from scratch as one clean run. Passing unit tests or restoring archived results must not be reported as completion of that pending check.

## Figures and interpretation

| Figure / filename stem | Reading guide |
|---|---|
| 1 · `figure1_red_y_cascada` | Eight-firm teaching example: withdraw C; D/E fail in round 1 and F in round 2. G retains supplier H. One initial and three additional failures; this selected example is not typicality evidence. |
| 2 · `figure2_severidad_y_estrategia` | Mean **total** failures by severity and strategy. Bars show the minimum/maximum of twenty network means, not confidence intervals. |
| 3 · `figure3_redundancia` | Mean **additional** failures with R1 alternatives under identical shocks. Adds 800 edges per network; costs and capacity are absent. Adding substitutes cannot worsen a cascade under this rule. |
| 4 · `figure4_concentracion` | Link HHI and additional failures for original/pool150/pool100. Equal edge counts and customer in-degrees; identities and routes change. Original-targeted sets are fixed, not adapted. One assignment per level/network; no isolated causal HHI effect. |
| 5 · `figure5_intermediacion_y_dano` | All 20,000 individual cases and layer means (4,000 firms per layer). Overlapping points, no fitted trend or jitter; opacity is not a frequency scale. Sources/sinks have zero betweenness. Ties select the first network/firm identifier. |
| C1 · `figureC1_conectividad` | Weak fragmentation of survivors, including different pre-shock baselines. Direction is ignored for component grouping; connectivity is not productive flow or supply sufficiency. |

Figures 2 and 3/4 use different failure measures: account for initial withdrawals when comparing vertical values. Lines connect observed severities; intermediate severities were not simulated. Keep these qualifications with figures when publishing.

To regenerate figures, restore the detailed reference CSVs and use a copy with an empty `figures/` directory:

```bash
python src/figure1.py
python src/plot_results.py
```

Only Figure 1 evaluates the existing teaching cascade; `plot_results.py` reads saved results and draws no new shocks or networks. Plotting also exports captions and metadata with source hashes. Fonts are embedded in PDF and outlined in SVG.

## Scope and future work

V1 deliberately excludes capacity, substitution delays, costs, inventories, recovery, meaningful economic-size effects, dynamic prices, banks, governments, comprehensive international trade, general equilibrium, strategic/learning agents, machine learning, reinforcement learning, LLM agents, causal inference and real-firm calibration.

A partial-substitution threshold would change the assumption that one active supplier is sufficient. These mechanisms belong to separate future research questions; none is an implementation task for this experiment. Preserve unexpected findings and do not change assumptions to manufacture a crisis.
