import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# Game 1: Empresa vs Funcionario
#
# Experimentos:
# 1. Benchmark
# 2. Barrido de detección
# 3. Detección x sanción
# ============================================================


# ------------------------------------------------------------
# 1. PARÁMETROS BASE
# ------------------------------------------------------------

PROFIT = 100
BRIBE = 20

BASE_DETECTION_PROBABILITY = 0.10

BASE_FIRM_PENALTY = 100
BASE_OFFICIAL_PENALTY = 100

HONEST_WIN_PROBABILITY = 0.30
CORRUPT_WIN_PROBABILITY = 0.90


# ------------------------------------------------------------
# 2. FUNCIONES DE PAYOFF
# ------------------------------------------------------------

def firm_honest_payoff(
    profit,
    honest_win_probability
):
    """
    Utilidad esperada de competir honestamente.
    """
    return honest_win_probability * profit


def firm_bribe_payoff(
    profit,
    bribe,
    detection_probability,
    firm_penalty,
    corrupt_win_probability
):
    """
    Utilidad esperada de sobornar cuando
    el funcionario acepta el soborno.
    """
    return (
        corrupt_win_probability * profit
        - bribe
        - detection_probability * firm_penalty
    )


def official_accept_payoff(
    bribe,
    detection_probability,
    official_penalty
):
    """
    Utilidad esperada del funcionario
    si acepta el soborno.
    """
    return (
        bribe
        - detection_probability * official_penalty
    )


def official_reject_payoff():
    """
    Normalizamos el payoff de rechazar a cero.
    """
    return 0


# ------------------------------------------------------------
# 3. UMBRALES TEÓRICOS
# ------------------------------------------------------------

def official_detection_threshold(
    bribe,
    official_penalty
):
    """
    p* = B / F_f
    """
    return bribe / official_penalty


def firm_detection_threshold(
    profit,
    bribe,
    firm_penalty,
    honest_win_probability,
    corrupt_win_probability
):
    """
    p* = [ (q_c - q_h) * pi - B ] / F_e
    """
    return (
        (
            corrupt_win_probability
            - honest_win_probability
        )
        * profit
        - bribe
    ) / firm_penalty


def official_penalty_threshold(
    bribe,
    detection_probability
):
    """
    F_f* = B / p

    No existe un umbral finito cuando p = 0.
    """
    if detection_probability == 0:
        return np.inf

    return bribe / detection_probability


def firm_penalty_threshold(
    profit,
    bribe,
    detection_probability,
    honest_win_probability,
    corrupt_win_probability
):
    """
    F_e* =
    [ (q_c - q_h) * pi - B ] / p

    No existe un umbral finito cuando p = 0.
    """
    if detection_probability == 0:
        return np.inf

    corruption_advantage = (
        (
            corrupt_win_probability
            - honest_win_probability
        )
        * profit
        - bribe
    )

    return corruption_advantage / detection_probability


# ------------------------------------------------------------
# 4. RESOLVER EL JUEGO
# ------------------------------------------------------------

def solve_game(
    detection_probability,
    firm_penalty,
    official_penalty
):
    """
    Resuelve el juego para una combinación concreta
    de detección y sanciones.
    """

    honest_payoff = firm_honest_payoff(
        PROFIT,
        HONEST_WIN_PROBABILITY
    )

    bribe_payoff = firm_bribe_payoff(
        PROFIT,
        BRIBE,
        detection_probability,
        firm_penalty,
        CORRUPT_WIN_PROBABILITY
    )

    accept_payoff = official_accept_payoff(
        BRIBE,
        detection_probability,
        official_penalty
    )

    reject_payoff = official_reject_payoff()

    # Usamos > y no >=.
    # En puntos exactos de indiferencia no clasificamos
    # al agente como participante corrupto.

    firm_prefers_bribe = (
        bribe_payoff > honest_payoff
    )

    official_prefers_accept = (
        accept_payoff > reject_payoff
    )

    corruption_sustainable = (
        firm_prefers_bribe
        and official_prefers_accept
    )

    return {
        "p": detection_probability,
        "firm_penalty": firm_penalty,
        "official_penalty": official_penalty,
        "firm_honest_payoff": honest_payoff,
        "firm_bribe_payoff": bribe_payoff,
        "official_accept_payoff": accept_payoff,
        "official_reject_payoff": reject_payoff,
        "firm_prefers_bribe": firm_prefers_bribe,
        "official_prefers_accept": official_prefers_accept,
        "corruption_sustainable": corruption_sustainable
    }


# ============================================================
# EXPERIMENTO 1
# BENCHMARK
# ============================================================

