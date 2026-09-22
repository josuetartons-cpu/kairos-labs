# ============================================================
# KAIROS OPTIMIZATION LAB #1
# POLÍTICAS DE TRANSFERENCIA
# ============================================================


# ============================================================
# GOBIERNO A — TRANSFERENCIA UNIVERSAL
# ============================================================

def universal_transfer(
    households,
    budget
):
    df = households.copy()

    transfer_per_household = (
        budget / len(df)
    )

    df["transfer"] = transfer_per_household

    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df


# ============================================================
# GOBIERNO B — LOS MÁS POBRES PRIMERO
# ============================================================

def poorest_first_transfer(
    households,
    budget,
    transfer_amount=1_000
):
    df = households.copy()

    df["transfer"] = 0.0

    poor_households = (
        df[df["poor"]]
        .copy()
        .sort_values(
            by="income",
            ascending=True
        )
    )

    max_beneficiaries = int(
        budget // transfer_amount
    )

    selected = poor_households.head(
        max_beneficiaries
    )

    df.loc[
        selected.index,
        "transfer"
    ] = transfer_amount

    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df


# ============================================================
# GOBIERNO C — CIERRE EXACTO DE BRECHA
# ============================================================

def poverty_gap_transfer(
    households,
    budget
):
    df = households.copy()

    df["transfer"] = 0.0

    poor_households = (
        df[df["poor"]]
        .copy()
        .sort_values(
            by="poverty_gap",
            ascending=True
        )
    )

    remaining_budget = budget

    for idx, row in poor_households.iterrows():

        required = row["poverty_gap"]

        if required <= remaining_budget:

            df.loc[
                idx,
                "transfer"
            ] = required

            remaining_budget -= required

        else:
            break

    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df


# ============================================================
# GOBIERNO D — POBREZA MÁS PROFUNDA PRIMERO
# ============================================================

def deepest_poverty_first_transfer(
    households,
    budget
):
    df = households.copy()

    df["transfer"] = 0.0

    poor_households = (
        df[df["poor"]]
        .copy()
        .sort_values(
            by="poverty_gap",
            ascending=False
        )
    )

    remaining_budget = budget

    for idx, row in poor_households.iterrows():

        if remaining_budget <= 0:
            break

        required = row["poverty_gap"]

        transfer = min(
            required,
            remaining_budget
        )

        df.loc[
            idx,
            "transfer"
        ] = transfer

        remaining_budget -= transfer

    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df


# ============================================================
# GOBIERNO C — INFORMACIÓN IMPERFECTA
# ============================================================

def poverty_gap_transfer_imperfect(
    households,
    budget
):
    df = households.copy()

    df["transfer"] = 0.0

    perceived_poor = (
        df[df["poor_observed"]]
        .copy()
        .sort_values(
            by="poverty_gap_observed",
            ascending=True
        )
    )

    remaining_budget = budget

    for idx, row in perceived_poor.iterrows():

        required = row[
            "poverty_gap_observed"
        ]

        if required <= remaining_budget:

            df.loc[
                idx,
                "transfer"
            ] = required

            remaining_budget -= required

        else:
            break

    # Decidimos con ingreso observado,
    # evaluamos usando ingreso verdadero.
    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df

# ============================================================
# GOBIERNO C — REPORTES ESTRATÉGICOS
# ============================================================

def poverty_gap_transfer_strategic(
    households,
    budget
):
    df = households.copy()

    df["transfer"] = 0.0

    perceived_poor = (
        df[df["poor_reported"]]
        .copy()
        .sort_values(
            by="poverty_gap_reported",
            ascending=True
        )
    )

    remaining_budget = budget

    for idx, row in perceived_poor.iterrows():

        required = row["poverty_gap_reported"]

        if required <= remaining_budget:

            df.loc[
                idx,
                "transfer"
            ] = required

            remaining_budget -= required

        else:
            break

    # Evaluamos usando ingreso verdadero
    df["income_after"] = (
        df["income"] + df["transfer"]
    )

    return df
