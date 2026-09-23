import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 7 — INSTITUTIONAL RESPONSE TO SANCTIONS
#
# Objective:
# Hold the market and probability of detection constant,
# vary only the sanction level F,
# and observe changes in incentives, corruption, and Public Value.
#
# IMPORTANT:
# This is NOT Monte Carlo.
# We use the exact same 100 tenders and 500 bids.
# ============================================================


# ------------------------------------------------------------
# 1. FIXED PARAMETERS
# ------------------------------------------------------------

DETECTION_PROBABILITY = 0.10

BRIBE = 20

PRIVATE_PROFIT_MARGIN = 0.20

HONEST_PUBLIC_VALUE_EXPECTED = 8197.05


# ------------------------------------------------------------
# 2. SANCTION GRID
# ------------------------------------------------------------
#
# F = 0, 25, 50, ..., 2000
#
# We go to 2000 because, under the current private-profit
# assumptions, firms begin leaving corruption only above
# roughly 1100 and the strongest firms may require around 1700.
# ------------------------------------------------------------

SANCTION_VALUES = np.arange(
    0,
    2000 + 25,
    25
)


# ------------------------------------------------------------
# 3. LOAD THE SAME HONEST MARKET
# ------------------------------------------------------------

market = pd.read_csv(
    "results/honest_market_all_bids.csv"
)


# ------------------------------------------------------------
# 4. VALIDATE MARKET
# ------------------------------------------------------------

assert len(market) == 500

assert (
    market["tender_id"]
    .nunique()
    == 100
)

assert (
    market
    .groupby("tender_id")
    .size()
    .eq(5)
    .all()
)


# ------------------------------------------------------------
# 5. PRIVATE PROFIT
# ------------------------------------------------------------

market["private_profit"] = (
    PRIVATE_PROFIT_MARGIN
    * market["price"]
)


# ------------------------------------------------------------
# 6. RUN ONE SANCTION SCENARIO
# ------------------------------------------------------------