base_case = solve_game(
    detection_probability=BASE_DETECTION_PROBABILITY,
    firm_penalty=BASE_FIRM_PENALTY,
    official_penalty=BASE_OFFICIAL_PENALTY
)

official_threshold = official_detection_threshold(
    BRIBE,
    BASE_OFFICIAL_PENALTY
)

firm_threshold = firm_detection_threshold(
    PROFIT,
    BRIBE,
    BASE_FIRM_PENALTY,
    HONEST_WIN_PROBABILITY,
    CORRUPT_WIN_PROBABILITY
)


print("\n" + "=" * 65)
print("KAIROS CORRUPTION LAB")
print("GAME 1 — BENCHMARK")
print("=" * 65)

print("\nPARÁMETROS BASE")
print(f"Beneficio del contrato: {PROFIT}")
print(f"Soborno: {BRIBE}")

print(
    f"Probabilidad de detección: "
    f"{BASE_DETECTION_PROBABILITY:.0%}"
)

print(
    f"Sanción empresa: "
    f"{BASE_FIRM_PENALTY}"
)

print(
    f"Sanción funcionario: "
    f"{BASE_OFFICIAL_PENALTY}"
)

print(
    f"Probabilidad de ganar honestamente: "
    f"{HONEST_WIN_PROBABILITY:.0%}"
)

print(
    f"Probabilidad de ganar con corrupción: "
    f"{CORRUPT_WIN_PROBABILITY:.0%}"
)


print("\nPAYOFFS EMPRESA")

print(
    f"Competir honestamente: "
    f"{base_case['firm_honest_payoff']:.2f}"
)

print(
    f"Sobornar si es aceptado: "
    f"{base_case['firm_bribe_payoff']:.2f}"
)


print("\nPAYOFFS FUNCIONARIO")

print(
    f"Aceptar soborno: "
    f"{base_case['official_accept_payoff']:.2f}"
)

print(
    f"Rechazar soborno: "
    f"{base_case['official_reject_payoff']:.2f}"
)


print("\nUMBRALES TEÓRICOS")

print(
    f"Funcionario: "
    f"{official_threshold:.0%}"
)

print(
    f"Empresa: "
    f"{firm_threshold:.0%}"
)


print("\nRESULTADO")

if base_case["corruption_sustainable"]:
    print("Corrupción estratégicamente sostenible.")
else:
    print(
        "La transacción corrupta no es "
        "estratégicamente sostenible."
    )


# ------------------------------------------------------------
# VALIDACIÓN AUTOMÁTICA DEL BENCHMARK
# ------------------------------------------------------------

assert np.isclose(
    base_case["firm_honest_payoff"],
    30
)

assert np.isclose(
    base_case["firm_bribe_payoff"],
    60
)

assert np.isclose(
    base_case["official_accept_payoff"],
    10
)

assert np.isclose(
    official_threshold,
    0.20
)

assert np.isclose(
    firm_threshold,
    0.40
)

assert base_case["corruption_sustainable"] is True


print("\nBenchmark validado correctamente.")


# ============================================================
# EXPERIMENTO 2
# BARRIDO DE DETECCIÓN
# ============================================================

detection_results = []


for i in range(0, 101):

    p = i / 100

    result = solve_game(
        detection_probability=p,
        firm_penalty=BASE_FIRM_PENALTY,
        official_penalty=BASE_OFFICIAL_PENALTY
    )

    result["firm_strategy"] = (
        "Sobornar"
        if result["firm_prefers_bribe"]
        else "Honesto"
    )

    result["official_strategy"] = (
        "Aceptar"
        if result["official_prefers_accept"]
        else "Rechazar"
    )

    result["corruption"] = (
        "Sí"
        if result["corruption_sustainable"]
        else "No"
    )

    detection_results.append(result)


detection_df = pd.DataFrame(
    detection_results
)


detection_df.to_csv(
    "results/detection_sweep.csv",
    index=False
)


# ------------------------------------------------------------
# FIGURA EXPERIMENTO 2
# ------------------------------------------------------------

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    detection_df["p"],
    detection_df["firm_honest_payoff"],
    label="Empresa: competir honestamente"
)

plt.plot(
    detection_df["p"],
    detection_df["firm_bribe_payoff"],
    label="Empresa: sobornar"
)

plt.plot(
    detection_df["p"],
    detection_df["official_accept_payoff"],
    label="Funcionario: aceptar"
)

plt.axhline(
    0,
    linestyle="--"
)

plt.axvline(
    official_threshold,
    linestyle="--",
    label="Umbral funcionario"
)

plt.axvline(
    firm_threshold,
    linestyle="--",
    label="Umbral empresa"
)

