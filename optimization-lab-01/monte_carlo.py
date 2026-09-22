import pandas as pd

from simulation import (
    generate_households,
    calculate_poverty,
    add_income_measurement_error
)

from policies import (
    universal_transfer,
    poorest_first_transfer,
    poverty_gap_transfer,
    deepest_poverty_first_transfer,
    poverty_gap_transfer_imperfect,
    poverty_gap_transfer_strategic
)

from game_theory import strategic_reporting




def evaluate_policy(
    baseline_households,
    allocation,
    poverty_line
):
    """
    Evalúa una política usando el ingreso real posterior
    a las transferencias.
    """

    evaluated = calculate_poverty(
        allocation,
        poverty_line,
        income_column="income_after"
    )

    poor_before = baseline_households["poor"].sum()
    poor_after = evaluated["poor"].sum()

    poverty_rate = poor_after / len(evaluated)

    lifted = poor_before - poor_after

    remaining_gap = evaluated["poverty_gap"].sum()

    return {
        "poverty_rate": poverty_rate,
        "lifted": lifted,
        "remaining_gap": remaining_gap
    }


def run_monte_carlo(
    simulations=50,
    n_households=100_000,
    poverty_line=2_000,
    budget=20_000_000,
    transfer_amount_b=1_000,
    measurement_sigma=500,
    audit_probability=0.10,
    penalty_multiplier=2.0,
    fixed_manipulation_cost=25,
    audit_cost_per_household=100
):

    results = []

    for seed in range(simulations):

        # ====================================================
        # 1. GENERAR POBLACIÓN
        # ====================================================

        households = generate_households(
            n=n_households,
            seed=seed
        )

        households = calculate_poverty(
            households,
            poverty_line
        )

        poor_before = households["poor"].sum()

        baseline_gap = households["poverty_gap"].sum()

        baseline_poverty_rate = (
            poor_before / len(households)
        )

        # ====================================================
        # 2. GOBIERNO A — UNIVERSAL
        # ====================================================

        gov_a = universal_transfer(
            households,
            budget
        )

        metrics_a = evaluate_policy(
            households,
            gov_a,
            poverty_line
        )

        # ====================================================
        # 3. GOBIERNO B — Q1,000 A LOS MÁS POBRES
        # ====================================================

        gov_b = poorest_first_transfer(
            households,
            budget,
            transfer_amount=transfer_amount_b
        )

        metrics_b = evaluate_policy(
            households,
            gov_b,
            poverty_line
        )

        # ====================================================
        # 4. GOBIERNO C — BRECHA EXACTA
        # ====================================================

        gov_c = poverty_gap_transfer(
            households,
            budget
        )

        metrics_c = evaluate_policy(
            households,
            gov_c,
            poverty_line
        )

        # ====================================================
        # 5. GOBIERNO D — POBREZA PROFUNDA PRIMERO
        # ====================================================

        gov_d = deepest_poverty_first_transfer(
            households,
            budget
        )

        metrics_d = evaluate_policy(
            households,
            gov_d,
            poverty_line
        )

        # ====================================================
        # 6. C CON INFORMACIÓN IMPERFECTA
        # ====================================================

        imperfect_households = add_income_measurement_error(
            households,
            poverty_line,
            sigma=measurement_sigma,
            seed=10_000 + seed
        )

        gov_c_imperfect = poverty_gap_transfer_imperfect(
            imperfect_households,
            budget
        )

        metrics_c_imperfect = evaluate_policy(
            households,
            gov_c_imperfect,
            poverty_line
        )

        # ====================================================
        # 7. COMPORTAMIENTO ESTRATÉGICO
        #    Escenario original:
        #    auditoría 10%, sanción 2x
        # ====================================================

        strategic_households = strategic_reporting(
            households,
            poverty_line=poverty_line,
            audit_probability=audit_probability,
            penalty_multiplier=penalty_multiplier,
            fixed_manipulation_cost=fixed_manipulation_cost
        )

        manipulation_rate = (
            strategic_households["strategic"].mean()
        )

        strategic_allocation = (
            poverty_gap_transfer_strategic(
                strategic_households,
                budget
            )
        )

        metrics_strategic = evaluate_policy(
            households,
            strategic_allocation,
            poverty_line
        )

        # ====================================================
        # 8. MECANISMO COMPATIBLE CON INCENTIVOS
        #
        #    Parte II-G:
        #    auditoría = 9.5%
        #    sanción = 10x
        # ====================================================

        compatible_audit_probability = 0.095
        compatible_penalty_multiplier = 10.0

        compatible_households = strategic_reporting(
            households,
            poverty_line=poverty_line,
            audit_probability=compatible_audit_probability,
            penalty_multiplier=compatible_penalty_multiplier,
            fixed_manipulation_cost=fixed_manipulation_cost
        )

        compatible_manipulation_rate = (
            compatible_households["strategic"].mean()
        )

        audit_cost = (
            n_households
            * compatible_audit_probability
            * audit_cost_per_household
        )

        compatible_transfer_budget = (
            budget - audit_cost
        )

        compatible_allocation = (
            poverty_gap_transfer_strategic(
                compatible_households,
                compatible_transfer_budget
            )
        )

        metrics_compatible = evaluate_policy(
            households,
            compatible_allocation,
            poverty_line
        )

        # ====================================================
        # 9. GUARDAR RESULTADOS
        # ====================================================

        results.append({

            "seed": seed,

            "baseline_poverty_rate":
                baseline_poverty_rate,

            "baseline_gap":
                baseline_gap,

            # Gobierno A
            "A_poverty":
                metrics_a["poverty_rate"],

            "A_lifted":
                metrics_a["lifted"],

            "A_gap":
                metrics_a["remaining_gap"],

            # Gobierno B
            "B_poverty":
                metrics_b["poverty_rate"],

            "B_lifted":
                metrics_b["lifted"],

            "B_gap":
                metrics_b["remaining_gap"],

            # Gobierno C
            "C_poverty":
                metrics_c["poverty_rate"],

            "C_lifted":
                metrics_c["lifted"],

            "C_gap":
                metrics_c["remaining_gap"],

            # Gobierno D
            "D_poverty":
                metrics_d["poverty_rate"],

            "D_lifted":
                metrics_d["lifted"],

            "D_gap":
                metrics_d["remaining_gap"],

            # C imperfecto
            "C_imp_poverty":
                metrics_c_imperfect["poverty_rate"],

            "C_imp_lifted":
                metrics_c_imperfect["lifted"],

            "C_imp_gap":
                metrics_c_imperfect["remaining_gap"],

            # Estratégico
            "strategic_manipulation":
                manipulation_rate,

            "strategic_poverty":
                metrics_strategic["poverty_rate"],

            "strategic_lifted":
                metrics_strategic["lifted"],

            "strategic_gap":
                metrics_strategic["remaining_gap"],

            # Incentive compatible
            "compatible_manipulation":
                compatible_manipulation_rate,

            "compatible_poverty":
                metrics_compatible["poverty_rate"],

            "compatible_lifted":
                metrics_compatible["lifted"],

            "compatible_gap":
                metrics_compatible["remaining_gap"]
        })

        print(
            f"Monte Carlo: "
            f"{seed + 1}/{simulations} completado"
        )

    return pd.DataFrame(results)


def summarize_monte_carlo(results):

    variables = {

        "Baseline pobreza":
            "baseline_poverty_rate",

        "Gobierno A pobreza":
            "A_poverty",

        "Gobierno B pobreza":
            "B_poverty",

        "Gobierno C pobreza":
            "C_poverty",

        "Gobierno D pobreza":
            "D_poverty",

        "C imperfecto pobreza":
            "C_imp_poverty",

        "Estratégico pobreza":
            "strategic_poverty",

        "Compatible pobreza":
            "compatible_poverty",

        "Manipulación estratégica":
            "strategic_manipulation",

        "Manipulación compatible":
            "compatible_manipulation"
    }

    summary_rows = []

    for label, column in variables.items():

        summary_rows.append({
            "Indicador": label,
            "Media": results[column].mean(),
            "Desv.Est.": results[column].std(),
            "Mínimo": results[column].min(),
            "Máximo": results[column].max()
        })

    return pd.DataFrame(summary_rows)