def run_scenario(
    sanction
):
    """
    Run all 100 tenders for one common sanction level.

    For this experiment:
    firm_penalty = official_penalty = sanction

    Detection probability stays fixed at 10%.
    """

    scenario_market = market.copy()


    # --------------------------------------------------------
    # Firm payoff from corruption
    # --------------------------------------------------------

    scenario_market[
        "bribe_payoff"
    ] = (
        scenario_market[
            "private_profit"
        ]
        - BRIBE
        - DETECTION_PROBABILITY
        * sanction
    )


    scenario_market[
        "willing_to_bribe"
    ] = (
        scenario_market[
            "bribe_payoff"
        ]
        > 0
    )


    # --------------------------------------------------------
    # Official payoff
    # --------------------------------------------------------

    official_accept_payoff = (
        BRIBE
        - DETECTION_PROBABILITY
        * sanction
    )

    official_prefers_accept = (
        official_accept_payoff > 0
    )


    # --------------------------------------------------------
    # Process every tender
    # --------------------------------------------------------

    tender_records = []


    for tender_id, tender_df in (
        scenario_market
        .groupby(
            "tender_id",
            sort=True
        )
    ):

        tender_df = tender_df.copy()


        # ----------------------------------------------------
        # Honest winner
        # ----------------------------------------------------

        honest_winner = (
            tender_df
            .sort_values(
                "public_value",
                ascending=False
            )
            .iloc[0]
        )

        honest_public_value = (
            honest_winner[
                "public_value"
            ]
        )


        # ----------------------------------------------------
        # Losing firms only
        # ----------------------------------------------------

        losing_firms = (
            tender_df[
                tender_df["firm_id"]
                != honest_winner["firm_id"]
            ]
            .copy()
        )


        # ----------------------------------------------------
        # Firms willing to bribe
        # ----------------------------------------------------

        bribing_candidates = (
            losing_firms[
                losing_firms[
                    "willing_to_bribe"
                ]
            ]
            .copy()
        )


        # ----------------------------------------------------
        # Default outcome
        # ----------------------------------------------------

        final_winner = honest_winner

        corruption_attempted = False
        corruption_accepted = False
        award_distorted = False


        # ----------------------------------------------------
        # Strategic corruption
        # ----------------------------------------------------

        if len(
            bribing_candidates
        ) > 0:

            corruption_attempted = True

            corrupt_candidate = (
                bribing_candidates
                .sort_values(
                    "bribe_payoff",
                    ascending=False
                )
                .iloc[0]
            )


            # ------------------------------------------------
            # Official decision
            # ------------------------------------------------

            if official_prefers_accept:

                corruption_accepted = True

                final_winner = (
                    corrupt_candidate
                )

                award_distorted = (
                    final_winner["firm_id"]
                    != honest_winner[
                        "firm_id"
                    ]
                )


        # ----------------------------------------------------
        # Final Public Value
        # ----------------------------------------------------

        final_public_value = (
            final_winner[
                "public_value"
            ]
        )


        # ----------------------------------------------------
        # Corruption loss
        # ----------------------------------------------------

        corruption_loss = (
            honest_public_value
            - final_public_value
        )


        if (
            corruption_loss < 0
            and np.isclose(
                corruption_loss,
                0
            )
        ):
            corruption_loss = 0.0


        assert (
            corruption_loss >= 0
        )


        tender_records.append(
            {
                "tender_id":
                    tender_id,

                "honest_public_value":
                    honest_public_value,

                "final_public_value":
                    final_public_value,

                "corruption_attempted":
                    corruption_attempted,

                "corruption_accepted":
                    corruption_accepted,

                "award_distorted":
                    award_distorted,

                "corruption_loss":
                    corruption_loss
            }
        )


    # --------------------------------------------------------
    # Tender-level results
    # --------------------------------------------------------

    tender_results = pd.DataFrame(
        tender_records
    )


    # --------------------------------------------------------
    # Aggregate results
    # --------------------------------------------------------

    honest_public_value = (
        tender_results[
            "honest_public_value"
        ].sum()
    )

    final_public_value = (
        tender_results[
            "final_public_value"
        ].sum()
    )

    corruption_loss = (
        tender_results[
            "corruption_loss"
        ].sum()
    )


    corruption_attempts = int(
        tender_results[
            "corruption_attempted"
        ].sum()
    )

    accepted_bribes = int(
        tender_results[
            "corruption_accepted"
        ].sum()
    )

    distorted_awards = int(
        tender_results[
            "award_distorted"
        ].sum()
    )


    # --------------------------------------------------------
    # Firms willing to bribe
    # --------------------------------------------------------

    firms_willing_to_bribe = int(
        scenario_market[
            "willing_to_bribe"
        ].sum()
    )


    # --------------------------------------------------------
    # Loss percentage
    # --------------------------------------------------------

    loss_percentage = (
        corruption_loss
        / honest_public_value
        * 100
    )


    # --------------------------------------------------------
    # Accounting check
    # --------------------------------------------------------

    assert np.isclose(
        honest_public_value
        - final_public_value,
        corruption_loss
    )


    return {
        "sanction":
            sanction,

        "official_accept_payoff":
            official_accept_payoff,

        "official_prefers_accept":
            official_prefers_accept,

        "firms_willing_to_bribe":
            firms_willing_to_bribe,

        "corruption_attempts":
            corruption_attempts,

        "accepted_bribes":
            accepted_bribes,

        "distorted_awards":
            distorted_awards,

        "honest_public_value":
            honest_public_value,

        "final_public_value":
            final_public_value,

        "corruption_loss":
            corruption_loss,

        "loss_percentage":
            loss_percentage
    }


# ============================================================
# 7. RUN SANCTION SWEEP
# ============================================================

scenario_results = []


for sanction in SANCTION_VALUES:

    result = run_scenario(
        sanction=sanction
    )

    scenario_results.append(
        result
    )


results = pd.DataFrame(
    scenario_results
)


# ------------------------------------------------------------
# 8. VALIDATE HONEST BENCHMARK
# ------------------------------------------------------------

