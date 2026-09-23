import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 4 — HONEST PROCUREMENT MARKET
#
# Objectives:
# 1. Validate one transparent procurement benchmark.
# 2. Build a reproducible synthetic market of 100 tenders.
# 3. Select winners using Public Value.
# 4. Measure the honest-market counterfactual.
#
# IMPORTANT:
# No corruption is introduced in this file yet.
# ============================================================


# ------------------------------------------------------------
# 1. GLOBAL PARAMETERS
# ------------------------------------------------------------

SEED = 42

N_TENDERS = 100
N_FIRMS_PER_TENDER = 5

WEIGHT_QUALITY = 0.30
WEIGHT_PRICE = 0.25
WEIGHT_EXPERIENCE = 0.25
WEIGHT_LOW_RISK = 0.20


# ------------------------------------------------------------
# 2. VALIDATE WEIGHTS
# ------------------------------------------------------------

total_weight = (
    WEIGHT_QUALITY
    + WEIGHT_PRICE
    + WEIGHT_EXPERIENCE
    + WEIGHT_LOW_RISK
)

assert np.isclose(
    total_weight,
    1.0
)


# ------------------------------------------------------------
# 3. PUBLIC VALUE FUNCTIONS
# ------------------------------------------------------------

def calculate_price_score(prices):
    """
    Normalize prices within one tender.

    Cheapest offer -> 100
    Most expensive offer -> 0

    All other offers are positioned proportionally
    between those two values.
    """

    price_min = prices.min()
    price_max = prices.max()

    if np.isclose(
        price_min,
        price_max
    ):
        return pd.Series(
            100.0,
            index=prices.index
        )

    return (
        100
        * (
            1
            - (
                (prices - price_min)
                / (price_max - price_min)
            )
        )
    )


def calculate_public_value(df):
    """
    Calculate Public Value using the weights
    selected for Kairos Corruption Lab.

    PublicValue =
        0.30 * Quality
        + 0.25 * PriceScore
        + 0.25 * Experience
        + 0.20 * LowRisk
    """

    return (
        WEIGHT_QUALITY
        * df["quality"]

        + WEIGHT_PRICE
        * df["price_score"]

        + WEIGHT_EXPERIENCE
        * df["experience"]

        + WEIGHT_LOW_RISK
        * df["low_risk_score"]
    )


def evaluate_tender(tender_df):
    """
    Evaluate all firms participating in one tender.

    Returns the same DataFrame with:
    - price score
    - low-risk score
    - public value
    - rank
    """

    tender_df = tender_df.copy()

    tender_df["price_score"] = (
        calculate_price_score(
            tender_df["price"]
        )
    )

    tender_df["low_risk_score"] = (
        100
        - tender_df["risk"]
    )

    tender_df["public_value"] = (
        calculate_public_value(
            tender_df
        )
    )

    tender_df["rank"] = (
        tender_df["public_value"]
        .rank(
            ascending=False,
            method="first"
        )
        .astype(int)
    )

    return tender_df


# ============================================================
# PART A
# DETERMINISTIC FIVE-FIRM BENCHMARK
# ============================================================


# ------------------------------------------------------------
# 4. BENCHMARK FIRMS
# ------------------------------------------------------------

benchmark_firms = pd.DataFrame(
    [
        {
            "firm": "Empresa A",
            "price": 800,
            "quality": 80,
            "experience": 70,
            "risk": 20
        },
        {
            "firm": "Empresa B",
            "price": 700,
            "quality": 65,
            "experience": 60,
            "risk": 25
        },
        {
            "firm": "Empresa C",
            "price": 900,
            "quality": 95,
            "experience": 90,
            "risk": 10
        },
        {
            "firm": "Empresa D",
            "price": 750,
            "quality": 75,
            "experience": 85,
            "risk": 30
        },
        {
            "firm": "Empresa E",
            "price": 650,
            "quality": 55,
            "experience": 50,
            "risk": 40
        }
    ]
)


# ------------------------------------------------------------
# 5. EVALUATE BENCHMARK
# ------------------------------------------------------------

benchmark_firms = (
    evaluate_tender(
        benchmark_firms
    )
    .sort_values(
        by="public_value",
        ascending=False
    )
    .reset_index(drop=True)
)

benchmark_winner = (
    benchmark_firms.iloc[0]
)


# ------------------------------------------------------------
# 6. VALIDATE BENCHMARK
# ------------------------------------------------------------

assert len(
    benchmark_firms
) == 5

assert benchmark_firms[
    "price_score"
].between(
    0,
    100
).all()

assert benchmark_firms[
    "low_risk_score"
].between(
    0,
    100
).all()

assert benchmark_firms[
    "public_value"
].between(
    0,
    100
).all()

assert (
    benchmark_winner["firm"]
    == "Empresa D"
)

assert np.isclose(
    benchmark_winner[
        "public_value"
    ],
    72.75
)


# ------------------------------------------------------------
# 7. SAVE BENCHMARK
# ------------------------------------------------------------

benchmark_firms.to_csv(
    "results/honest_market.csv",
    index=False
)