plt.xlabel(
    "Probabilidad de detección"
)

plt.ylabel(
    "Payoff esperado"
)

plt.title(
    "Kairos Corruption Lab — "
    "Payoffs según probabilidad de detección"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/detection_payoffs.png",
    dpi=300
)

plt.close()


# ============================================================
# EXPERIMENTO 3A
# DETECCIÓN x SANCIÓN — FUNCIONARIO
# ============================================================

official_grid_results = []


detection_values = np.linspace(
    0,
    1,
    101
)

penalty_values = np.arange(
    0,
    501,
    5
)


for p in detection_values:

    for penalty in penalty_values:

        payoff = official_accept_payoff(
            BRIBE,
            p,
            penalty
        )

        prefers_accept = (
            payoff > 0
        )

        official_grid_results.append(
            {
                "p": p,
                "official_penalty": penalty,
                "official_accept_payoff": payoff,
                "official_prefers_accept": prefers_accept
            }
        )


official_grid_df = pd.DataFrame(
    official_grid_results
)


official_grid_df.to_csv(
    "results/official_penalty_grid.csv",
    index=False
)


# ------------------------------------------------------------
# MATRIZ PARA FIGURA DEL FUNCIONARIO
# ------------------------------------------------------------

official_matrix = (
    official_grid_df
    .pivot(
        index="official_penalty",
        columns="p",
        values="official_prefers_accept"
    )
    .astype(int)
)


plt.figure(
    figsize=(10, 7)
)

plt.imshow(
    official_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        detection_values.min(),
        detection_values.max(),
        penalty_values.min(),
        penalty_values.max()
    ]
)

# Frontera teórica F = B / p
p_boundary = np.linspace(
    0.04,
    1,
    500
)

official_boundary = (
    BRIBE / p_boundary
)

plt.plot(
    p_boundary,
    official_boundary,
    linestyle="--",
    label="Frontera teórica: F = B / p"
)

plt.xlabel(
    "Probabilidad de detección"
)

plt.ylabel(
    "Sanción al funcionario"
)

plt.title(
    "Funcionario — Región estratégica "
    "detección × sanción"
)

plt.ylim(
    0,
    500
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/official_detection_penalty_map.png",
    dpi=300
)

plt.close()


# ============================================================
# EXPERIMENTO 3B
# DETECCIÓN x SANCIÓN — EMPRESA
# ============================================================

firm_grid_results = []


for p in detection_values:

    for penalty in penalty_values:

        honest_payoff = firm_honest_payoff(
            PROFIT,
            HONEST_WIN_PROBABILITY
        )

        corrupt_payoff = firm_bribe_payoff(
            PROFIT,
            BRIBE,
            p,
            penalty,
            CORRUPT_WIN_PROBABILITY
        )

        prefers_bribe = (
            corrupt_payoff > honest_payoff
        )

        firm_grid_results.append(
            {
                "p": p,
                "firm_penalty": penalty,
                "firm_honest_payoff": honest_payoff,
                "firm_bribe_payoff": corrupt_payoff,
                "firm_prefers_bribe": prefers_bribe
            }
        )


firm_grid_df = pd.DataFrame(
    firm_grid_results
)


firm_grid_df.to_csv(
    "results/firm_penalty_grid.csv",
    index=False
)


firm_matrix = (
    firm_grid_df
    .pivot(
        index="firm_penalty",
        columns="p",
        values="firm_prefers_bribe"
    )
    .astype(int)
)


plt.figure(
    figsize=(10, 7)
)

plt.imshow(
    firm_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        detection_values.min(),
        detection_values.max(),
        penalty_values.min(),
        penalty_values.max()
    ]
)

# Frontera teórica de la empresa

corruption_advantage = (
    (
        CORRUPT_WIN_PROBABILITY
        - HONEST_WIN_PROBABILITY
    )
    * PROFIT
    - BRIBE
)

firm_boundary = (
    corruption_advantage
    / p_boundary
)

plt.plot(
    p_boundary,
    firm_boundary,
    linestyle="--",
    label="Frontera teórica empresa"
)

plt.xlabel(
    "Probabilidad de detección"
)

plt.ylabel(
    "Sanción a la empresa"
)

plt.title(
    "Empresa — Región estratégica "
    "detección × sanción"
)

plt.ylim(
    0,
    500
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/firm_detection_penalty_map.png",
    dpi=300
)

plt.close()


# ============================================================
# EXPERIMENTO 3C
# MAPA CONJUNTO DE REGÍMENES ESTRATÉGICOS
# ============================================================

