# Public Procurement Corruption Lab

A reproducible computational experiment from **Kairos Labs** exploring how corruption can distort public procurement, how detection and sanctions change strategic incentives, and how enforcement costs and behavioral adaptation affect policy outcomes.

The project combines game theory, synthetic procurement markets, policy simulation, institutional cost analysis, sensitivity analysis, and dynamic behavioral adaptation.

> **Important:** This is a theoretical and computational experiment. The simulated firms, procurement processes, behavioral responses, and corruption mechanisms are synthetic. Results should not be interpreted as empirical estimates of corruption in any specific country or procurement system.

---

## Research question

Public procurement systems are designed to allocate contracts according to criteria such as price, quality, experience, and risk.

But what happens when firms and public officials can strategically deviate from those rules?

This lab studies several related questions:

- When is offering a bribe strategically attractive to a firm?
- When is accepting a bribe attractive to a public official?
- How does corruption alter procurement outcomes and public value?
- How much detection or punishment is required to change those incentives?
- Are different combinations of detection and sanctions strategically equivalent?
- What happens when enforcement itself is costly?
- How sensitive is the preferred enforcement policy to institutional costs?
- Can a reform change behavior over repeated procurement rounds?

The objective is not to estimate real-world corruption rates. It is to construct a transparent computational environment in which these mechanisms can be examined.

---

## Experimental structure

The project is organized as a sequence of connected computational experiments.

### Experiments 1–3 — Strategic incentives

The first stage constructs the underlying game between firms and public officials.

The baseline parameters include:

- contract benefit: `100`
- bribe: `20`
- probability of detection: `10%`
- firm sanction: `100`
- official sanction: `100`
- probability of winning honestly: `30%`
- probability of winning through corruption: `90%`

Under the baseline assumptions:

- expected payoff to the firm from honest participation: `30`
- expected payoff from bribery: `60`
- expected payoff to the official from accepting the bribe: `10`
- payoff from rejecting it: `0`

The model also derives theoretical deterrence thresholds.

Under the baseline configuration:

- the official stops accepting once expected punishment offsets the bribe;
- the firm stops finding bribery attractive once expected sanctions eliminate its strategic advantage.

The experiment then maps these incentives across combinations of detection probabilities and sanctions.

---

## Experiment 4 — Synthetic procurement market

The next stage creates a synthetic public procurement environment.

Firms compete using procurement characteristics including:

- quality;
- price;
- experience;
- risk.

The honest procurement mechanism evaluates bids using a weighted scoring rule.

Baseline weights:

| Criterion | Weight |
|---|---:|
| Quality | 30% |
| Price | 25% |
| Experience | 25% |
| Low risk | 20% |

This produces the benchmark allocation that would occur under the modeled honest procurement system.

The experiment records both individual bids and winning firms so later experiments can compare honest and corrupted allocations.

---

## Experiment 5 — Corruption enters the market

The corruption experiment introduces strategic bribery into the synthetic procurement environment.

Under the baseline configuration:

- 500 firms participate;
- 100 corruption attempts occur;
- 100 bribes are accepted;
- 100 procurement awards are distorted.

The benchmark simulation produces:

| Outcome | Value |
|---|---:|
| Honest public value | 8,197.05 |
| Corrupt public value | 5,653.88 |
| Public-value loss | 2,543.17 |
| Relative loss | 31.03% |
| Mean loss per tender | 25.43 |

These values describe the synthetic baseline experiment and are **not empirical estimates of real procurement losses**.

---

## Experiment 6 — Detection policy

The model then varies the probability that corruption is detected.

The experiment evaluates how stronger detection affects:

- corruption attempts;
- accepted bribes;
- distorted awards;
- public value;
- corruption losses.

This allows the deterrence mechanism predicted by the game-theoretic model to be observed inside the simulated procurement market.

---

## Experiments 7–8 — Sanctions and policy combinations

Detection is only one enforcement instrument.

The next experiments vary sanctions and study combinations of:

- detection probability;
- firm penalties;
- official penalties.

An important implication of the theoretical model is that different enforcement configurations can generate equivalent strategic incentives.

For example, combinations satisfying the same expected-penalty condition may produce similar deterrence.

The policy grid therefore examines enforcement as a joint design problem rather than treating detection and punishment independently.

---

## Institutional enforcement costs

Perfect enforcement is not free.

The model therefore introduces a stylized institutional cost function for monitoring and sanctions.

The policy objective becomes:

**maximize net public value**

rather than simply:

**maximize deterrence**

This creates a trade-off between:

- reducing corruption;
- recovering public value;
- and paying for enforcement capacity.

Under the baseline institutional-cost assumptions used in the experiment, the simulated preferred clean policy is:

- detection probability: `20%`
- sanction: `100`
- institutional cost: `90`
- net public value: `8,107.05`

These results are conditional on the synthetic cost function and should not be interpreted as policy prescriptions for real procurement systems.

---

## Cost sensitivity

Because institutional enforcement costs are uncertain, the lab performs sensitivity analysis across alternative cost assumptions.