# ------------------------------------------------------------
# 8. PRINT BENCHMARK
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 72
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 4A — "
    "HONEST PROCUREMENT BENCHMARK"
)

print(
    "=" * 72
)


print(
    "\nPUBLIC VALUE WEIGHTS"
)

print(
    f"Quality:     "
    f"{WEIGHT_QUALITY:.0%}"
)

print(
    f"Price:       "
    f"{WEIGHT_PRICE:.0%}"
)

print(
    f"Experience:  "
    f"{WEIGHT_EXPERIENCE:.0%}"
)

print(
    f"Low risk:    "
    f"{WEIGHT_LOW_RISK:.0%}"
)


print(
    "\nBENCHMARK WINNER"
)

print(
    f"Winner: "
    f"{benchmark_winner['firm']}"
)

print(
    f"Public value: "
    f"{benchmark_winner['public_value']:.2f}"
)

print(
    "\nBenchmark validated correctly."
)


# ============================================================
# PART B
# SYNTHETIC MARKET — 100 TENDERS
# ============================================================


# ------------------------------------------------------------
# 9. INITIALIZE REPRODUCIBLE GENERATOR
# ------------------------------------------------------------

rng = np.random.default_rng(
    SEED
)


# ------------------------------------------------------------
# 10. GENERATE SYNTHETIC PROCUREMENT MARKET
# ------------------------------------------------------------
#
# Every tender contains 5 firms.
#
# Synthetic characteristics:
#
# price       -> 650 to 950
# quality     -> 50 to 100
# experience  -> 40 to 100
# risk        -> 5 to 45
#
# These are NOT empirical Guatemala estimates.
# They only define the artificial economy.
# ------------------------------------------------------------

market_records = []


for tender_id in range(
    1,
    N_TENDERS + 1
):

    for firm_number in range(
        1,
        N_FIRMS_PER_TENDER + 1
    ):

        market_records.append(
            {
                "tender_id": tender_id,

                "firm_id": (
                    f"T{tender_id:03d}_"
                    f"F{firm_number}"
                ),

                "price": rng.uniform(
                    650,
                    950
                ),

                "quality": rng.uniform(
                    50,
                    100
                ),

                "experience": rng.uniform(
                    40,
                    100
                ),

                "risk": rng.uniform(
                    5,
                    45
                )
            }
        )


market = pd.DataFrame(
    market_records
)


# ------------------------------------------------------------
# 11. VALIDATE RAW MARKET
# ------------------------------------------------------------

expected_rows = (
    N_TENDERS
    * N_FIRMS_PER_TENDER
)

assert len(
    market
) == expected_rows

assert (
    market["tender_id"]
    .nunique()
    == N_TENDERS
)

assert (
    market
    .groupby("tender_id")
    .size()
    .eq(
        N_FIRMS_PER_TENDER
    )
    .all()
)


# ------------------------------------------------------------
# 12. EVALUATE EVERY TENDER
# ------------------------------------------------------------

evaluated_tenders = []


for tender_id, tender_df in market.groupby(
    "tender_id",
    sort=True
):

    evaluated = (
        evaluate_tender(
            tender_df
        )
    )

    evaluated_tenders.append(
        evaluated
    )


honest_market = pd.concat(
    evaluated_tenders,
    ignore_index=True
)


# ------------------------------------------------------------
# 13. SELECT HONEST WINNER OF EACH TENDER
# ------------------------------------------------------------

honest_winners = (
    honest_market[
        honest_market["rank"] == 1
    ]
    .copy()
    .sort_values(
        "tender_id"
    )
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# 14. VALIDATE WINNERS
# ------------------------------------------------------------

assert len(
    honest_winners
) == N_TENDERS

assert (
    honest_winners[
        "tender_id"
    ]
    .nunique()
    == N_TENDERS
)

assert (
    honest_winners[
        "rank"
    ]
    == 1
).all()


# ------------------------------------------------------------
# 15. HONEST-MARKET COUNTERFACTUAL
# ------------------------------------------------------------

total_public_value_honest = (
    honest_winners[
        "public_value"
    ].sum()
)

average_public_value_honest = (
    honest_winners[
        "public_value"
    ].mean()
)

median_public_value_honest = (
    honest_winners[
        "public_value"
    ].median()
)

total_spending_honest = (
    honest_winners[
        "price"
    ].sum()
)

average_winning_price = (
    honest_winners[
        "price"
    ].mean()
)

average_winner_quality = (
    honest_winners[
        "quality"
    ].mean()
)

average_winner_experience = (
    honest_winners[
        "experience"
    ].mean()
)

average_winner_risk = (
    honest_winners[
        "risk"
    ].mean()
)


# ------------------------------------------------------------
# 16. BUILD SUMMARY TABLE
# ------------------------------------------------------------

summary = pd.DataFrame(
    [
        {
            "seed": SEED,

            "n_tenders": N_TENDERS,

            "firms_per_tender":
                N_FIRMS_PER_TENDER,

            "total_bids":
                len(honest_market),

            "total_public_value_honest":
                total_public_value_honest,

            "average_public_value_honest":
                average_public_value_honest,

            "median_public_value_honest":
                median_public_value_honest,

            "total_spending_honest":
                total_spending_honest,

            "average_winning_price":
                average_winning_price,

            "average_winner_quality":
                average_winner_quality,

            "average_winner_experience":
                average_winner_experience,

            "average_winner_risk":
                average_winner_risk
        }
    ]
)


# ------------------------------------------------------------
# 17. SAVE MARKET RESULTS
# ------------------------------------------------------------

honest_market.to_csv(
    "results/honest_market_all_bids.csv",
    index=False
)

honest_winners.to_csv(
    "results/honest_market_winners.csv",
    index=False
)

summary.to_csv(
    "results/honest_market_summary.csv",
    index=False
)


# ============================================================
# PART C
# FIGURES
# ============================================================


# ------------------------------------------------------------
# 18. DISTRIBUTION OF WINNING PUBLIC VALUE
# ------------------------------------------------------------

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    honest_winners[
        "public_value"
    ],
    bins=15
)