# Para mantener el mapa en dos dimensiones,
# usamos aquí una sanción común:
#
# firm_penalty = official_penalty = F
#
# Los mapas anteriores permiten estudiar
# cada sanción por separado.

strategic_results = []


for p in detection_values:

    for penalty in penalty_values:

        result = solve_game(
            detection_probability=p,
            firm_penalty=penalty,
            official_penalty=penalty
        )

        if (
            result["firm_prefers_bribe"]
            and result["official_prefers_accept"]
        ):
            regime = 0
            regime_name = "Corrupción sostenible"

        elif (
            result["firm_prefers_bribe"]
            and not result["official_prefers_accept"]
        ):
            regime = 1
            regime_name = (
                "Empresa soborna / "
                "Funcionario rechaza"
            )

        else:
            regime = 2
            regime_name = "Estrategia honesta"

        strategic_results.append(
            {
                "p": p,
                "penalty": penalty,
                "regime": regime,
                "regime_name": regime_name
            }
        )


strategic_df = pd.DataFrame(
    strategic_results
)


strategic_df.to_csv(
    "results/strategic_regions.csv",
    index=False
)


strategic_matrix = (
    strategic_df
    .pivot(
        index="penalty",
        columns="p",
        values="regime"
    )
)


plt.figure(
    figsize=(10, 7)
)

plt.imshow(
    strategic_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        detection_values.min(),
        detection_values.max(),
        penalty_values.min(),
        penalty_values.max()
    ],
    vmin=0,
    vmax=2
)

# Frontera funcionario
plt.plot(
    p_boundary,
    official_boundary,
    linestyle="--",
    label="Umbral funcionario"
)

# Frontera empresa
plt.plot(
    p_boundary,
    firm_boundary,
    linestyle="--",
    label="Umbral empresa"
)

plt.xlabel(
    "Probabilidad de detección"
)

plt.ylabel(
    "Sanción común"
)

plt.title(
    "Kairos Corruption Lab — "
    "Regímenes estratégicos"
)

plt.ylim(
    0,
    500
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/strategic_regions.png",
    dpi=300
)

plt.close()


# ============================================================
# VALIDACIONES DEL EXPERIMENTO 3
# ============================================================

print("\n" + "=" * 65)
print("EXPERIMENTO 3 — DETECCIÓN × SANCIÓN")
print("=" * 65)


print("\nFUNCIONARIO")

for p in [
    0.05,
    0.10,
    0.20,
    0.40,
    0.50,
    1.00
]:

    threshold = official_penalty_threshold(
        BRIBE,
        p
    )

    print(
        f"p = {p:.0%} -> "
        f"sanción crítica = {threshold:.2f}"
    )


print("\nEMPRESA")

for p in [
    0.10,
    0.20,
    0.40,
    0.50,
    1.00
]:

    threshold = firm_penalty_threshold(
        PROFIT,
        BRIBE,
        p,
        HONEST_WIN_PROBABILITY,
        CORRUPT_WIN_PROBABILITY
    )

    print(
        f"p = {p:.0%} -> "
        f"sanción crítica = {threshold:.2f}"
    )


# ------------------------------------------------------------
# VALIDACIONES MATEMÁTICAS
# ------------------------------------------------------------

assert np.isclose(
    official_penalty_threshold(
        BRIBE,
        0.10
    ),
    200
)

assert np.isclose(
    official_penalty_threshold(
        BRIBE,
        0.20
    ),
    100
)

assert np.isclose(
    firm_penalty_threshold(
        PROFIT,
        BRIBE,
        0.10,
        HONEST_WIN_PROBABILITY,
        CORRUPT_WIN_PROBABILITY
    ),
    400
)

assert np.isclose(
    firm_penalty_threshold(
        PROFIT,
        BRIBE,
        0.40,
        HONEST_WIN_PROBABILITY,
        CORRUPT_WIN_PROBABILITY
    ),
    100
)


print(
    "\nUmbrales del Experimento 3 "
    "validados correctamente."
)


# ============================================================
# RESUMEN FINAL
# ============================================================

print("\n" + "=" * 65)
print("ARCHIVOS GENERADOS")
print("=" * 65)

print(
    "results/detection_sweep.csv"
)

print(
    "results/official_penalty_grid.csv"
)

print(
    "results/firm_penalty_grid.csv"
)

print(
    "results/strategic_regions.csv"
)

print()

print(
    "figures/detection_payoffs.png"
)

print(
    "figures/official_detection_penalty_map.png"
)

print(
    "figures/firm_detection_penalty_map.png"
)

print(
    "figures/strategic_regions.png"
)

print(
    "\nExperimentos 1, 2 y 3 "
    "completados correctamente."
)

print("=" * 65 + "\n")