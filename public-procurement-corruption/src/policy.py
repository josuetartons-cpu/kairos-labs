import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 8A — COMBINED INSTITUTIONAL POLICY
#
# Detection probability p and sanction F vary simultaneously.
#
# Objectives:
# 1. Map corruption outcomes over (p, F).
# 2. Validate combinations with equal expected penalty pF.
# 3. Measure Public Value over the full institutional grid.
#
# IMPORTANT:
# No institutional cost is included yet.
# ============================================================


# ------------------------------------------------------------
# 1. FIXED PARAMETERS
# ------------------------------------------------------------

BRIBE = 20

PRIVATE_PROFIT_MARGIN = 0.20

HONEST_PUBLIC_VALUE_EXPECTED = 8197.05


# ------------------------------------------------------------
# 2. POLICY GRID
# ------------------------------------------------------------
#
# Detection:
# 0%, 5%, 10%, ..., 100%
#
# Sanction:
# 0, 25, 50, ..., 2000
# ------------------------------------------------------------

DETECTION_VALUES = np.arange(
    0,
    1.0001,
    0.05
)

SANCTION_VALUES = np.arange(
    0,
    2000 + 25,
    25
)


# ------------------------------------------------------------
# 3. LOAD SAME PROCUREMENT MARKET
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
# 6. RUN ONE POLICY SCENARIO
# ------------------------------------------------------------