plt.axvline(
    average_public_value_honest,
    linestyle="--",
    label=(
        "Average honest "
        "public value"
    )
)

plt.xlabel(
    "Winning Public Value"
)

plt.ylabel(
    "Number of tenders"
)

plt.title(
    "Kairos Corruption Lab — "
    "Honest Procurement Benchmark"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "honest_public_value_distribution.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 19. PUBLIC VALUE BY TENDER
# ------------------------------------------------------------

plt.figure(
    figsize=(11, 6)
)

plt.plot(
    honest_winners[
        "tender_id"
    ],
    honest_winners[
        "public_value"
    ]
)

plt.axhline(
    average_public_value_honest,
    linestyle="--",
    label=(
        "Average honest "
        "public value"
    )
)

plt.xlabel(
    "Tender"
)

plt.ylabel(
    "Winning Public Value"
)

plt.title(
    "Kairos Corruption Lab — "
    "Public Value Across Honest Tenders"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "honest_public_value_by_tender.png",
    dpi=300
)

plt.close()


# ============================================================
# PART D
# TERMINAL SUMMARY
# ============================================================

print(
    "\n"
    + "=" * 72
)

print(
    "EXPERIMENT 4B — "
    "100-TENDER HONEST MARKET"
)

print(
    "=" * 72
)


print(
    f"\nSeed: "
    f"{SEED}"
)

print(
    f"Tenders: "
    f"{N_TENDERS}"
)

print(
    f"Firms per tender: "
    f"{N_FIRMS_PER_TENDER}"
)

print(
    f"Total bids: "
    f"{len(honest_market)}"
)


print(
    "\nHONEST MARKET COUNTERFACTUAL"
)

print(
    f"Total Public Value: "
    f"{total_public_value_honest:.2f}"
)

print(
    f"Average Public Value: "
    f"{average_public_value_honest:.2f}"
)

print(
    f"Median Public Value: "
    f"{median_public_value_honest:.2f}"
)


print(
    "\nWINNING CONTRACT CHARACTERISTICS"
)

print(
    f"Total spending: "
    f"{total_spending_honest:.2f}"
)

print(
    f"Average winning price: "
    f"{average_winning_price:.2f}"
)

print(
    f"Average quality: "
    f"{average_winner_quality:.2f}"
)

print(
    f"Average experience: "
    f"{average_winner_experience:.2f}"
)

print(
    f"Average risk: "
    f"{average_winner_risk:.2f}"
)


# ------------------------------------------------------------
# 20. SHOW FIRST 10 WINNERS
# ------------------------------------------------------------

print(
    "\nFIRST 10 HONEST WINNERS"
)

winner_columns = [
    "tender_id",
    "firm_id",
    "price",
    "quality",
    "experience",
    "risk",
    "price_score",
    "public_value"
]

print(
    honest_winners[
        winner_columns
    ]
    .head(10)
    .to_string(
        index=False,
        formatters={
            "price":
                "{:.2f}".format,

            "quality":
                "{:.2f}".format,

            "experience":
                "{:.2f}".format,

            "risk":
                "{:.2f}".format,

            "price_score":
                "{:.2f}".format,

            "public_value":
                "{:.2f}".format
        }
    )
)


# ------------------------------------------------------------
# 21. FINAL VALIDATION
# ------------------------------------------------------------

assert (
    total_public_value_honest
    > 0
)

assert (
    average_public_value_honest
    >= 0
)

assert (
    average_public_value_honest
    <= 100
)

assert (
    honest_market[
        "public_value"
    ]
    .between(
        0,
        100
    )
    .all()
)


print(
    "\nMarket validations passed correctly."
)


print(
    "\nFILES GENERATED"
)

print(
    "results/honest_market.csv"
)

print(
    "results/honest_market_all_bids.csv"
)

print(
    "results/honest_market_winners.csv"
)

print(
    "results/honest_market_summary.csv"
)

print()

print(
    "figures/"
    "honest_public_value_distribution.png"
)

print(
    "figures/"
    "honest_public_value_by_tender.png"
)


print(
    "\nExperiment 4 completed correctly."
)

print(
    "=" * 72
    + "\n"
)