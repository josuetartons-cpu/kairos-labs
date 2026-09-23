import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 5 — CORRUPTION ENTERS THE PROCUREMENT MARKET
#
# Objective:
# Compare the honest procurement counterfactual with
# strategically distorted procurement outcomes.
# ============================================================


# ------------------------------------------------------------
# 1. PARAMETERS
# ------------------------------------------------------------

DETECTION_PROBABILITY = 0.10

BRIBE = 20

FIRM_PENALTY = 100
OFFICIAL_PENALTY = 100

PRIVATE_PROFIT_MARGIN = 0.20


# ------------------------------------------------------------
# 2. LOAD HONEST MARKET
# ------------------------------------------------------------

market = pd.read_csv(
    "results/honest_market_all_bids.csv"
)


# ------------------------------------------------------------
# 3. BASIC VALIDATION
# ------------------------------------------------------------

assert len(market) == 500

assert market["tender_id"].nunique() == 100

assert (
    market
    .groupby("tender_id")
    .size()
    .eq(5)
    .all()
)


# ------------------------------------------------------------
# 4. PRIVATE PROFIT
# ------------------------------------------------------------
#
# Synthetic assumption:
#
# PrivateProfit_i = margin * Price_i
#
# This is NOT an empirical estimate.
# It only gives firms heterogeneous private incentives.
# ------------------------------------------------------------

market["private_profit"] = (
    PRIVATE_PROFIT_MARGIN
    * market["price"]
)


# ------------------------------------------------------------
# 5. FIRM'S CORRUPTION PAYOFF
# ------------------------------------------------------------
#
# Once honest ranking is known:
#
# Honest payoff for a losing firm = 0
#
# EU(Bribe) =
# PrivateProfit - Bribe - p * FirmPenalty
# ------------------------------------------------------------

market["bribe_payoff"] = (
    market["private_profit"]
    - BRIBE
    - DETECTION_PROBABILITY * FIRM_PENALTY
)


market["willing_to_bribe"] = (
    market["bribe_payoff"] > 0
)


# ------------------------------------------------------------
# 6. OFFICIAL'S PAYOFF
# ------------------------------------------------------------

official_accept_payoff = (
    BRIBE
    - DETECTION_PROBABILITY * OFFICIAL_PENALTY
)

official_prefers_accept = (
    official_accept_payoff > 0
)


# ------------------------------------------------------------
# 7. PROCESS EACH TENDER
# ------------------------------------------------------------

corrupt_tender_records = []


for tender_id, tender_df in market.groupby(
    "tender_id",
    sort=True
):

    tender_df = tender_df.copy()

    # --------------------------------------------------------
    # Honest winner
    # --------------------------------------------------------

    honest_winner = (
        tender_df
        .sort_values(
            "public_value",
            ascending=False
        )
        .iloc[0]
    )

    honest_public_value = (
        honest_winner["public_value"]
    )


    # --------------------------------------------------------
    # Only losing firms can try to distort the award
    # --------------------------------------------------------

    losing_firms = (
        tender_df[
            tender_df["firm_id"]
            != honest_winner["firm_id"]
        ]
        .copy()
    )


    # --------------------------------------------------------
    # Firms willing to bribe
    # --------------------------------------------------------

    bribing_candidates = (
        losing_firms[
            losing_firms["willing_to_bribe"]
        ]
        .copy()
    )


    # --------------------------------------------------------
    # Default outcome = honest procurement
    # --------------------------------------------------------

    final_winner = honest_winner

    corruption_attempted = False
    corruption_accepted = False
    award_distorted = False

    corrupt_firm_id = None
    corrupt_firm_payoff = np.nan


    # --------------------------------------------------------
    # Strategic corruption attempt
    # --------------------------------------------------------

    if len(bribing_candidates) > 0:

        corruption_attempted = True

        # Firm with highest expected private payoff
        # from corruption attempts the bribe.

        corrupt_candidate = (
            bribing_candidates
            .sort_values(
                "bribe_payoff",
                ascending=False
            )
            .iloc[0]
        )

        corrupt_firm_id = (
            corrupt_candidate["firm_id"]
        )

        corrupt_firm_payoff = (
            corrupt_candidate["bribe_payoff"]
        )


        # ----------------------------------------------------
        # Official decision
        # ----------------------------------------------------

        if official_prefers_accept:

            corruption_accepted = True

            final_winner = (
                corrupt_candidate
            )

            award_distorted = (
                final_winner["firm_id"]
                != honest_winner["firm_id"]
            )


    # --------------------------------------------------------
    # Final public value
    # --------------------------------------------------------

    final_public_value = (
        final_winner["public_value"]
    )


    # --------------------------------------------------------
    # Corruption loss
    # --------------------------------------------------------

    corruption_loss = (
        honest_public_value
        - final_public_value
    )


    # Numerical safety
    if corruption_loss < 0 and np.isclose(
        corruption_loss,
        0
    ):
        corruption_loss = 0.0


    assert corruption_loss >= 0


    # --------------------------------------------------------
    # Save tender-level result
    # --------------------------------------------------------

    corrupt_tender_records.append(
        {
            "tender_id":
                tender_id,

            "honest_winner":
                honest_winner["firm_id"],

            "honest_public_value":
                honest_public_value,

            "corrupt_candidate":
                corrupt_firm_id,

            "corrupt_firm_payoff":
                corrupt_firm_payoff,

            "corruption_attempted":
                corruption_attempted,

            "official_accepts":
                official_prefers_accept,

            "corruption_accepted":
                corruption_accepted,

            "award_distorted":
                award_distorted,

            "final_winner":
                final_winner["firm_id"],

            "final_public_value":
                final_public_value,

            "corruption_loss":
                corruption_loss
        }
    )