The experiment evaluates how the preferred combination of detection and sanctions changes as monitoring and punishment become more or less expensive.

This section illustrates an important distinction:

A policy can be effective at eliminating corruption while still being inefficient if achieving that deterrence requires excessively costly enforcement.

---

## Experiment 9 — Dynamic behavioral adaptation

The final stage introduces repeated procurement rounds.

The simulation contains:

- 100 rounds;
- a reform beginning in round 51;
- heterogeneous but deterministic adaptation among corruption-eligible firms.

Before the reform, corruption remains strategically attractive under the modeled parameters.

After the reform changes expected enforcement, accepted corruption falls to zero.

In the reproduced simulation:

| Period | Corruption attempts | Accepted bribes | Distorted awards | Average public value |
|---|---:|---:|---:|---:|
| Pre-reform | 5,000 | 5,000 | 5,000 | 5,653.88 |
| Post-reform | 1,625 | 0 | 0 | 8,197.05 |

By round 100:

- corruption attempts: `0`
- accepted bribes: `0`
- eligible-firm average propensity: `0.221`
- eligible losing firms above the behavioral threshold: `0`

The behavioral adaptation mechanism and heterogeneous learning rates are **synthetic assumptions** introduced to study persistence and adaptation. They are not estimates of actual firm behavior.

---

## Repository structure

```text
public-procurement-corruption/
│
├── README.md
├── requirements.txt
│
├── src/
│   ├── game.py
│   ├── market.py
│   ├── corruption.py
│   ├── analysis.py
│   ├── policy.py
│   ├── sanctions.py
│   ├── cost.py
│   ├── cost_sensitivity.py
│   ├── dynamics.py
│   ├── select_figures.py
│   └── select_results.py
│
├── figures/
│   └── generated visualizations
│
└── results/
    └── generated CSV outputs
```

---

## Reproducing the experiment

### 1. Clone Kairos Labs

```bash
git clone https://github.com/josuetartons-cpu/kairos-labs.git
cd kairos-labs/public-procurement-corruption
```

### 2. Create an isolated Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the computational pipeline

Run the scripts in this order:

```bash
python src/game.py
python src/market.py
python src/corruption.py
python src/analysis.py
python src/policy.py
python src/sanctions.py
python src/cost.py
python src/cost_sensitivity.py
python src/dynamics.py
```

Or stop automatically if any stage fails:

```bash
python src/game.py &&
python src/market.py &&
python src/corruption.py &&
python src/analysis.py &&
python src/policy.py &&
python src/sanctions.py &&
python src/cost.py &&
python src/cost_sensitivity.py &&
python src/dynamics.py
```

The scripts regenerate the corresponding files in `results/` and `figures/`.

---

## Reproducibility validation

Before publication, the complete experiment was reproduced from a clean Python virtual environment using the dependencies specified in `requirements.txt`.

The pipeline was executed sequentially from `game.py` through `dynamics.py`.

SHA-256 hashes were calculated for the 22 CSV outputs before and after reproduction.

All 22 regenerated result files matched the reference outputs **exactly at the SHA-256 level**.

This validates deterministic computational reproducibility for the tested environment.

---

## Main outputs

The repository contains visualizations covering:

- game-theoretic detection thresholds;
- sanction thresholds;
- strategic regions;
- honest procurement outcomes;
- honest versus corrupted public value;
- corruption losses;
- detection-policy sweeps;
- sanction-policy sweeps;
- joint enforcement policy maps;
- institutional enforcement costs;
- net public value;
- cost sensitivity;
- dynamic corruption attempts;
- accepted bribes;
- behavioral adaptation;
- public value over repeated rounds.

The `results/` directory contains the underlying CSV outputs used for these analyses.

---

## Interpretation and limitations

This lab is designed to explore mechanisms, not to estimate causal effects or actual corruption prevalence.

Several components are deliberately synthetic, including:

- the population of firms;
- procurement characteristics;
- corruption opportunities;
- probabilities of honest and corrupt success;
- sanctions and detection parameters;
- institutional enforcement costs;
- behavioral adaptation;
- heterogeneous learning rates.

The numerical results therefore describe the internal behavior of the simulated model.

They should not be interpreted as estimates of:

- corruption prevalence in Guatemala or any other country;
- actual procurement losses;
- real firm or official behavior;
- optimal legal sanctions;
- optimal real-world enforcement budgets.

The value of the experiment lies in making theoretical mechanisms explicit and computationally testable.

---

## Relationship to Kairos

This repository contains the reproducible computational material behind a **Kairos** research publication on corruption and public procurement.

Kairos separates:

- **editorial research and explanation**, published on the main website;
- **reproducible code and computational experiments**, maintained in Kairos Labs.

This structure allows readers to move from the argument and interpretation to the underlying model, outputs, and code.

---

## License

This project is distributed under the license specified in the root of the **Kairos Labs** repository.

---

## Kairos Labs

**Kairos Labs** is the reproducible research and computational experimentation layer of Proyecto Kairos.

Its purpose is to make selected analyses, simulations, models, and data workflows transparent and reproducible.