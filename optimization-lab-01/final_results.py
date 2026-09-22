# ============================================================
# KAIROS OPTIMIZATION LAB #1
# PARTE III-C — SÍNTESIS FINAL Y GRÁFICAS
# ============================================================

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from simulation import calculate_poverty
from policies import (
    universal_transfer,
    poorest_first_transfer,
    poverty_gap_transfer,
    deepest_poverty_first_transfer
)


def create_final_results(
    households,
    poverty_line,
    base_budget,
    monte_carlo_results
):

    # ========================================================
    # CARPETAS DE SALIDA
    # ========================================================

    figures_dir = Path("figures")
    results_dir = Path("results")

    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    poor_before = households["poor"].sum()

    # ========================================================
    # 1. RESULTADOS BASE A–D CON Q20M
    # ========================================================

    policies = {
        "A — Universal": universal_transfer(
            households,
            base_budget
        ),

        "B — Q1,000\nmás pobres": poorest_first_transfer(
            households,
            base_budget,
            transfer_amount=1_000
        ),

        "C — Brecha\nmínima primero": poverty_gap_transfer(
            households,
            base_budget
        ),

        "D — Pobreza\nprofunda primero": deepest_poverty_first_transfer(
            households,
            base_budget
        )
    }

    base_results = []

    for name, allocation in policies.items():

        evaluated = calculate_poverty(
            allocation,
            poverty_line,
            income_column="income_after"
        )

        poor_after = evaluated["poor"].sum()

        base_results.append({
            "policy": name,
            "poverty_rate": poor_after / len(households),
            "lifted": poor_before - poor_after,
            "remaining_gap": evaluated["poverty_gap"].sum(),
            "spent": allocation["transfer"].sum()
        })

    base_df = pd.DataFrame(base_results)

    base_df.to_csv(
        results_dir / "resultados_base.csv",
        index=False
    )

    # ========================================================
    # GRÁFICA 1 — POBREZA FINAL A–D
    # ========================================================

    plt.figure(figsize=(9, 6))

    bars = plt.bar(
        base_df["policy"],
        base_df["poverty_rate"] * 100
    )

    plt.ylabel("Pobreza final (%)")
    plt.title(
        "Kairos Optimization Lab #1\n"
        "Pobreza final por estrategia — presupuesto Q20 millones"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    for bar, value in zip(
        bars,
        base_df["poverty_rate"] * 100
    ):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.35,
            f"{value:.2f}%",
            ha="center"
        )

    plt.tight_layout()

    plt.savefig(
        figures_dir / "01_pobreza_final_gobiernos.png",
        dpi=300
    )

    plt.close()

    # ========================================================
    # 2. SENSIBILIDAD AL PRESUPUESTO
    # ========================================================

    budget_values = [
        10_000_000,
        15_000_000,
        20_000_000,
        25_000_000,
        30_000_000
    ]

    budget_results = []

    for budget in budget_values:

        allocations = {

            "A": universal_transfer(
                households,
                budget
            ),

            "B": poorest_first_transfer(
                households,
                budget,
                transfer_amount=1_000
            ),

            "C": poverty_gap_transfer(
                households,
                budget
            ),

            "D": deepest_poverty_first_transfer(
                households,
                budget
            )
        }

        for government, allocation in allocations.items():

            evaluated = calculate_poverty(
                allocation,
                poverty_line,
                income_column="income_after"
            )

            poor_after = evaluated["poor"].sum()

            budget_results.append({
                "budget": budget,
                "government": government,
                "poverty_rate": poor_after / len(households),
                "lifted": poor_before - poor_after,
                "remaining_gap": evaluated["poverty_gap"].sum(),
                "spent": allocation["transfer"].sum()
            })

    budget_df = pd.DataFrame(budget_results)

    budget_df.to_csv(
        results_dir / "sensibilidad_presupuesto.csv",
        index=False
    )

    # ========================================================
    # GRÁFICA 2 — PRESUPUESTO VS POBREZA
    # ========================================================

    plt.figure(figsize=(9, 6))

    for government in ["A", "B", "C", "D"]:

        data = budget_df[
            budget_df["government"] == government
        ]

        plt.plot(
            data["budget"] / 1_000_000,
            data["poverty_rate"] * 100,
            marker="o",
            label=f"Gobierno {government}"
        )

    plt.xlabel("Presupuesto de transferencias (Q millones)")
    plt.ylabel("Pobreza final (%)")

    plt.title(
        "Sensibilidad de la pobreza al presupuesto"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    plt.savefig(
        figures_dir / "02_sensibilidad_presupuesto.png",
        dpi=300
    )

    plt.close()

    # ========================================================
    # 3. MONTE CARLO
    # ========================================================

    mc_scenarios = {
        "A": "A_poverty",
        "B": "B_poverty",
        "C": "C_poverty",
        "D": "D_poverty",
        "C imperfecto": "C_imp_poverty",
        "Estratégico": "strategic_poverty",
        "Compatible": "compatible_poverty"
    }

    mc_summary = []

    for name, column in mc_scenarios.items():

        mc_summary.append({
            "scenario": name,
            "mean": monte_carlo_results[column].mean(),
            "std": monte_carlo_results[column].std(),
            "minimum": monte_carlo_results[column].min(),
            "maximum": monte_carlo_results[column].max()
        })

    mc_df = pd.DataFrame(mc_summary)

    mc_df.to_csv(
        results_dir / "resumen_monte_carlo.csv",
        index=False
    )

    # ========================================================
    # GRÁFICA 3 — MONTE CARLO
    # ========================================================

    plt.figure(figsize=(10, 6))

    means = mc_df["mean"] * 100

    lower_errors = (
        mc_df["mean"] - mc_df["minimum"]
    ) * 100

    upper_errors = (
        mc_df["maximum"] - mc_df["mean"]
    ) * 100

    plt.errorbar(
        mc_df["scenario"],
        means,
        yerr=[
            lower_errors,
            upper_errors
        ],
        fmt="o",
        capsize=5
    )

    plt.ylabel("Pobreza final (%)")

    plt.title(
        "Robustez en 50 poblaciones sintéticas\n"
        "Media y rango mínimo–máximo"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        figures_dir / "03_monte_carlo_robustez.png",
        dpi=300
    )

    plt.close()

    # ========================================================
    # 4. DESTRUYENDO LAS SUPERPOTENCIAS DEL GOBIERNO C
    # ========================================================

    deterioration_labels = [
        "C perfecto",
        "Información\nimperfecta",
        "Conducta\nestratégica",
        "Mecanismo\ncompatible"
    ]

    deterioration_values = [
        monte_carlo_results["C_poverty"].mean() * 100,
        monte_carlo_results["C_imp_poverty"].mean() * 100,
        monte_carlo_results["strategic_poverty"].mean() * 100,
        monte_carlo_results["compatible_poverty"].mean() * 100
    ]

    plt.figure(figsize=(9, 6))

    bars = plt.bar(
        deterioration_labels,
        deterioration_values
    )

    plt.ylabel("Pobreza final media (%)")

    plt.title(
        "Del gobierno omnisciente al diseño de incentivos\n"
        "Promedio de 50 simulaciones"
    )

    plt.grid(
        axis="y",
        alpha=0.25
    )

    for bar, value in zip(
        bars,
        deterioration_values
    ):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.25,
            f"{value:.2f}%",
            ha="center"
        )

    plt.tight_layout()

    plt.savefig(
        figures_dir /
        "04_informacion_incentivos.png",
        dpi=300
    )

    plt.close()

    # ========================================================
    # 5. RESUMEN FINAL
    # ========================================================

    print("\nPARTE III-C — SÍNTESIS FINAL")
    print("=" * 75)

    print(
        f"Pobreza inicial: "
        f"{households['poor'].mean():.2%}"
    )

    print(
        f"Brecha inicial: "
        f"Q{households['poverty_gap'].sum():,.2f}"
    )

    print("\nRESULTADOS BASE — Q20M")

    for _, row in base_df.iterrows():

        print(
            f"{row['policy']:<28} | "
            f"Pobreza: {row['poverty_rate']:>6.2%} | "
            f"Salen: {row['lifted']:>6,.0f} | "
            f"Brecha: Q{row['remaining_gap']:>12,.2f}"
        )

    print("\nMONTE CARLO — RESULTADOS CENTRALES")

    print(
        f"C perfecto: "
        f"{monte_carlo_results['C_poverty'].mean():.2%}"
    )

    print(
        f"C imperfecto: "
        f"{monte_carlo_results['C_imp_poverty'].mean():.2%}"
    )

    print(
        f"Estratégico: "
        f"{monte_carlo_results['strategic_poverty'].mean():.2%}"
    )

    print(
        f"Mecanismo compatible: "
        f"{monte_carlo_results['compatible_poverty'].mean():.2%}"
    )

    print(
        f"Manipulación compatible: "
        f"{monte_carlo_results['compatible_manipulation'].mean():.2%}"
    )

    print("\nARCHIVOS GENERADOS")

    print(
        "figures/01_pobreza_final_gobiernos.png"
    )

    print(
        "figures/02_sensibilidad_presupuesto.png"
    )

    print(
        "figures/03_monte_carlo_robustez.png"
    )

    print(
        "figures/04_informacion_incentivos.png"
    )

    print(
        "results/resultados_base.csv"
    )

    print(
        "results/sensibilidad_presupuesto.csv"
    )

    print(
        "results/resumen_monte_carlo.csv"
    )

    print("\n" + "=" * 75)

    print(
        "KAIROS OPTIMIZATION LAB #1 — "
        "EXPERIMENTO COMPLETADO"
    )

    print("=" * 75)