# ------------------------------------------------------------
# 8. RESULTS DATAFRAME
# ------------------------------------------------------------

corruption_results = pd.DataFrame(
    corrupt_tender_records
)


# ------------------------------------------------------------
# 9. AGGREGATE RESULTS
# ------------------------------------------------------------

total_public_value_honest = (
    corruption_results[
        "honest_public_value"
    ].sum()
)

total_public_value_corrupt = (
    corruption_results[
        "final_public_value"
    ].sum()
)

total_corruption_loss = (
    corruption_results[
        "corruption_loss"
    ].sum()
)


corruption_attempts = (
    corruption_results[
        "corruption_attempted"
    ].sum()
)

accepted_bribes = (
    corruption_results[
        "corruption_accepted"
    ].sum()
)

distorted_awards = (
    corruption_results[
        "award_distorted"
    ].sum()
)


average_loss_per_distorted_tender = (
    corruption_results.loc[
        corruption_results[
            "award_distorted"
        ],
        "corruption_loss"
    ].mean()
)


if np.isnan(
    average_loss_per_distorted_tender
):
    average_loss_per_distorted_tender = 0


# ------------------------------------------------------------
# 10. VALIDATE ACCOUNTING
# ------------------------------------------------------------

assert np.isclose(
    total_public_value_honest
    - total_public_value_corrupt,
    total_corruption_loss
)


assert np.isclose(
    total_public_value_honest,
    8197.05,
    atol=0.02
)


# ------------------------------------------------------------
# 11. SUMMARY TABLE
# ------------------------------------------------------------

summary = pd.DataFrame(
    [
        {
            "detection_probability":
                DETECTION_PROBABILITY,

            "bribe":
                BRIBE,

            "firm_penalty":
                FIRM_PENALTY,

            "official_penalty":
                OFFICIAL_PENALTY,

            "private_profit_margin":
                PRIVATE_PROFIT_MARGIN,

            "official_accept_payoff":
                official_accept_payoff,

            "corruption_attempts":
                corruption_attempts,

            "accepted_bribes":
                accepted_bribes,

            "distorted_awards":
                distorted_awards,

            "public_value_honest":
                total_public_value_honest,

            "public_value_corrupt":
                total_public_value_corrupt,

            "total_corruption_loss":
                total_corruption_loss,

            "average_loss_per_distorted_tender":
                average_loss_per_distorted_tender
        }
    ]
)


# ------------------------------------------------------------
# 12. SAVE RESULTS
# ------------------------------------------------------------

corruption_results.to_csv(
    "results/corruption_market.csv",
    index=False
)

summary.to_csv(
    "results/corruption_summary.csv",
    index=False
)


# ============================================================
# 13. FIGURE — HONEST VS CORRUPT PUBLIC VALUE
# ============================================================

