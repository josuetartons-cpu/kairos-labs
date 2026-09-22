from simulation import (
    generate_households,
    calculate_poverty,
    calculate_fgt,
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

from monte_carlo import (
    run_monte_carlo,
    summarize_monte_carlo
)
from final_results import create_final_results

# ============================================================
# KAIROS OPTIMIZATION LAB #1
# ============================================================


# ------------------------------------------------------------
# 1. PARÁMETROS
# ------------------------------------------------------------

N_HOUSEHOLDS = 100_000
POVERTY_LINE = 2_000
BUDGET = 20_000_000
SEED = 42

TRANSFER_B = 1_000

SIGMA_ERROR = 500
ERROR_SEED = 123


# ------------------------------------------------------------
# 2. GENERAR POBLACIÓN
# ------------------------------------------------------------

households = generate_households(
    n=N_HOUSEHOLDS,
    seed=SEED
)

households = calculate_poverty(
    households,
    poverty_line=POVERTY_LINE,
    income_column="income"
)


# ------------------------------------------------------------
# 3. SITUACIÓN INICIAL
# ------------------------------------------------------------

poor_before = households["poor"].sum()

poverty_rate_before = (
    households["poor"].mean()
)

poverty_gap_before = (
    households["poverty_gap"].sum()
)


print("\nKAIROS OPTIMIZATION LAB #1")
print("=" * 60)

print("\nSITUACIÓN INICIAL")
print("-" * 60)

print(
    f"Hogares simulados: "
    f"{N_HOUSEHOLDS:,}"
)

print(
    f"Línea de pobreza: "
    f"Q{POVERTY_LINE:,.2f}"
)

print(
    f"Hogares pobres: "
    f"{poor_before:,}"
)

print(
    f"Tasa de pobreza: "
    f"{poverty_rate_before:.2%}"
)

print(
    f"Brecha total de pobreza: "
    f"Q{poverty_gap_before:,.2f}"
)


# ============================================================
# GOBIERNO A — TRANSFERENCIA UNIVERSAL
# ============================================================

government_a = universal_transfer(
    households,
    budget=BUDGET
)

government_a = calculate_poverty(
    government_a,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


poor_a = (
    government_a["poor"].sum()
)

poverty_rate_a = (
    government_a["poor"].mean()
)

poverty_gap_a = (
    government_a["poverty_gap"].sum()
)

lifted_a = (
    poor_before - poor_a
)

gap_reduction_a = (
    poverty_gap_before
    - poverty_gap_a
)

cost_per_lifted_a = (
    BUDGET / lifted_a
    if lifted_a > 0
    else 0
)


print("\nGOBIERNO A — TRANSFERENCIA UNIVERSAL")
print("-" * 60)

print(
    f"Presupuesto: "
    f"Q{BUDGET:,.2f}"
)

print(
    f"Transferencia por hogar: "
    f"Q{government_a['transfer'].iloc[0]:,.2f}"
)

print(
    f"Hogares pobres después: "
    f"{poor_a:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_a:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_a:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_a:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_a:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_a:,.2f}"
)


# ============================================================
# GOBIERNO B — LOS MÁS POBRES PRIMERO
# ============================================================

government_b = poorest_first_transfer(
    households,
    budget=BUDGET,
    transfer_amount=TRANSFER_B
)

government_b = calculate_poverty(
    government_b,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


poor_b = (
    government_b["poor"].sum()
)

poverty_rate_b = (
    government_b["poor"].mean()
)

poverty_gap_b = (
    government_b["poverty_gap"].sum()
)

lifted_b = (
    poor_before - poor_b
)

gap_reduction_b = (
    poverty_gap_before
    - poverty_gap_b
)

beneficiaries_b = (
    government_b["transfer"] > 0
).sum()

spent_b = (
    government_b["transfer"].sum()
)

cost_per_lifted_b = (
    spent_b / lifted_b
    if lifted_b > 0
    else 0
)


print("\nGOBIERNO B — LOS MÁS POBRES PRIMERO")
print("-" * 60)

print(
    f"Presupuesto disponible: "
    f"Q{BUDGET:,.2f}"
)

print(
    f"Transferencia por beneficiario: "
    f"Q{TRANSFER_B:,.2f}"
)

print(
    f"Hogares beneficiados: "
    f"{beneficiaries_b:,}"
)

print(
    f"Presupuesto utilizado: "
    f"Q{spent_b:,.2f}"
)

print(
    f"Hogares pobres después: "
    f"{poor_b:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_b:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_b:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_b:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_b:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_b:,.2f}"
)


# ============================================================
# GOBIERNO C — CIERRE EXACTO DE BRECHA
# ============================================================

government_c = poverty_gap_transfer(
    households,
    budget=BUDGET
)

government_c = calculate_poverty(
    government_c,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


poor_c = (
    government_c["poor"].sum()
)

poverty_rate_c = (
    government_c["poor"].mean()
)

poverty_gap_c = (
    government_c["poverty_gap"].sum()
)

lifted_c = (
    poor_before - poor_c
)

gap_reduction_c = (
    poverty_gap_before
    - poverty_gap_c
)

beneficiaries_c = (
    government_c["transfer"] > 0
).sum()

spent_c = (
    government_c["transfer"].sum()
)

cost_per_lifted_c = (
    spent_c / lifted_c
    if lifted_c > 0
    else 0
)


print("\nGOBIERNO C — CIERRE EXACTO DE BRECHA")
print("-" * 60)

print(
    f"Presupuesto disponible: "
    f"Q{BUDGET:,.2f}"
)

print(
    f"Hogares beneficiados: "
    f"{beneficiaries_c:,}"
)

print(
    f"Presupuesto utilizado: "
    f"Q{spent_c:,.2f}"
)

print(
    f"Hogares pobres después: "
    f"{poor_c:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_c:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_c:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_c:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_c:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_c:,.2f}"
)


# ============================================================
# GOBIERNO D — POBREZA MÁS PROFUNDA PRIMERO
# ============================================================

government_d = deepest_poverty_first_transfer(
    households,
    budget=BUDGET
)

government_d = calculate_poverty(
    government_d,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


poor_d = (
    government_d["poor"].sum()
)

poverty_rate_d = (
    government_d["poor"].mean()
)

poverty_gap_d = (
    government_d["poverty_gap"].sum()
)

lifted_d = (
    poor_before - poor_d
)

gap_reduction_d = (
    poverty_gap_before
    - poverty_gap_d
)

beneficiaries_d = (
    government_d["transfer"] > 0
).sum()

spent_d = (
    government_d["transfer"].sum()
)

cost_per_lifted_d = (
    spent_d / lifted_d
    if lifted_d > 0
    else 0
)


print("\nGOBIERNO D — POBREZA MÁS PROFUNDA PRIMERO")
print("-" * 60)

print(
    f"Presupuesto disponible: "
    f"Q{BUDGET:,.2f}"
)

print(
    f"Hogares beneficiados: "
    f"{beneficiaries_d:,}"
)

print(
    f"Presupuesto utilizado: "
    f"Q{spent_d:,.2f}"
)

print(
    f"Hogares pobres después: "
    f"{poor_d:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_d:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_d:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_d:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_d:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_d:,.2f}"
)


# ============================================================
# COMPARACIÓN A vs B vs C vs D
# ============================================================

print("\nCOMPARACIÓN A vs B vs C vs D")
print("=" * 60)

print(
    f"A — hogares fuera de pobreza: "
    f"{lifted_a:,}"
)

print(
    f"B — hogares fuera de pobreza: "
    f"{lifted_b:,}"
)

print(
    f"C — hogares fuera de pobreza: "
    f"{lifted_c:,}"
)

print(
    f"D — hogares fuera de pobreza: "
    f"{lifted_d:,}"
)

print()

print(
    f"A — brecha restante: "
    f"Q{poverty_gap_a:,.2f}"
)

print(
    f"B — brecha restante: "
    f"Q{poverty_gap_b:,.2f}"
)

print(
    f"C — brecha restante: "
    f"Q{poverty_gap_c:,.2f}"
)

print(
    f"D — brecha restante: "
    f"Q{poverty_gap_d:,.2f}"
)

print()

print(
    f"A — costo por hogar rescatado: "
    f"Q{cost_per_lifted_a:,.2f}"
)

print(
    f"B — costo por hogar rescatado: "
    f"Q{cost_per_lifted_b:,.2f}"
)

print(
    f"C — costo por hogar rescatado: "
    f"Q{cost_per_lifted_c:,.2f}"
)

print(
    f"D — costo por hogar rescatado: "
    f"Q{cost_per_lifted_d:,.2f}"
)


# ============================================================
# MEDIDAS FGT
# ============================================================

fgt_before = calculate_fgt(
    households,
    poverty_line=POVERTY_LINE,
    income_column="income"
)

fgt_a = calculate_fgt(
    government_a,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)

fgt_b = calculate_fgt(
    government_b,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)

fgt_c = calculate_fgt(
    government_c,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)

fgt_d = calculate_fgt(
    government_d,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


print("\nFGT — MEDIDAS DE POBREZA")
print("=" * 60)

print(
    f"Baseline | "
    f"FGT0: {fgt_before['FGT0']:.4f} | "
    f"FGT1: {fgt_before['FGT1']:.4f} | "
    f"FGT2: {fgt_before['FGT2']:.4f}"
)

print(
    f"A        | "
    f"FGT0: {fgt_a['FGT0']:.4f} | "
    f"FGT1: {fgt_a['FGT1']:.4f} | "
    f"FGT2: {fgt_a['FGT2']:.4f}"
)

print(
    f"B        | "
    f"FGT0: {fgt_b['FGT0']:.4f} | "
    f"FGT1: {fgt_b['FGT1']:.4f} | "
    f"FGT2: {fgt_b['FGT2']:.4f}"
)

print(
    f"C        | "
    f"FGT0: {fgt_c['FGT0']:.4f} | "
    f"FGT1: {fgt_c['FGT1']:.4f} | "
    f"FGT2: {fgt_c['FGT2']:.4f}"
)

print(
    f"D        | "
    f"FGT0: {fgt_d['FGT0']:.4f} | "
    f"FGT1: {fgt_d['FGT1']:.4f} | "
    f"FGT2: {fgt_d['FGT2']:.4f}"
)


# ============================================================
# GOBIERNO C — INFORMACIÓN IMPERFECTA
# ============================================================

households_imperfect = add_income_measurement_error(
    households,
    poverty_line=POVERTY_LINE,
    sigma=SIGMA_ERROR,
    seed=ERROR_SEED
)


government_c_imperfect = poverty_gap_transfer_imperfect(
    households_imperfect,
    budget=BUDGET
)


government_c_imperfect = calculate_poverty(
    government_c_imperfect,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


poor_c_imperfect = (
    government_c_imperfect["poor"].sum()
)

poverty_rate_c_imperfect = (
    government_c_imperfect["poor"].mean()
)

poverty_gap_c_imperfect = (
    government_c_imperfect["poverty_gap"].sum()
)

lifted_c_imperfect = (
    poor_before
    - poor_c_imperfect
)

beneficiaries_c_imperfect = (
    government_c_imperfect["transfer"] > 0
).sum()

spent_c_imperfect = (
    government_c_imperfect["transfer"].sum()
)

gap_reduction_c_imperfect = (
    poverty_gap_before
    - poverty_gap_c_imperfect
)

cost_per_lifted_c_imperfect = (
    spent_c_imperfect
    / lifted_c_imperfect
    if lifted_c_imperfect > 0
    else 0
)


# ============================================================
# ERRORES DE CLASIFICACIÓN
# ============================================================

false_positive = (
    (~households_imperfect["poor"])
    &
    households_imperfect["poor_observed"]
).sum()

false_negative = (
    households_imperfect["poor"]
    &
    (~households_imperfect["poor_observed"])
).sum()


# ============================================================
# FILTRACIÓN DEL PROGRAMA
# ============================================================

received_transfer = (
    government_c_imperfect["transfer"] > 0
)

nonpoor_beneficiaries = (
    received_transfer
    &
    (~households_imperfect["poor"])
).sum()

poor_beneficiaries = (
    received_transfer
    &
    households_imperfect["poor"]
).sum()

leakage_rate = (
    nonpoor_beneficiaries
    / beneficiaries_c_imperfect
    if beneficiaries_c_imperfect > 0
    else 0
)


# ============================================================
# RESULTADOS — INFORMACIÓN IMPERFECTA
# ============================================================

print("\nGOBIERNO C — INFORMACIÓN IMPERFECTA")
print("=" * 60)

print(
    f"Error estándar del ingreso: "
    f"Q{SIGMA_ERROR:,.2f}"
)

print(
    f"Hogares verdaderamente pobres: "
    f"{poor_before:,}"
)

print()

print(
    f"Falsos positivos: "
    f"{false_positive:,}"
)

print(
    f"Falsos negativos: "
    f"{false_negative:,}"
)

print()

print(
    f"Hogares beneficiados: "
    f"{beneficiaries_c_imperfect:,}"
)

print(
    f"Beneficiarios verdaderamente pobres: "
    f"{poor_beneficiaries:,}"
)

print(
    f"Beneficiarios que no eran pobres: "
    f"{nonpoor_beneficiaries:,}"
)

print(
    f"Tasa de filtración: "
    f"{leakage_rate:.2%}"
)

print()

print(
    f"Presupuesto utilizado: "
    f"Q{spent_c_imperfect:,.2f}"
)

print(
    f"Hogares pobres después: "
    f"{poor_c_imperfect:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_c_imperfect:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_c_imperfect:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_c_imperfect:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_c_imperfect:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_c_imperfect:,.2f}"
)


# ============================================================
# COMPARACIÓN C PERFECTO vs C IMPERFECTO
# ============================================================

print("\nC PERFECTO vs C CON INFORMACIÓN IMPERFECTA")
print("=" * 60)

print(
    f"C perfecto — pobreza final: "
    f"{poverty_rate_c:.2%}"
)

print(
    f"C imperfecto — pobreza final: "
    f"{poverty_rate_c_imperfect:.2%}"
)

print()

print(
    f"C perfecto — hogares fuera de pobreza: "
    f"{lifted_c:,}"
)

print(
    f"C imperfecto — hogares fuera de pobreza: "
    f"{lifted_c_imperfect:,}"
)

print()

print(
    f"C perfecto — brecha restante: "
    f"Q{poverty_gap_c:,.2f}"
)

print(
    f"C imperfecto — brecha restante: "
    f"Q{poverty_gap_c_imperfect:,.2f}"
)
# ============================================================
# ANÁLISIS DE SENSIBILIDAD
# CALIDAD DE INFORMACIÓN
# ============================================================

sigma_values = [
    0,
    100,
    250,
    500,
    750,
    1_000
]


print("\nSENSIBILIDAD — CALIDAD DE INFORMACIÓN")
print("=" * 100)

print(
    f"{'Sigma':>8} | "
    f"{'F. Pos.':>8} | "
    f"{'F. Neg.':>8} | "
    f"{'Filtración':>10} | "
    f"{'Pobreza final':>13} | "
    f"{'Salen pobreza':>13} | "
    f"{'Brecha final':>15}"
)

print("-" * 100)


for sigma in sigma_values:

    # --------------------------------------------------------
    # Crear información imperfecta
    # --------------------------------------------------------

    households_test = add_income_measurement_error(
        households,
        poverty_line=POVERTY_LINE,
        sigma=sigma,
        seed=ERROR_SEED
    )


    # --------------------------------------------------------
    # Aplicar Gobierno C
    # --------------------------------------------------------

    government_test = poverty_gap_transfer_imperfect(
        households_test,
        budget=BUDGET
    )


    government_test = calculate_poverty(
        government_test,
        poverty_line=POVERTY_LINE,
        income_column="income_after"
    )


    # --------------------------------------------------------
    # Resultados reales
    # --------------------------------------------------------

    poor_test = (
        government_test["poor"].sum()
    )

    poverty_rate_test = (
        government_test["poor"].mean()
    )

    lifted_test = (
        poor_before - poor_test
    )

    poverty_gap_test = (
        government_test["poverty_gap"].sum()
    )


    # --------------------------------------------------------
    # Errores de clasificación
    # --------------------------------------------------------

    false_positive_test = (
        (~households_test["poor"])
        &
        households_test["poor_observed"]
    ).sum()

    false_negative_test = (
        households_test["poor"]
        &
        (~households_test["poor_observed"])
    ).sum()


    # --------------------------------------------------------
    # Filtración
    # --------------------------------------------------------

    received_test = (
        government_test["transfer"] > 0
    )

    beneficiaries_test = (
        received_test.sum()
    )

    nonpoor_beneficiaries_test = (
        received_test
        &
        (~households_test["poor"])
    ).sum()

    leakage_test = (
        nonpoor_beneficiaries_test
        / beneficiaries_test
        if beneficiaries_test > 0
        else 0
    )


    # --------------------------------------------------------
    # Imprimir fila
    # --------------------------------------------------------

    print(
        f"Q{sigma:>7,.0f} | "
        f"{false_positive_test:>8,} | "
        f"{false_negative_test:>8,} | "
        f"{leakage_test:>9.2%} | "
        f"{poverty_rate_test:>12.2%} | "
        f"{lifted_test:>13,} | "
        f"Q{poverty_gap_test:>14,.2f}"
    )

    # ============================================================
# PARTE II — COMPORTAMIENTO ESTRATÉGICO
# ============================================================

strategic_households = strategic_reporting(
    households,
    poverty_line=POVERTY_LINE,
    audit_probability=0.10,
    penalty_multiplier=2.0,
    fixed_manipulation_cost=25
)


# ============================================================
# DECISIONES DE LOS HOGARES
# ============================================================

truthful_households = (
    strategic_households["manipulation"] == 0
).sum()

manipulation_250 = (
    strategic_households["manipulation"] == 250
).sum()

manipulation_500 = (
    strategic_households["manipulation"] == 500
).sum()

strategic_total = (
    strategic_households["strategic"].sum()
)

strategic_rate = (
    strategic_total / len(strategic_households)
)


# ============================================================
# HOGARES QUE CAMBIAN SU CLASIFICACIÓN
# ============================================================

true_nonpoor = (
    strategic_households["income"]
    >= POVERTY_LINE
)

reported_poor = (
    strategic_households["poor_reported"]
)

nonpoor_appear_poor = (
    true_nonpoor
    &
    reported_poor
).sum()


# ============================================================
# POBRES QUE MANIPULAN
# ============================================================

true_poor = (
    strategic_households["income"]
    < POVERTY_LINE
)

poor_manipulators = (
    true_poor
    &
    strategic_households["strategic"]
).sum()


# ============================================================
# NO POBRES QUE MANIPULAN
# ============================================================

nonpoor_manipulators = (
    true_nonpoor
    &
    strategic_households["strategic"]
).sum()


# ============================================================
# RESULTADOS
# ============================================================

print("\nPARTE II — COMPORTAMIENTO ESTRATÉGICO")
print("=" * 70)

print(
    f"Probabilidad de auditoría: "
    f"{0.10:.0%}"
)

print(
    f"Multiplicador de penalización: "
    f"{2.0:.1f}x"
)

print(
    f"Costo fijo de manipulación: "
    f"Q{25:,.2f}"
)

print()

print(
    f"Hogares que dicen la verdad: "
    f"{truthful_households:,}"
)

print(
    f"Hogares que ocultan Q250: "
    f"{manipulation_250:,}"
)

print(
    f"Hogares que ocultan Q500: "
    f"{manipulation_500:,}"
)

print()

print(
    f"Total de hogares que manipulan: "
    f"{strategic_total:,}"
)

print(
    f"Tasa de comportamiento estratégico: "
    f"{strategic_rate:.2%}"
)

print()

print(
    f"Hogares pobres que manipulan: "
    f"{poor_manipulators:,}"
)

print(
    f"Hogares no pobres que manipulan: "
    f"{nonpoor_manipulators:,}"
)

print()

print(
    f"Hogares no pobres que logran "
    f"parecer pobres: "
    f"{nonpoor_appear_poor:,}"
)

# ============================================================
# PARTE II-B — GOBIERNO BAJO REPORTES ESTRATÉGICOS
# ============================================================

government_strategic = poverty_gap_transfer_strategic(
    strategic_households,
    budget=BUDGET
)

government_strategic = calculate_poverty(
    government_strategic,
    poverty_line=POVERTY_LINE,
    income_column="income_after"
)


# ============================================================
# RESULTADOS DE POBREZA
# ============================================================

poor_strategic_after = (
    government_strategic["poor"].sum()
)

poverty_rate_strategic_after = (
    government_strategic["poor"].mean()
)

poverty_gap_strategic_after = (
    government_strategic["poverty_gap"].sum()
)

lifted_strategic = (
    poor_before
    - poor_strategic_after
)

gap_reduction_strategic = (
    poverty_gap_before
    - poverty_gap_strategic_after
)


# ============================================================
# USO DEL PRESUPUESTO
# ============================================================

strategic_beneficiaries = (
    government_strategic["transfer"] > 0
).sum()

spent_strategic = (
    government_strategic["transfer"].sum()
)

cost_per_lifted_strategic = (
    spent_strategic
    / lifted_strategic
    if lifted_strategic > 0
    else 0
)


# ============================================================
# FILTRACIÓN POR MANIPULACIÓN
# ============================================================

received_strategic = (
    government_strategic["transfer"] > 0
)

true_poor_baseline = (
    strategic_households["income"]
    < POVERTY_LINE
)

true_nonpoor_baseline = (
    strategic_households["income"]
    >= POVERTY_LINE
)

poor_beneficiaries_strategic = (
    received_strategic
    &
    true_poor_baseline
).sum()

nonpoor_beneficiaries_strategic = (
    received_strategic
    &
    true_nonpoor_baseline
).sum()

leakage_rate_strategic = (
    nonpoor_beneficiaries_strategic
    / strategic_beneficiaries
    if strategic_beneficiaries > 0
    else 0
)


# ============================================================
# DINERO QUE TERMINA EN HOGARES NO POBRES
# ============================================================

money_to_nonpoor = (
    government_strategic.loc[
        true_nonpoor_baseline,
        "transfer"
    ].sum()
)

money_to_poor = (
    government_strategic.loc[
        true_poor_baseline,
        "transfer"
    ].sum()
)

budget_leakage_rate = (
    money_to_nonpoor
    / spent_strategic
    if spent_strategic > 0
    else 0
)


# ============================================================
# RESULTADOS
# ============================================================

print("\nPARTE II-B — GOBIERNO BAJO REPORTES ESTRATÉGICOS")
print("=" * 75)

print(
    f"Hogares beneficiados: "
    f"{strategic_beneficiaries:,}"
)

print(
    f"Presupuesto utilizado: "
    f"Q{spent_strategic:,.2f}"
)

print()

print(
    f"Beneficiarios verdaderamente pobres: "
    f"{poor_beneficiaries_strategic:,}"
)

print(
    f"Beneficiarios verdaderamente no pobres: "
    f"{nonpoor_beneficiaries_strategic:,}"
)

print(
    f"Tasa de filtración por beneficiarios: "
    f"{leakage_rate_strategic:.2%}"
)

print()

print(
    f"Dinero recibido por hogares pobres: "
    f"Q{money_to_poor:,.2f}"
)

print(
    f"Dinero recibido por hogares no pobres: "
    f"Q{money_to_nonpoor:,.2f}"
)

print(
    f"Filtración presupuestaria: "
    f"{budget_leakage_rate:.2%}"
)

print()

print(
    f"Hogares pobres después: "
    f"{poor_strategic_after:,}"
)

print(
    f"Tasa de pobreza después: "
    f"{poverty_rate_strategic_after:.2%}"
)

print(
    f"Hogares que salieron de pobreza: "
    f"{lifted_strategic:,}"
)

print(
    f"Brecha restante: "
    f"Q{poverty_gap_strategic_after:,.2f}"
)

print(
    f"Reducción de brecha: "
    f"Q{gap_reduction_strategic:,.2f}"
)

print(
    f"Costo por hogar que salió de pobreza: "
    f"Q{cost_per_lifted_strategic:,.2f}"
)

# ============================================================
# PARTE II-C — SENSIBILIDAD A LA PROBABILIDAD DE AUDITORÍA
# ============================================================

audit_probabilities = [
    0.00,
    0.05,
    0.10,
    0.20,
    0.30,
    0.40,
    0.45,
    0.47,
    0.475,
    0.48,
    0.50,
    0.75,
    1.00
]


print("\nPARTE II-C — SENSIBILIDAD A LA AUDITORÍA")
print("=" * 85)

print(
    f"{'Auditoría':>10} | "
    f"{'Manipulan':>10} | "
    f"{'Tasa':>9} | "
    f"{'Ocultan Q250':>13} | "
    f"{'Ocultan Q500':>13}"
)

print("-" * 85)


for audit_probability in audit_probabilities:

    test_households = strategic_reporting(
        households,
        poverty_line=POVERTY_LINE,
        audit_probability=audit_probability,
        penalty_multiplier=2.0,
        fixed_manipulation_cost=25
    )

    manipulators = (
        test_households["strategic"].sum()
    )

    manipulation_rate = (
        manipulators / len(test_households)
    )

    hide_250 = (
        test_households["manipulation"] == 250
    ).sum()

    hide_500 = (
        test_households["manipulation"] == 500
    ).sum()

    print(
        f"{audit_probability:>9.1%} | "
        f"{manipulators:>10,} | "
        f"{manipulation_rate:>8.2%} | "
        f"{hide_250:>13,} | "
        f"{hide_500:>13,}"
    )
# ============================================================
# PARTE II-D — MATRIZ AUDITORÍA × SANCIÓN
# ============================================================

audit_grid = [
    0.05,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50
]

penalty_grid = [
    1.0,
    2.0,
    3.0,
    5.0,
    10.0
]


print("\nPARTE II-D — MATRIZ AUDITORÍA × SANCIÓN")
print("=" * 95)

print(
    f"{'Auditoría':>10} | "
    f"{'Sanción':>8} | "
    f"{'Manipulan':>10} | "
    f"{'Tasa':>9} | "
    f"{'Ocultan Q250':>13} | "
    f"{'Ocultan Q500':>13}"
)

print("-" * 95)


for audit_probability in audit_grid:

    for penalty_multiplier in penalty_grid:

        test_households = strategic_reporting(
            households,
            poverty_line=POVERTY_LINE,
            audit_probability=audit_probability,
            penalty_multiplier=penalty_multiplier,
            fixed_manipulation_cost=25
        )

        manipulators = (
            test_households["strategic"].sum()
        )

        manipulation_rate = (
            manipulators / len(test_households)
        )

        hide_250 = (
            test_households["manipulation"] == 250
        ).sum()

        hide_500 = (
            test_households["manipulation"] == 500
        ).sum()

        print(
            f"{audit_probability:>9.0%} | "
            f"{penalty_multiplier:>7.1f}x | "
            f"{manipulators:>10,} | "
            f"{manipulation_rate:>8.2%} | "
            f"{hide_250:>13,} | "
            f"{hide_500:>13,}"
        )

# ============================================================
# PARTE II-E — COSTO ADMINISTRATIVO DE AUDITORÍA
# ============================================================

AUDIT_COST_PER_HOUSEHOLD = 100

audit_grid_cost = [
    0.05,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50
]

penalty_grid_cost = [
    1.0,
    2.0,
    3.0,
    5.0,
    10.0
]


print("\nPARTE II-E — COSTO DE AUDITORÍA")
print("=" * 100)

print(
    f"{'Auditoría':>10} | "
    f"{'Sanción':>8} | "
    f"{'Manipulación':>12} | "
    f"{'Auditorías':>11} | "
    f"{'Costo auditoría':>16}"
)

print("-" * 100)


for audit_probability in audit_grid_cost:

    for penalty_multiplier in penalty_grid_cost:

        test_households = strategic_reporting(
            households,
            poverty_line=POVERTY_LINE,
            audit_probability=audit_probability,
            penalty_multiplier=penalty_multiplier,
            fixed_manipulation_cost=25
        )

        manipulators = (
            test_households["strategic"].sum()
        )

        manipulation_rate = (
            manipulators / len(test_households)
        )

        expected_audits = (
            len(test_households)
            * audit_probability
        )

        audit_cost = (
            expected_audits
            * AUDIT_COST_PER_HOUSEHOLD
        )

        print(
            f"{audit_probability:>9.0%} | "
            f"{penalty_multiplier:>7.1f}x | "
            f"{manipulation_rate:>11.2%} | "
            f"{expected_audits:>11,.0f} | "
            f"Q{audit_cost:>15,.2f}"
        )
# ============================================================
# PARTE II-F — PRESUPUESTO TOTAL:
# AUDITORÍA VS TRANSFERENCIAS
# ============================================================

TOTAL_PROGRAM_BUDGET = 20_000_000
AUDIT_COST_PER_HOUSEHOLD = 100

audit_grid_budget = [
    0.05,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50
]

penalty_grid_budget = [
    1.0,
    2.0,
    3.0,
    5.0,
    10.0
]


print("\nPARTE II-F — AUDITORÍA VS TRANSFERENCIAS")
print("=" * 145)

print(
    f"{'Aud.':>6} | "
    f"{'Sanc.':>6} | "
    f"{'Manip.':>8} | "
    f"{'Costo audit.':>14} | "
    f"{'Presup. transf.':>16} | "
    f"{'Pobreza final':>13} | "
    f"{'Salen pobreza':>14} | "
    f"{'Brecha final':>16}"
)

print("-" * 145)


for audit_probability in audit_grid_budget:

    for penalty_multiplier in penalty_grid_budget:

        # ----------------------------------------------------
        # 1. Costo esperado de auditoría
        # ----------------------------------------------------

        expected_audits = (
            len(households)
            * audit_probability
        )

        audit_cost = (
            expected_audits
            * AUDIT_COST_PER_HOUSEHOLD
        )

        # Dinero restante para transferencias
        transfer_budget = max(
            0,
            TOTAL_PROGRAM_BUDGET - audit_cost
        )

        # ----------------------------------------------------
        # 2. Los hogares eligen qué reportar
        # ----------------------------------------------------

        strategic_test = strategic_reporting(
            households,
            poverty_line=POVERTY_LINE,
            audit_probability=audit_probability,
            penalty_multiplier=penalty_multiplier,
            fixed_manipulation_cost=25
        )

        manipulators = (
            strategic_test["strategic"].sum()
        )

        manipulation_rate = (
            manipulators / len(strategic_test)
        )

        # ----------------------------------------------------
        # 3. Gobierno distribuye el presupuesto restante
        # ----------------------------------------------------

        allocation = poverty_gap_transfer_strategic(
            strategic_test,
            transfer_budget
        )

        # ----------------------------------------------------
        # 4. Evaluamos resultados usando ingreso REAL
        # ----------------------------------------------------

        evaluated = calculate_poverty(
            allocation,
            POVERTY_LINE,
            income_column="income_after"
        )

        poor_after = (
            evaluated["poor"].sum()
        )

        poverty_rate_after = (
            poor_after / len(evaluated)
        )

        lifted_from_poverty = (
            households["poor"].sum()
            - poor_after
        )

        remaining_gap = (
            evaluated["poverty_gap"].sum()
        )

        # ----------------------------------------------------
        # 5. Imprimir resultados
        # ----------------------------------------------------

        print(
            f"{audit_probability:>5.0%} | "
            f"{penalty_multiplier:>5.1f}x | "
            f"{manipulation_rate:>7.2%} | "
            f"Q{audit_cost:>13,.0f} | "
            f"Q{transfer_budget:>15,.0f} | "
            f"{poverty_rate_after:>12.2%} | "
            f"{lifted_from_poverty:>14,} | "
            f"Q{remaining_gap:>15,.2f}"
        )
# ============================================================
# PARTE II-G — LÍMITES INSTITUCIONALES A LAS SANCIONES
# ============================================================

TOTAL_PROGRAM_BUDGET = 20_000_000
AUDIT_COST_PER_HOUSEHOLD = 100

penalty_limits = [
    2.0,
    3.0,
    5.0,
    10.0
]


print("\nPARTE II-G — LÍMITES A LAS SANCIONES")
print("=" * 125)

print(
    f"{'Sanción':>8} | "
    f"{'Aud. teórica':>13} | "
    f"{'Escenario':>10} | "
    f"{'Auditoría':>10} | "
    f"{'Manip.':>8} | "
    f"{'Costo audit.':>14} | "
    f"{'Pobreza final':>13} | "
    f"{'Brecha final':>16}"
)

print("-" * 125)


for penalty_multiplier in penalty_limits:

    # --------------------------------------------------------
    # 1. Umbral teórico
    #    p*F >= 0.95
    # --------------------------------------------------------

    theoretical_threshold = (
        0.95 / penalty_multiplier
    )

    # Probamos:
    # - ligeramente debajo del umbral
    # - exactamente en el umbral
    # - ligeramente arriba
    audit_tests = [
        ("Debajo", max(0, theoretical_threshold - 0.005)),
        ("Umbral", theoretical_threshold),
        ("Arriba", min(1, theoretical_threshold + 0.005))
    ]

    for scenario, audit_probability in audit_tests:

        # ----------------------------------------------------
        # 2. Comportamiento estratégico
        # ----------------------------------------------------

        strategic_test = strategic_reporting(
            households,
            poverty_line=POVERTY_LINE,
            audit_probability=audit_probability,
            penalty_multiplier=penalty_multiplier,
            fixed_manipulation_cost=25
        )

        manipulators = (
            strategic_test["strategic"].sum()
        )

        manipulation_rate = (
            manipulators / len(strategic_test)
        )

        # ----------------------------------------------------
        # 3. Costo administrativo
        # ----------------------------------------------------

        expected_audits = (
            len(households)
            * audit_probability
        )

        audit_cost = (
            expected_audits
            * AUDIT_COST_PER_HOUSEHOLD
        )

        transfer_budget = max(
            0,
            TOTAL_PROGRAM_BUDGET - audit_cost
        )

        # ----------------------------------------------------
        # 4. Distribución de transferencias
        # ----------------------------------------------------

        allocation = poverty_gap_transfer_strategic(
            strategic_test,
            transfer_budget
        )

        evaluated = calculate_poverty(
            allocation,
            POVERTY_LINE,
            income_column="income_after"
        )

        poverty_rate_after = (
            evaluated["poor"].mean()
        )

        remaining_gap = (
            evaluated["poverty_gap"].sum()
        )

        # ----------------------------------------------------
        # 5. Resultados
        # ----------------------------------------------------

        print(
            f"{penalty_multiplier:>7.1f}x | "
            f"{theoretical_threshold:>12.2%} | "
            f"{scenario:>10} | "
            f"{audit_probability:>9.2%} | "
            f"{manipulation_rate:>7.2%} | "
            f"Q{audit_cost:>13,.2f} | "
            f"{poverty_rate_after:>12.2%} | "
            f"Q{remaining_gap:>15,.2f}"
        )

# ============================================================
# PARTE III-A — MONTE CARLO
# ============================================================

print("\nPARTE III-A — MONTE CARLO")
print("=" * 80)

monte_carlo_results = run_monte_carlo(
    simulations=50,
    n_households=100_000,
    poverty_line=POVERTY_LINE,
    budget=BUDGET
)

monte_carlo_summary = summarize_monte_carlo(
    monte_carlo_results
)


print("\nRESUMEN MONTE CARLO — 50 SIMULACIONES")
print("=" * 100)

for _, row in monte_carlo_summary.iterrows():

    print(
        f"{row['Indicador']:<28} | "
        f"Media: {row['Media']:>8.2%} | "
        f"DE: {row['Desv.Est.']:>8.2%} | "
        f"Min: {row['Mínimo']:>8.2%} | "
        f"Max: {row['Máximo']:>8.2%}"
    )


print("\nBRECHAS DE POBREZA — MONTE CARLO")
print("=" * 100)

gap_columns = {
    "Gobierno A":
        "A_gap",

    "Gobierno B":
        "B_gap",

    "Gobierno C":
        "C_gap",

    "Gobierno D":
        "D_gap",

    "C imperfecto":
        "C_imp_gap",

    "Estratégico":
        "strategic_gap",

    "Compatible":
        "compatible_gap"
}


for name, column in gap_columns.items():

    print(
        f"{name:<20} | "
        f"Media: Q{monte_carlo_results[column].mean():>14,.2f} | "
        f"DE: Q{monte_carlo_results[column].std():>12,.2f}"
    )

# ============================================================
# PARTE III-B — SENSIBILIDAD AL PRESUPUESTO
# ============================================================

budget_values = [
    10_000_000,
    15_000_000,
    20_000_000,
    25_000_000,
    30_000_000
]


print("\nPARTE III-B — SENSIBILIDAD AL PRESUPUESTO")
print("=" * 120)

print(
    f"{'Presupuesto':>14} | "
    f"{'Gobierno':>10} | "
    f"{'Pobreza final':>14} | "
    f"{'Salen pobreza':>14} | "
    f"{'Brecha final':>17} | "
    f"{'Gastado':>15}"
)

print("-" * 120)


for test_budget in budget_values:

    # ========================================================
    # GOBIERNO A
    # ========================================================

    gov_a_budget = universal_transfer(
        households,
        test_budget
    )

    eval_a_budget = calculate_poverty(
        gov_a_budget,
        POVERTY_LINE,
        income_column="income_after"
    )

    poor_a = eval_a_budget["poor"].sum()

    lifted_a = (
        households["poor"].sum() - poor_a
    )

    gap_a = (
        eval_a_budget["poverty_gap"].sum()
    )

    spent_a = (
        gov_a_budget["transfer"].sum()
    )

    # ========================================================
    # GOBIERNO B
    # ========================================================

    gov_b_budget = poorest_first_transfer(
        households,
        test_budget,
        transfer_amount=1_000
    )

    eval_b_budget = calculate_poverty(
        gov_b_budget,
        POVERTY_LINE,
        income_column="income_after"
    )

    poor_b = eval_b_budget["poor"].sum()

    lifted_b = (
        households["poor"].sum() - poor_b
    )

    gap_b = (
        eval_b_budget["poverty_gap"].sum()
    )

    spent_b = (
        gov_b_budget["transfer"].sum()
    )

    # ========================================================
    # GOBIERNO C
    # ========================================================

    gov_c_budget = poverty_gap_transfer(
        households,
        test_budget
    )

    eval_c_budget = calculate_poverty(
        gov_c_budget,
        POVERTY_LINE,
        income_column="income_after"
    )

    poor_c = eval_c_budget["poor"].sum()

    lifted_c = (
        households["poor"].sum() - poor_c
    )

    gap_c = (
        eval_c_budget["poverty_gap"].sum()
    )

    spent_c = (
        gov_c_budget["transfer"].sum()
    )

    # ========================================================
    # GOBIERNO D
    # ========================================================

    gov_d_budget = deepest_poverty_first_transfer(
        households,
        test_budget
    )

    eval_d_budget = calculate_poverty(
        gov_d_budget,
        POVERTY_LINE,
        income_column="income_after"
    )

    poor_d = eval_d_budget["poor"].sum()

    lifted_d = (
        households["poor"].sum() - poor_d
    )

    gap_d = (
        eval_d_budget["poverty_gap"].sum()
    )

    spent_d = (
        gov_d_budget["transfer"].sum()
    )

    # ========================================================
    # IMPRIMIR RESULTADOS
    # ========================================================

    results_budget = [
        ("A", poor_a, lifted_a, gap_a, spent_a),
        ("B", poor_b, lifted_b, gap_b, spent_b),
        ("C", poor_c, lifted_c, gap_c, spent_c),
        ("D", poor_d, lifted_d, gap_d, spent_d)
    ]

    for government, poor, lifted, gap, spent in results_budget:

        poverty_rate = (
            poor / len(households)
        )

        print(
            f"Q{test_budget:>12,.0f} | "
            f"{government:>10} | "
            f"{poverty_rate:>13.2%} | "
            f"{lifted:>14,} | "
            f"Q{gap:>16,.2f} | "
            f"Q{spent:>14,.2f}"
        )

    print("-" * 120)
# ============================================================
# PARTE III-C — SÍNTESIS FINAL
# ============================================================

create_final_results(
    households=households,
    poverty_line=POVERTY_LINE,
    base_budget=BUDGET,
    monte_carlo_results=monte_carlo_results
)

print("\n" + "=" * 60)
print("FIN DE LA SIMULACIÓN")
print("=" * 60)