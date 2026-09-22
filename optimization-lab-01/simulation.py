import numpy as np
import pandas as pd


# ============================================================
# GENERACIÓN DE HOGARES
# ============================================================

def generate_households(
    n=100_000,
    seed=42
):
    rng = np.random.default_rng(seed)

    household_size = rng.integers(
        1,
        8,
        size=n
    )

    income = rng.lognormal(
        mean=8.0,
        sigma=0.75,
        size=n
    )

    households = pd.DataFrame({
        "household_id": np.arange(n),
        "members": household_size,
        "income": income
    })

    return households


# ============================================================
# CÁLCULO DE POBREZA
# ============================================================

def calculate_poverty(
    households,
    poverty_line,
    income_column="income"
):
    df = households.copy()

    df["poor"] = (
        df[income_column] < poverty_line
    )

    df["poverty_gap"] = np.maximum(
        0,
        poverty_line - df[income_column]
    )

    return df


# ============================================================
# ÍNDICES FGT
# ============================================================

def calculate_fgt(
    households,
    poverty_line,
    income_column="income"
):
    df = households.copy()

    income = df[income_column]

    normalized_gap = (
        (poverty_line - income)
        / poverty_line
    ).clip(lower=0)

    fgt0 = (
        income < poverty_line
    ).mean()

    fgt1 = normalized_gap.mean()

    fgt2 = (
        normalized_gap ** 2
    ).mean()

    return {
        "FGT0": fgt0,
        "FGT1": fgt1,
        "FGT2": fgt2
    }


# ============================================================
# ERROR DE MEDICIÓN DEL INGRESO
# ============================================================

def add_income_measurement_error(
    households,
    poverty_line,
    sigma=500,
    seed=123
):
    df = households.copy()

    rng = np.random.default_rng(seed)

    error = rng.normal(
        loc=0,
        scale=sigma,
        size=len(df)
    )

    df["income_observed"] = (
        df["income"] + error
    ).clip(lower=0)

    df["poor_observed"] = (
        df["income_observed"]
        < poverty_line
    )

    df["poverty_gap_observed"] = np.maximum(
        0,
        poverty_line
        - df["income_observed"]
    )

    return df