assert np.allclose(
    results[
        "honest_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ------------------------------------------------------------
# 9. VALIDATE BASELINE F = 100
# ------------------------------------------------------------

baseline_100 = (
    results[
        results["sanction"]
        == 100
    ]
    .iloc[0]
)


assert (
    baseline_100[
        "corruption_attempts"
    ]
    == 100
)

assert (
    baseline_100[
        "accepted_bribes"
    ]
    == 100
)

assert (
    baseline_100[
        "distorted_awards"
    ]
    == 100
)

assert np.isclose(
    baseline_100[
        "final_public_value"
    ],
    5653.88,
    atol=0.02
)

assert np.isclose(
    baseline_100[
        "corruption_loss"
    ],
    2543.17,
    atol=0.02
)


# ------------------------------------------------------------
# 10. VALIDATE OFFICIAL THRESHOLD F = 200
# ------------------------------------------------------------
#
# EU(Accept)
# = 20 - 0.10 * 200
# = 0
#
# With strict > 0:
# official rejects.
# ------------------------------------------------------------

threshold_200 = (
    results[
        results["sanction"]
        == 200
    ]
    .iloc[0]
)


assert np.isclose(
    threshold_200[
        "official_accept_payoff"
    ],
    0
)

assert (
    bool(
        threshold_200[
            "official_prefers_accept"
        ]
    )
    is False
)

assert (
    threshold_200[
        "accepted_bribes"
    ]
    == 0
)

assert (
    threshold_200[
        "distorted_awards"
    ]
    == 0
)

assert np.isclose(
    threshold_200[
        "final_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ============================================================
# 11. SAVE RESULTS
# ============================================================

results.to_csv(
    "results/sanction_policy_sweep.csv",
    index=False
)


# ============================================================
# 12. FIGURE — CORRUPTION VS SANCTION
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    results["sanction"],
    results["corruption_attempts"],
    marker="o",
    label="Corruption attempts"
)

plt.plot(
    results["sanction"],
    results["accepted_bribes"],
    marker="o",
    label="Accepted bribes"
)

plt.plot(
    results["sanction"],
    results["distorted_awards"],
    marker="o",
    label="Distorted awards"
)

plt.axvline(
    200,
    linestyle="--",
    label="Official threshold (F = 200)"
)

plt.xlabel(
    "Sanction"
)

plt.ylabel(
    "Number of tenders"
)

plt.title(
    "Kairos Corruption Lab — "
    "Corruption Activity vs Sanction"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "corruption_vs_sanction.png",
    dpi=300
)

plt.close()


# ============================================================
# 13. FIGURE — PUBLIC VALUE VS SANCTION
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    results["sanction"],
    results["final_public_value"],
    marker="o",
    label="Observed Public Value"
)

plt.axhline(
    HONEST_PUBLIC_VALUE_EXPECTED,
    linestyle="--",
    label="Honest benchmark"
)

plt.axvline(
    200,
    linestyle="--",
    label="Official threshold (F = 200)"
)

plt.xlabel(
    "Sanction"
)

plt.ylabel(
    "Total Public Value"
)

plt.title(
    "Kairos Corruption Lab — "
    "Public Value vs Sanction"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "public_value_vs_sanction.png",
    dpi=300
)

plt.close()


# ============================================================
# 14. FIGURE — FIRMS WILLING TO BRIBE
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    results["sanction"],
    results["firms_willing_to_bribe"],
    marker="o"
)

plt.axvline(
    200,
    linestyle="--",
    label="Official threshold (F = 200)"
)

plt.xlabel(
    "Sanction"
)

plt.ylabel(
    "Firms willing to bribe"
)

plt.title(
    "Kairos Corruption Lab — "
    "Firm Incentives vs Sanction"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "firms_willing_vs_sanction.png",
    dpi=300
)

plt.close()


# ============================================================
# 15. FIGURE — CORRUPTION LOSS VS SANCTION
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    results["sanction"],
    results["corruption_loss"],
    marker="o"
)

plt.axvline(
    200,
    linestyle="--",
    label="Official threshold (F = 200)"
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Sanction"
)

plt.ylabel(
    "Total Public Value Loss"
)

plt.title(
    "Kairos Corruption Lab — "
    "Corruption Loss vs Sanction"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "corruption_loss_vs_sanction.png",
    dpi=300
)

plt.close()


# ============================================================
# 16. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 92
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 7 — "
    "INSTITUTIONAL RESPONSE TO SANCTIONS"
)

print(
    "=" * 92
)


print(
    "\nFIXED PARAMETERS"
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
    f"Private profit margin: "
    f"{PRIVATE_PROFIT_MARGIN:.0%}"
)

print(
    f"Honest Public Value benchmark: "
    f"{HONEST_PUBLIC_VALUE_EXPECTED:.2f}"
)


print(
    "\n"
    + "=" * 92
)

print(
    "SANCTION POLICY SWEEP"
)

print(
    "=" * 92
)