def run_policy(
    detection_probability,
    sanction
):
    """
    Run all 100 tenders for one institutional policy pair:

        (p, F)

    We use the same sanction F for firms and officials.
    """

    scenario_market = market.copy()


    # --------------------------------------------------------
    # Firm corruption payoff
    # --------------------------------------------------------

    scenario_market[
        "bribe_payoff"
    ] = (
        scenario_market[
            "private_profit"
        ]
        - BRIBE
        - detection_probability
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
        - detection_probability
        * sanction
    )

    official_prefers_accept = (
        official_accept_payoff > 0
    )


    # --------------------------------------------------------
    # Expected penalty
    # --------------------------------------------------------

    expected_penalty = (
        detection_probability
        * sanction
    )


    # --------------------------------------------------------
    # Process tenders
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
        # Losing firms
        # ----------------------------------------------------

        losing_firms = (
            tender_df[
                tender_df["firm_id"]
                != honest_winner["firm_id"]
            ]
            .copy()
        )


        # ----------------------------------------------------
        # Bribing candidates
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


        assert corruption_loss >= 0


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
    # Tender results
    # --------------------------------------------------------

    tender_results = pd.DataFrame(
        tender_records
    )


    # --------------------------------------------------------
    # Aggregate scenario
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


    firms_willing_to_bribe = int(
        scenario_market[
            "willing_to_bribe"
        ].sum()
    )


    loss_percentage = (
        corruption_loss
        / honest_public_value
        * 100
    )


    # --------------------------------------------------------
    # Accounting validation
    # --------------------------------------------------------

    assert np.isclose(
        honest_public_value
        - final_public_value,
        corruption_loss
    )


    return {
        "p":
            detection_probability,

        "sanction":
            sanction,

        "expected_penalty":
            expected_penalty,

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
# 7. RUN FULL POLICY GRID
# ============================================================

policy_records = []


for p in DETECTION_VALUES:

    for sanction in SANCTION_VALUES:

        result = run_policy(
            detection_probability=p,
            sanction=sanction
        )

        policy_records.append(
            result
        )


results = pd.DataFrame(
    policy_records
)


# ------------------------------------------------------------
# 8. CLEAN p REPRESENTATION
# ------------------------------------------------------------

results["p"] = (
    results["p"]
    .round(2)
)


# ------------------------------------------------------------
# 9. VALIDATE HONEST COUNTERFACTUAL
# ------------------------------------------------------------

assert np.allclose(
    results[
        "honest_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ============================================================
# 10. VALIDATE BASELINE
# ============================================================
#
# p = 10%, F = 100
#
# Must reproduce Experiment 5.
# ============================================================

baseline = (
    results[
        np.isclose(
            results["p"],
            0.10
        )
        &
        (
            results["sanction"]
            == 100
        )
    ]
    .iloc[0]
)


assert (
    baseline[
        "corruption_attempts"
    ]
    == 100
)

assert (
    baseline[
        "accepted_bribes"
    ]
    == 100
)

assert (
    baseline[
        "distorted_awards"
    ]
    == 100
)

assert np.isclose(
    baseline[
        "final_public_value"
    ],
    5653.88,
    atol=0.02
)

assert np.isclose(
    baseline[
        "corruption_loss"
    ],
    2543.17,
    atol=0.02
)


# ============================================================
# 11. EQUIVALENT POLICY TESTS
# ============================================================
#
# These policies all satisfy:
#
# pF = 20
#
# Therefore:
#
# EU_official(Accept) = 0
#
# Under strict > 0:
# official rejects.
# ============================================================

equivalent_policies = [
    (0.10, 200),
    (0.20, 100),
    (0.40, 50)
]


equivalent_records = []


for p, sanction in equivalent_policies:

    row = (
        results[
            np.isclose(
                results["p"],
                p
            )
            &
            (
                results["sanction"]
                == sanction
            )
        ]
        .iloc[0]
    )


    assert np.isclose(
        row[
            "expected_penalty"
        ],
        20
    )

    assert np.isclose(
        row[
            "official_accept_payoff"
        ],
        0
    )

    assert (
        row[
            "accepted_bribes"
        ]
        == 0
    )

    assert (
        row[
            "distorted_awards"
        ]
        == 0
    )

    assert np.isclose(
        row[
            "final_public_value"
        ],
        HONEST_PUBLIC_VALUE_EXPECTED,
        atol=0.02
    )


    equivalent_records.append(
        {
            "p":
                p,

            "sanction":
                sanction,

            "expected_penalty":
                row[
                    "expected_penalty"
                ],

            "firms_willing_to_bribe":
                int(
                    row[
                        "firms_willing_to_bribe"
                    ]
                ),

            "accepted_bribes":
                int(
                    row[
                        "accepted_bribes"
                    ]
                ),

            "public_value":
                row[
                    "final_public_value"
                ]
        }
    )


equivalent_df = pd.DataFrame(
    equivalent_records
)


# ============================================================
# 12. SAVE RESULTS
# ============================================================

results.to_csv(
    "results/policy_grid.csv",
    index=False
)

equivalent_df.to_csv(
    "results/equivalent_policies.csv",
    index=False
)


# ============================================================
# 13. BUILD MATRICES FOR HEATMAPS
# ============================================================

distorted_matrix = (
    results
    .pivot(
        index="sanction",
        columns="p",
        values="distorted_awards"
    )
)


public_value_matrix = (
    results
    .pivot(
        index="sanction",
        columns="p",
        values="final_public_value"
    )
)


loss_matrix = (
    results
    .pivot(
        index="sanction",
        columns="p",
        values="corruption_loss"
    )
)


firms_matrix = (
    results
    .pivot(
        index="sanction",
        columns="p",
        values="firms_willing_to_bribe"
    )
)


# ============================================================
# 14. FIGURE — DISTORTED AWARDS POLICY MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    distorted_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        DETECTION_VALUES.min(),
        DETECTION_VALUES.max(),
        SANCTION_VALUES.min(),
        SANCTION_VALUES.max()
    ]
)

plt.xlabel(
    "Probability of detection"
)

plt.ylabel(
    "Sanction"
)

plt.title(
    "Kairos Corruption Lab — "
    "Distorted Awards Across Institutional Policies"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "policy_distorted_awards_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 15. FIGURE — PUBLIC VALUE POLICY MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    public_value_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        DETECTION_VALUES.min(),
        DETECTION_VALUES.max(),
        SANCTION_VALUES.min(),
        SANCTION_VALUES.max()
    ]
)

plt.xlabel(
    "Probability of detection"
)

plt.ylabel(
    "Sanction"
)

plt.title(
    "Kairos Corruption Lab — "
    "Public Value Across Institutional Policies"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "policy_public_value_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 16. FIGURE — CORRUPTION LOSS POLICY MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    loss_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        DETECTION_VALUES.min(),
        DETECTION_VALUES.max(),
        SANCTION_VALUES.min(),
        SANCTION_VALUES.max()
    ]
)