comparison = pd.DataFrame(
    {
        "Scenario": [
            "Honest market",
            "Corrupt market"
        ],

        "Public Value": [
            total_public_value_honest,
            total_public_value_corrupt
        ]
    }
)


plt.figure(
    figsize=(8, 6)
)

plt.bar(
    comparison["Scenario"],
    comparison["Public Value"]
)

plt.ylabel(
    "Total Public Value"
)

plt.title(
    "Kairos Corruption Lab — "
    "Honest vs Corrupt Procurement"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "honest_vs_corrupt_public_value.png",
    dpi=300
)

plt.close()


# ============================================================
# 14. FIGURE — LOSS BY TENDER
# ============================================================

plt.figure(
    figsize=(11, 6)
)

plt.bar(
    corruption_results[
        "tender_id"
    ],
    corruption_results[
        "corruption_loss"
    ]
)

plt.xlabel(
    "Tender"
)

plt.ylabel(
    "Public Value Loss"
)

plt.title(
    "Kairos Corruption Lab — "
    "Corruption Loss by Tender"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "corruption_loss_by_tender.png",
    dpi=300
)

plt.close()


# ============================================================
# 15. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 72
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 5 — "
    "CORRUPTION ENTERS PROCUREMENT"
)

print(
    "=" * 72
)


print(
    "\nINSTITUTIONAL PARAMETERS"
)

print(
    f"Detection probability: "
    f"{DETECTION_PROBABILITY:.0%}"
)

print(
    f"Bribe: "
    f"{BRIBE:.2f}"
)

print(
    f"Firm penalty: "
    f"{FIRM_PENALTY:.2f}"
)

print(
    f"Official penalty: "
    f"{OFFICIAL_PENALTY:.2f}"
)

print(
    f"Private profit margin: "
    f"{PRIVATE_PROFIT_MARGIN:.0%}"
)


print(
    "\nOFFICIAL"
)

print(
    f"EU(Accept): "
    f"{official_accept_payoff:.2f}"
)

print(
    f"Best response: "
    f"{'ACCEPT' if official_prefers_accept else 'REJECT'}"
)


print(
    "\nCORRUPTION ACTIVITY"
)

print(
    f"Corruption attempts: "
    f"{corruption_attempts}"
)

print(
    f"Accepted bribes: "
    f"{accepted_bribes}"
)

print(
    f"Distorted awards: "
    f"{distorted_awards}"
)


print(
    "\nPUBLIC VALUE"
)

print(
    f"Honest Public Value: "
    f"{total_public_value_honest:.2f}"
)

print(
    f"Corrupt Public Value: "
    f"{total_public_value_corrupt:.2f}"
)

print(
    f"Total Corruption Loss: "
    f"{total_corruption_loss:.2f}"
)


loss_percentage = (
    total_corruption_loss
    / total_public_value_honest
    * 100
)


print(
    f"Loss as % of honest value: "
    f"{loss_percentage:.2f}%"
)


print(
    f"Average loss per distorted tender: "
    f"{average_loss_per_distorted_tender:.2f}"
)


# ------------------------------------------------------------
# 16. FIRST 10 DISTORTED TENDERS
# ------------------------------------------------------------

distorted = (
    corruption_results[
        corruption_results[
            "award_distorted"
        ]
    ]
)


print(
    "\nFIRST 10 DISTORTED TENDERS"
)


if len(distorted) == 0:

    print(
        "No awards were distorted."
    )

else:

    print(
        distorted[
            [
                "tender_id",
                "honest_winner",
                "corrupt_candidate",
                "honest_public_value",
                "final_public_value",
                "corruption_loss"
            ]
        ]
        .head(10)
        .to_string(
            index=False,
            formatters={
                "honest_public_value":
                    "{:.2f}".format,

                "final_public_value":
                    "{:.2f}".format,

                "corruption_loss":
                    "{:.2f}".format
            }
        )
    )


print(
    "\nFILES GENERATED"
)

print(
    "results/corruption_market.csv"
)

print(
    "results/corruption_summary.csv"
)

print(
    "figures/"
    "honest_vs_corrupt_public_value.png"
)

print(
    "figures/"
    "corruption_loss_by_tender.png"
)


print(
    "\nExperiment 5 completed correctly."
)

print(
    "=" * 72
    + "\n"
)