print(
    f"{'F':>7} "
    f"{'EU Official':>12} "
    f"{'Firms willing':>14} "
    f"{'Attempts':>10} "
    f"{'Accepted':>10} "
    f"{'Distorted':>10} "
    f"{'Public Value':>14} "
    f"{'Loss':>10} "
    f"{'Loss %':>9}"
)


print(
    "-" * 110
)


for _, row in results.iterrows():

    print(
        f"{row['sanction']:>7.0f} "
        f"{row['official_accept_payoff']:>12.2f} "
        f"{int(row['firms_willing_to_bribe']):>14} "
        f"{int(row['corruption_attempts']):>10} "
        f"{int(row['accepted_bribes']):>10} "
        f"{int(row['distorted_awards']):>10} "
        f"{row['final_public_value']:>14.2f} "
        f"{row['corruption_loss']:>10.2f} "
        f"{row['loss_percentage']:>8.2f}%"
    )


print(
    "=" * 110
)


# ------------------------------------------------------------
# 17. KEY VALIDATIONS
# ------------------------------------------------------------

print(
    "\nKEY VALIDATIONS"
)


print(
    "\nF = 100 reproduces Experiment 5:"
)

print(
    f"Attempts: "
    f"{int(baseline_100['corruption_attempts'])}"
)

print(
    f"Accepted: "
    f"{int(baseline_100['accepted_bribes'])}"
)

print(
    f"Distorted: "
    f"{int(baseline_100['distorted_awards'])}"
)

print(
    f"Public Value: "
    f"{baseline_100['final_public_value']:.2f}"
)

print(
    f"Corruption Loss: "
    f"{baseline_100['corruption_loss']:.2f}"
)


print(
    "\nF = 200:"
)

print(
    f"Official EU(Accept): "
    f"{threshold_200['official_accept_payoff']:.2f}"
)

print(
    f"Accepted bribes: "
    f"{int(threshold_200['accepted_bribes'])}"
)

print(
    f"Distorted awards: "
    f"{int(threshold_200['distorted_awards'])}"
)

print(
    f"Public Value: "
    f"{threshold_200['final_public_value']:.2f}"
)


# ------------------------------------------------------------
# 18. FIRST SANCTION WHERE FIRM INCENTIVES FALL
# ------------------------------------------------------------

less_than_all_firms = (
    results[
        results[
            "firms_willing_to_bribe"
        ]
        < 500
    ]
)


if len(
    less_than_all_firms
) > 0:

    first_firm_response = (
        less_than_all_firms
        .iloc[0]
    )

    print(
        "\nFIRST OBSERVED FIRM RESPONSE"
    )

    print(
        f"Sanction: "
        f"{first_firm_response['sanction']:.0f}"
    )

    print(
        f"Firms still willing to bribe: "
        f"{int(first_firm_response['firms_willing_to_bribe'])}"
    )

else:

    print(
        "\nNo firm incentive response "
        "within the tested sanction range."
    )


# ------------------------------------------------------------
# 19. FIRST SANCTION WITH ZERO WILLING FIRMS
# ------------------------------------------------------------

zero_firms = (
    results[
        results[
            "firms_willing_to_bribe"
        ]
        == 0
    ]
)


if len(
    zero_firms
) > 0:

    first_zero_firms = (
        zero_firms
        .iloc[0]
    )

    print(
        "\nFIRST SANCTION WITH ZERO "
        "FIRMS WILLING TO BRIBE"
    )

    print(
        f"Sanction: "
        f"{first_zero_firms['sanction']:.0f}"
    )

else:

    print(
        "\nSome firms remain willing to bribe "
        "at the maximum tested sanction."
    )


print(
    "\nAll theoretical and accounting "
    "validations passed correctly."
)


# ============================================================
# 20. FILES GENERATED
# ============================================================

print(
    "\nFILES GENERATED"
)

print(
    "results/"
    "sanction_policy_sweep.csv"
)

print(
    "figures/"
    "corruption_vs_sanction.png"
)

print(
    "figures/"
    "public_value_vs_sanction.png"
)

print(
    "figures/"
    "firms_willing_vs_sanction.png"
)

print(
    "figures/"
    "corruption_loss_vs_sanction.png"
)


print(
    "\nExperiment 7 completed correctly."
)

print(
    "=" * 92
    + "\n"
)