plt.xlabel(
    "Probability of detection"
)

plt.ylabel(
    "Sanction"
)

plt.title(
    "Kairos Corruption Lab — "
    "Corruption Loss Across Institutional Policies"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "policy_corruption_loss_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 17. FIGURE — FIRM INCENTIVES POLICY MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    firms_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        DETECTION_VALUES.min(),
        DETECTION_VALUES.max(),
        SANCTION_VALUES.min(),
        SANCTION_VALUES.max()
    ]
)

plt.xlabel(
    "Probability of detection"
)

plt.ylabel(
    "Sanction"
)

plt.title(
    "Kairos Corruption Lab — "
    "Firms Willing to Bribe"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "policy_firms_willing_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 18. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 92
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 8A — "
    "COMBINED DETECTION × SANCTION POLICY"
)

print(
    "=" * 92
)


print(
    "\nPOLICY GRID"
)

print(
    f"Detection values: "
    f"{len(DETECTION_VALUES)}"
)

print(
    f"Sanction values: "
    f"{len(SANCTION_VALUES)}"
)

print(
    f"Total policy scenarios: "
    f"{len(results)}"
)

print(
    f"Honest Public Value benchmark: "
    f"{HONEST_PUBLIC_VALUE_EXPECTED:.2f}"
)


# ------------------------------------------------------------
# 19. BASELINE
# ------------------------------------------------------------

print(
    "\nBASELINE POLICY"
)

print(
    "p = 10%, F = 100"
)

print(
    f"Expected penalty pF: "
    f"{baseline['expected_penalty']:.2f}"
)

print(
    f"Firms willing to bribe: "
    f"{int(baseline['firms_willing_to_bribe'])}"
)

print(
    f"Accepted bribes: "
    f"{int(baseline['accepted_bribes'])}"
)

print(
    f"Distorted awards: "
    f"{int(baseline['distorted_awards'])}"
)

print(
    f"Public Value: "
    f"{baseline['final_public_value']:.2f}"
)

print(
    f"Corruption Loss: "
    f"{baseline['corruption_loss']:.2f}"
)


# ------------------------------------------------------------
# 20. EQUIVALENT POLICIES
# ------------------------------------------------------------

print(
    "\n"
    + "=" * 92
)

print(
    "EQUIVALENT POLICIES — pF = 20"
)

print(
    "=" * 92
)


print(
    equivalent_df
    .to_string(
        index=False,
        formatters={
            "p":
                "{:.0%}".format,

            "expected_penalty":
                "{:.2f}".format,

            "public_value":
                "{:.2f}".format
        }
    )
)


# ------------------------------------------------------------
# 21. POLICY REGIME COUNTS
# ------------------------------------------------------------

corrupt_policy_count = int(
    (
        results[
            "distorted_awards"
        ]
        > 0
    )
    .sum()
)

clean_policy_count = int(
    (
        results[
            "distorted_awards"
        ]
        == 0
    )
    .sum()
)


print(
    "\nPOLICY REGIMES"
)

print(
    f"Scenarios with distorted awards: "
    f"{corrupt_policy_count}"
)

print(
    f"Scenarios with zero distorted awards: "
    f"{clean_policy_count}"
)


# ------------------------------------------------------------
# 22. VALIDATION MESSAGE
# ------------------------------------------------------------

print(
    "\nAll theoretical, market, and accounting "
    "validations passed correctly."
)


# ============================================================
# 23. FILES GENERATED
# ============================================================

print(
    "\nFILES GENERATED"
)

print(
    "results/"
    "policy_grid.csv"
)

print(
    "results/"
    "equivalent_policies.csv"
)

print()

print(
    "figures/"
    "policy_distorted_awards_map.png"
)

print(
    "figures/"
    "policy_public_value_map.png"
)

print(
    "figures/"
    "policy_corruption_loss_map.png"
)

print(
    "figures/"
    "policy_firms_willing_map.png"
)


print(
    "\nExperiment 8A completed correctly."
)

print(
    "=" * 92
    + "\n"
)