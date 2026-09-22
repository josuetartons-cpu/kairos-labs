# ============================================================
# KAIROS OPTIMIZATION LAB #1
# GAME THEORY
# ============================================================


def strategic_reporting(
    households,
    poverty_line,
    audit_probability=0.10,
    penalty_multiplier=2.0,
    fixed_manipulation_cost=25
):
    """
    Cada hogar puede elegir entre:

    1. Reportar su ingreso verdadero.
    2. Subdeclarar Q250.
    3. Subdeclarar Q500.

    El hogar elige el reporte que maximiza
    su utilidad esperada.
    """

    df = households.copy()

    reporting_options = [
        0,
        250,
        500
    ]

    chosen_reports = []
    chosen_manipulation = []
    expected_utilities = []

    for _, row in df.iterrows():

        true_income = row["income"]

        best_utility = float("-inf")
        best_report = true_income
        best_manipulation = 0

        for manipulation in reporting_options:

            reported_income = max(
                0,
                true_income - manipulation
            )

            # Transferencia que el hogar espera recibir
            expected_transfer = max(
                0,
                poverty_line - reported_income
            )

            # Costo esperado de ser descubierto
            expected_penalty = (
                audit_probability
                * penalty_multiplier
                * manipulation
            )

            # Mentir también tiene un pequeño costo fijo
            if manipulation > 0:
                manipulation_cost = (
                    expected_penalty
                    + fixed_manipulation_cost
                )
            else:
                manipulation_cost = 0

            # Utilidad esperada
            utility = (
                true_income
                + expected_transfer
                - manipulation_cost
            )

            if utility > best_utility:

                best_utility = utility
                best_report = reported_income
                best_manipulation = manipulation

        chosen_reports.append(
            best_report
        )

        chosen_manipulation.append(
            best_manipulation
        )

        expected_utilities.append(
            best_utility
        )

    df["income_reported"] = (
        chosen_reports
    )

    df["manipulation"] = (
        chosen_manipulation
    )

    df["strategic"] = (
        df["manipulation"] > 0
    )

    df["expected_utility"] = (
        expected_utilities
    )

    df["poor_reported"] = (
        df["income_reported"]
        < poverty_line
    )

    df["poverty_gap_reported"] = (
        poverty_line
        - df["income_reported"]
    ).clip(lower=0)

    return df