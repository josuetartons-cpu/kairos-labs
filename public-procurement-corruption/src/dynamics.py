import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 9B — HETEROGENEOUS DYNAMIC ADAPTATION
#
# Objective:
#
# Study persistence of corruption attempts after an
# institutional reform when firms differ in their speed
# of behavioral adaptation.
#
# Rounds 1–50:
#     weak institutions
#
# Rounds 51–100:
#     stronger institutions
#
# Key distinction:
#
#     Effective corruption
#         vs.
#     Persistence of corruption attempts
#
# IMPORTANT:
#
# - This is NOT reinforcement learning.
# - This is NOT an empirical behavioral model.
# - Firm heterogeneity is deterministic and synthetic.
# - Results describe mechanisms inside the artificial economy.
# ============================================================


# ============================================================
# 1. GENERAL PARAMETERS
# ============================================================

N_ROUNDS = 100

REFORM_ROUND = 51


BRIBE = 20

PRIVATE_PROFIT_MARGIN = 0.20


# ============================================================
# 2. INSTITUTIONAL REGIMES
# ============================================================

# ------------------------------------------------------------
# PRE-REFORM
#
# Weak institutional environment.
#
# pF = 10
#
# Official payoff:
#
# 20 - 10 = 10 > 0
#
# Therefore corruption is accepted.
# ------------------------------------------------------------

PRE_REFORM_P = 0.10

PRE_REFORM_SANCTION = 100


# ------------------------------------------------------------
# POST-REFORM
#
# Deterrence frontier identified in previous experiments.
#
# pF = 20
#
# Official payoff:
#
# 20 - 20 = 0
#
# Under our strict > 0 convention, the official rejects.
# ------------------------------------------------------------

POST_REFORM_P = 0.20

POST_REFORM_SANCTION = 100


# ============================================================
# 3. BEHAVIORAL PARAMETERS
# ============================================================

INITIAL_PROPENSITY = 0.50

MINIMUM_PROPENSITY = 0.25


# ------------------------------------------------------------
# Successful corruption reinforcement
# ------------------------------------------------------------

LAMBDA_SUCCESS = 0.25


# ------------------------------------------------------------
# Heterogeneous failure adaptation
#
# Every firm receives a deterministic learning rate between:
#
# 0.12 and 0.35
#
# Faster adapters reduce their propensity more rapidly after
# rejected corruption.
#
# Slower adapters persist for longer.
#
# This heterogeneity is synthetic.
# ------------------------------------------------------------

MIN_FAILURE_LAMBDA = 0.12

MAX_FAILURE_LAMBDA = 0.35


# ============================================================
# 4. HONEST BENCHMARK
# ============================================================

HONEST_PUBLIC_VALUE_EXPECTED = 8197.05


# ============================================================
# 5. LOAD SYNTHETIC PROCUREMENT MARKET
# ============================================================

market = pd.read_csv(
    "results/honest_market_all_bids.csv"
)


# ============================================================
# 6. VALIDATE MARKET
# ============================================================

assert len(market) == 500

assert market["tender_id"].nunique() == 100

assert (
    market
    .groupby("tender_id")
    .size()
    .eq(5)
    .all()
)


# ============================================================
# 7. PRIVATE PROFIT
# ============================================================

market[
    "private_profit"
] = (
    PRIVATE_PROFIT_MARGIN
    * market["price"]
)


# ============================================================
# 8. IDENTIFY PERMANENT HONEST WINNERS
# ============================================================
#
# The synthetic market is fixed across rounds.
#
# Therefore every tender has the same honest winner throughout
# the experiment.
# ============================================================

honest_winners = (
    market
    .sort_values(
        [
            "tender_id",
            "public_value"
        ],
        ascending=[
            True,
            False
        ]
    )
    .groupby(
        "tender_id",
        as_index=False
    )
    .first()
)


honest_winner_ids = set(
    honest_winners[
        "firm_id"
    ]
)


assert len(
    honest_winner_ids
) == 100


# ============================================================
# 9. IDENTIFY ELIGIBLE LOSING FIRMS
# ============================================================
#
# Only losing firms may attempt to distort the award.
#
# 500 total firms
# - 100 honest winners
# = 400 eligible losing firms
# ============================================================

eligible_losing_firm_ids = set(
    market.loc[
        ~market[
            "firm_id"
        ].isin(
            honest_winner_ids
        ),
        "firm_id"
    ]
)


assert len(
    eligible_losing_firm_ids
) == 400


# ============================================================
# 10. CREATE PERSISTENT FIRM STATES
# ============================================================

firm_states = (
    market[
        [
            "firm_id",
            "tender_id"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        "firm_id"
    )
    .reset_index(
        drop=True
    )
)


assert len(
    firm_states
) == 500


# ------------------------------------------------------------
# Initial propensity
# ------------------------------------------------------------

firm_states[
    "propensity_to_bribe"
] = INITIAL_PROPENSITY


# ------------------------------------------------------------
# Deterministic heterogeneous failure-learning rates
#
# No random draws are used.
# ------------------------------------------------------------

firm_states[
    "failure_lambda"
] = np.linspace(
    MIN_FAILURE_LAMBDA,
    MAX_FAILURE_LAMBDA,
    len(
        firm_states
    )
)


# ------------------------------------------------------------
# Eligibility indicator
# ------------------------------------------------------------

firm_states[
    "eligible_loser"
] = (
    firm_states[
        "firm_id"
    ]
    .isin(
        eligible_losing_firm_ids
    )
)


firm_states = (
    firm_states
    .set_index(
        "firm_id"
    )
)


# ============================================================
# 11. ADAPTATION FUNCTIONS
# ============================================================

def reinforce_success(
    current_propensity
):
    """
    Successful corruption increases future propensity.

    s_(t+1)
      =
    s_t + lambda_success * (1 - s_t)
    """

    new_propensity = (
        current_propensity
        +
        LAMBDA_SUCCESS
        * (
            1
            - current_propensity
        )
    )

    return min(
        1.0,
        new_propensity
    )


def reinforce_failure(
    current_propensity,
    failure_lambda
):
    """
    Failed corruption reduces future propensity.

    Firms differ in their failure-learning speed:

    s_(t+1)
      =
    s_t - lambda_i * s_t
    """

    new_propensity = (
        current_propensity
        -
        failure_lambda
        * current_propensity
    )

    return max(
        0.0,
        new_propensity
    )


# ============================================================
# 12. INSTITUTIONAL REGIME FUNCTION
# ============================================================

def get_institutional_regime(
    round_number
):

    if round_number < REFORM_ROUND:

        return {
            "regime":
                "Pre-reform",

            "p":
                PRE_REFORM_P,

            "sanction":
                PRE_REFORM_SANCTION
        }

    return {
        "regime":
            "Post-reform",

        "p":
            POST_REFORM_P,

        "sanction":
            POST_REFORM_SANCTION
    }


# ============================================================
# 13. STORAGE
# ============================================================

round_records = []

tender_records = []

propensity_records = []


# ============================================================
# 14. RUN REPEATED PROCUREMENT GAME
# ============================================================

for round_number in range(
    1,
    N_ROUNDS + 1
):

    # --------------------------------------------------------
    # Institutional environment
    # --------------------------------------------------------

    regime = get_institutional_regime(
        round_number
    )

    p = regime["p"]

    sanction = regime["sanction"]


    expected_penalty = (
        p
        * sanction
    )


    # --------------------------------------------------------
    # Official incentive
    # --------------------------------------------------------

    official_accept_payoff = (
        BRIBE
        -
        expected_penalty
    )


    official_accepts = (
        official_accept_payoff
        > 0
    )


    # ========================================================
    # ROUND COUNTERS
    # ========================================================

    round_attempts = 0

    round_accepted = 0

    round_distorted = 0

    round_public_value = 0.0

    round_honest_public_value = 0.0


    # ========================================================
    # PROCESS 100 TENDERS
    # ========================================================

    for tender_id, tender_df in (
        market
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
                [
                    "public_value",
                    "firm_id"
                ],
                ascending=[
                    False,
                    True
                ]
            )
            .iloc[0]
        )


        honest_public_value = float(
            honest_winner[
                "public_value"
            ]
        )


        round_honest_public_value += (
            honest_public_value
        )


        # ----------------------------------------------------
        # Losing firms only
        # ----------------------------------------------------

        losing_firms = (
            tender_df[
                tender_df[
                    "firm_id"
                ]
                != honest_winner[
                    "firm_id"
                ]
            ]
            .copy()
        )


        assert len(
            losing_firms
        ) == 4


        # ----------------------------------------------------
        # Persistent behavioral states
        # ----------------------------------------------------

        losing_firms[
            "propensity_to_bribe"
        ] = (
            losing_firms[
                "firm_id"
            ]
            .map(
                firm_states[
                    "propensity_to_bribe"
                ]
            )
        )


        losing_firms[
            "failure_lambda"
        ] = (
            losing_firms[
                "firm_id"
            ]
            .map(
                firm_states[
                    "failure_lambda"
                ]
            )
        )


        # ----------------------------------------------------
        # Economic corruption payoff
        # ----------------------------------------------------

        losing_firms[
            "bribe_payoff"
        ] = (
            losing_firms[
                "private_profit"
            ]
            -
            BRIBE
            -
            expected_penalty
        )


        # ----------------------------------------------------
        # Economic willingness
        # ----------------------------------------------------

        losing_firms[
            "economically_willing"
        ] = (
            losing_firms[
                "bribe_payoff"
            ]
            > 0
        )


        # ----------------------------------------------------
        # Behavioral willingness
        # ----------------------------------------------------

        losing_firms[
            "behaviorally_willing"
        ] = (
            losing_firms[
                "propensity_to_bribe"
            ]
            >= MINIMUM_PROPENSITY
        )


        # ----------------------------------------------------
        # Active corruption candidates
        # ----------------------------------------------------

        candidates = (
            losing_firms[
                losing_firms[
                    "economically_willing"
                ]
                &
                losing_firms[
                    "behaviorally_willing"
                ]
            ]
            .copy()
        )


        # ----------------------------------------------------
        # Strategic score
        #
        # Economic gain multiplied by behavioral propensity.
        # ----------------------------------------------------

        candidates[
            "strategic_score"
        ] = (
            candidates[
                "bribe_payoff"
            ]
            *
            candidates[
                "propensity_to_bribe"
            ]
        )


        # ====================================================
        # DEFAULT OUTCOME
        # ====================================================

        final_winner = honest_winner

        corruption_attempted = False

        corruption_accepted = False

        award_distorted = False

        corrupt_firm_id = None

        candidate_propensity_before = np.nan

        candidate_propensity_after = np.nan

        candidate_failure_lambda = np.nan


        # ====================================================
        # CORRUPTION ATTEMPT
        # ====================================================

        if len(
            candidates
        ) > 0:

            corruption_attempted = True

            round_attempts += 1


            # ------------------------------------------------
            # Strongest strategic candidate
            # ------------------------------------------------

            corrupt_candidate = (
                candidates
                .sort_values(
                    [
                        "strategic_score",
                        "bribe_payoff",
                        "firm_id"
                    ],
                    ascending=[
                        False,
                        False,
                        True
                    ]
                )
                .iloc[0]
            )


            corrupt_firm_id = (
                corrupt_candidate[
                    "firm_id"
                ]
            )


            candidate_propensity_before = float(
                firm_states
                .loc[
                    corrupt_firm_id,
                    "propensity_to_bribe"
                ]
            )


            candidate_failure_lambda = float(
                firm_states
                .loc[
                    corrupt_firm_id,
                    "failure_lambda"
                ]
            )


            # =================================================
            # OFFICIAL ACCEPTS
            # =================================================

            if official_accepts:

                corruption_accepted = True

                round_accepted += 1


                final_winner = (
                    corrupt_candidate
                )


                award_distorted = (
                    final_winner[
                        "firm_id"
                    ]
                    != honest_winner[
                        "firm_id"
                    ]
                )


                if award_distorted:

                    round_distorted += 1


                updated_propensity = (
                    reinforce_success(
                        candidate_propensity_before
                    )
                )


            # =================================================
            # OFFICIAL REJECTS
            # =================================================

            else:

                updated_propensity = (
                    reinforce_failure(
                        candidate_propensity_before,
                        candidate_failure_lambda
                    )
                )


            # ------------------------------------------------
            # Store persistent state
            # ------------------------------------------------

            firm_states.loc[
                corrupt_firm_id,
                "propensity_to_bribe"
            ] = updated_propensity


            candidate_propensity_after = float(
                updated_propensity
            )


        # ====================================================
        # FINAL PUBLIC VALUE
        # ====================================================

        final_public_value = float(
            final_winner[
                "public_value"
            ]
        )


        round_public_value += (
            final_public_value
        )


        corruption_loss = (
            honest_public_value
            -
            final_public_value
        )


        if np.isclose(
            corruption_loss,
            0
        ):

            corruption_loss = 0.0


        assert corruption_loss >= 0


        # ====================================================
        # SAVE TENDER RECORD
        # ====================================================

        tender_records.append(
            {
                "round":
                    round_number,

                "regime":
                    regime[
                        "regime"
                    ],

                "p":
                    p,

                "sanction":
                    sanction,

                "expected_penalty":
                    expected_penalty,

                "tender_id":
                    tender_id,

                "honest_winner":
                    honest_winner[
                        "firm_id"
                    ],

                "final_winner":
                    final_winner[
                        "firm_id"
                    ],

                "corrupt_candidate":
                    corrupt_firm_id,

                "corruption_attempted":
                    corruption_attempted,

                "corruption_accepted":
                    corruption_accepted,

                "award_distorted":
                    award_distorted,

                "honest_public_value":
                    honest_public_value,

                "final_public_value":
                    final_public_value,

                "corruption_loss":
                    corruption_loss,

                "candidate_propensity_before":
                    candidate_propensity_before,

                "candidate_propensity_after":
                    candidate_propensity_after,

                "candidate_failure_lambda":
                    candidate_failure_lambda
            }
        )


    # ========================================================
    # END-OF-ROUND BEHAVIORAL METRICS
    # ========================================================

    all_average_propensity = float(
        firm_states[
            "propensity_to_bribe"
        ]
        .mean()
    )


    eligible_states = (
        firm_states[
            firm_states[
                "eligible_loser"
            ]
        ]
    )


    eligible_average_propensity = float(
        eligible_states[
            "propensity_to_bribe"
        ]
        .mean()
    )


    eligible_median_propensity = float(
        eligible_states[
            "propensity_to_bribe"
        ]
        .median()
    )


    # --------------------------------------------------------
    # All firms above threshold
    #
    # Includes honest winners.
    # Kept only as a descriptive statistic.
    # --------------------------------------------------------

    all_firms_above_threshold = int(
        (
            firm_states[
                "propensity_to_bribe"
            ]
            >= MINIMUM_PROPENSITY
        )
        .sum()
    )


    # --------------------------------------------------------
    # Eligible losing firms above threshold
    #
    # This is the economically relevant behavioral metric.
    # --------------------------------------------------------

    eligible_losing_firms_above_threshold = int(
        (
            eligible_states[
                "propensity_to_bribe"
            ]
            >= MINIMUM_PROPENSITY
        )
        .sum()
    )


    round_corruption_loss = (
        round_honest_public_value
        -
        round_public_value
    )


    if np.isclose(
        round_corruption_loss,
        0
    ):

        round_corruption_loss = 0.0


    # --------------------------------------------------------
    # Accounting validation
    # --------------------------------------------------------

    assert np.isclose(
        round_honest_public_value
        -
        round_public_value,
        round_corruption_loss
    )


    round_records.append(
        {
            "round":
                round_number,

            "regime":
                regime[
                    "regime"
                ],

            "p":
                p,

            "sanction":
                sanction,

            "expected_penalty":
                expected_penalty,

            "official_accept_payoff":
                official_accept_payoff,

            "corruption_attempts":
                round_attempts,

            "accepted_bribes":
                round_accepted,

            "distorted_awards":
                round_distorted,

            "honest_public_value":
                round_honest_public_value,

            "final_public_value":
                round_public_value,

            "corruption_loss":
                round_corruption_loss,

            "all_average_propensity":
                all_average_propensity,

            "eligible_average_propensity":
                eligible_average_propensity,

            "eligible_median_propensity":
                eligible_median_propensity,

            "all_firms_above_threshold":
                all_firms_above_threshold,

            "eligible_losing_firms_above_threshold":
                eligible_losing_firms_above_threshold
        }
    )


    # ========================================================
    # FIRM STATE SNAPSHOT
    # ========================================================

    snapshot = (
        firm_states
        .reset_index()
        .copy()
    )


    snapshot[
        "round"
    ] = round_number


    snapshot[
        "regime"
    ] = regime[
        "regime"
    ]


    propensity_records.append(
        snapshot
    )


# ============================================================
# 15. BUILD DATAFRAMES
# ============================================================

round_results = pd.DataFrame(
    round_records
)


tender_results = pd.DataFrame(
    tender_records
)


propensity_results = pd.concat(
    propensity_records,
    ignore_index=True
)


# ============================================================
# 16. CORE VALIDATIONS
# ============================================================

assert len(
    round_results
) == 100


assert len(
    tender_results
) == 10000


assert len(
    propensity_results
) == 50000


# ------------------------------------------------------------
# Honest benchmark constant through time
# ------------------------------------------------------------

assert np.allclose(
    round_results[
        "honest_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ------------------------------------------------------------
# Round 1
# ------------------------------------------------------------

round_1 = (
    round_results[
        round_results[
            "round"
        ]
        == 1
    ]
    .iloc[0]
)


assert (
    round_1[
        "accepted_bribes"
    ]
    == 100
)


assert (
    round_1[
        "distorted_awards"
    ]
    == 100
)


# ------------------------------------------------------------
# Round 50
# ------------------------------------------------------------

round_50 = (
    round_results[
        round_results[
            "round"
        ]
        == 50
    ]
    .iloc[0]
)


assert (
    round_50[
        "accepted_bribes"
    ]
    == 100
)


assert (
    round_50[
        "distorted_awards"
    ]
    == 100
)


# ------------------------------------------------------------
# Reform round
# ------------------------------------------------------------

round_51 = (
    round_results[
        round_results[
            "round"
        ]
        == REFORM_ROUND
    ]
    .iloc[0]
)


assert np.isclose(
    round_51[
        "official_accept_payoff"
    ],
    0
)


assert (
    round_51[
        "accepted_bribes"
    ]
    == 0
)


assert (
    round_51[
        "distorted_awards"
    ]
    == 0
)


assert np.isclose(
    round_51[
        "final_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ------------------------------------------------------------
# Round 100
# ------------------------------------------------------------

round_100 = (
    round_results[
        round_results[
            "round"
        ]
        == 100
    ]
    .iloc[0]
)


assert (
    round_100[
        "accepted_bribes"
    ]
    == 0
)


assert (
    round_100[
        "distorted_awards"
    ]
    == 0
)


# ============================================================
# 17. ADAPTATION MILESTONES
# ============================================================

post_reform = (
    round_results[
        round_results[
            "round"
        ]
        >= REFORM_ROUND
    ]
    .copy()
)


# ------------------------------------------------------------
# First decline in aggregate attempts
# ------------------------------------------------------------

reduced_attempts = (
    post_reform[
        post_reform[
            "corruption_attempts"
        ]
        < 100
    ]
)


if len(
    reduced_attempts
) > 0:

    first_reduced_attempt_round = int(
        reduced_attempts
        .iloc[0][
            "round"
        ]
    )

else:

    first_reduced_attempt_round = None


# ------------------------------------------------------------
# First zero-attempt round
# ------------------------------------------------------------

zero_attempts = (
    post_reform[
        post_reform[
            "corruption_attempts"
        ]
        == 0
    ]
)


if len(
    zero_attempts
) > 0:

    first_zero_attempt_round = int(
        zero_attempts
        .iloc[0][
            "round"
        ]
    )

else:

    first_zero_attempt_round = None


# ------------------------------------------------------------
# First round with fewer than 200 eligible losing firms
# above behavioral threshold
# ------------------------------------------------------------

half_behavioral_pool = (
    post_reform[
        post_reform[
            "eligible_losing_firms_above_threshold"
        ]
        < 200
    ]
)


if len(
    half_behavioral_pool
) > 0:

    first_below_half_pool_round = int(
        half_behavioral_pool
        .iloc[0][
            "round"
        ]
    )

else:

    first_below_half_pool_round = None


# ------------------------------------------------------------
# Behavioral adjustment delay
# ------------------------------------------------------------

if (
    first_zero_attempt_round
    is not None
):

    adjustment_delay = (
        first_zero_attempt_round
        -
        REFORM_ROUND
    )

else:

    adjustment_delay = np.nan


# ============================================================
# 18. PERIOD SUMMARY
# ============================================================

period_summary = (
    round_results
    .groupby(
        "regime"
    )
    .agg(
        rounds=(
            "round",
            "count"
        ),

        total_attempts=(
            "corruption_attempts",
            "sum"
        ),

        total_accepted=(
            "accepted_bribes",
            "sum"
        ),

        total_distorted=(
            "distorted_awards",
            "sum"
        ),

        total_corruption_loss=(
            "corruption_loss",
            "sum"
        ),

        average_public_value=(
            "final_public_value",
            "mean"
        ),

        average_eligible_propensity=(
            "eligible_average_propensity",
            "mean"
        ),

        average_eligible_firms_above_threshold=(
            "eligible_losing_firms_above_threshold",
            "mean"
        )
    )
    .reset_index()
)


# ============================================================
# 19. SAVE RESULTS
# ============================================================

round_results.to_csv(
    "results/"
    "dynamic_round_results.csv",
    index=False
)


tender_results.to_csv(
    "results/"
    "dynamic_tender_results.csv",
    index=False
)


propensity_results.to_csv(
    "results/"
    "dynamic_firm_propensities.csv",
    index=False
)


period_summary.to_csv(
    "results/"
    "dynamic_period_summary.csv",
    index=False
)


# ============================================================
# 20. FIGURE — CORRUPTION ATTEMPTS
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "corruption_attempts"
    ],
    label="Corruption attempts"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Tenders with corruption attempts"
)

plt.title(
    "Kairos Corruption Lab — "
    "Persistence of Corruption Attempts After Reform"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_corruption_attempts.png",
    dpi=300
)


plt.close()


# ============================================================
# 21. FIGURE — ACCEPTED BRIBES
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "accepted_bribes"
    ],
    label="Accepted bribes"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Accepted bribes"
)

plt.title(
    "Kairos Corruption Lab — "
    "Effective Corruption Before and After Reform"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_accepted_bribes.png",
    dpi=300
)


plt.close()


# ============================================================
# 22. FIGURE — PUBLIC VALUE
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "final_public_value"
    ],
    label="Observed Public Value"
)


plt.axhline(
    HONEST_PUBLIC_VALUE_EXPECTED,
    linestyle="--",
    label="Honest benchmark"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Public Value"
)

plt.title(
    "Kairos Corruption Lab — "
    "Public Value Through Institutional Reform"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_public_value.png",
    dpi=300
)


plt.close()


# ============================================================
# 23. FIGURE — ELIGIBLE AVERAGE PROPENSITY
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "eligible_average_propensity"
    ],
    label="Eligible losing firms"
)


plt.axhline(
    MINIMUM_PROPENSITY,
    linestyle="--",
    label="Attempt threshold"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Average propensity to bribe"
)

plt.title(
    "Kairos Corruption Lab — "
    "Adaptive Corruption Propensity Among Eligible Firms"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_average_propensity.png",
    dpi=300
)


plt.close()


# ============================================================
# 24. FIGURE — ELIGIBLE LOSING FIRMS ABOVE THRESHOLD
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "eligible_losing_firms_above_threshold"
    ],
    label="Eligible losing firms above threshold"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Eligible firms"
)

plt.title(
    "Kairos Corruption Lab — "
    "Behavioral Persistence Among Eligible Losing Firms"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_eligible_firms_above_threshold.png",
    dpi=300
)


plt.close()


# ============================================================
# 25. FIGURE — ALL VS ELIGIBLE FIRMS
# ============================================================

plt.figure(
    figsize=(11, 7)
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "all_firms_above_threshold"
    ],
    label="All firms above threshold"
)


plt.plot(
    round_results[
        "round"
    ],
    round_results[
        "eligible_losing_firms_above_threshold"
    ],
    label="Eligible losing firms above threshold"
)


plt.axvline(
    REFORM_ROUND,
    linestyle="--",
    label="Institutional reform"
)


plt.xlabel(
    "Round"
)

plt.ylabel(
    "Number of firms"
)

plt.title(
    "Kairos Corruption Lab — "
    "All Firms vs Corruption-Eligible Firms"
)

plt.legend()

plt.tight_layout()


plt.savefig(
    "figures/"
    "dynamic_all_vs_eligible_firms.png",
    dpi=300
)


plt.close()


# ============================================================
# 26. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 108
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 9B — "
    "HETEROGENEOUS DYNAMIC ADAPTATION"
)

print(
    "=" * 108
)


# ============================================================
# 27. DYNAMIC DESIGN
# ============================================================

print(
    "\nDYNAMIC DESIGN"
)


print(
    f"Rounds: "
    f"{N_ROUNDS}"
)


print(
    f"Reform begins: "
    f"round {REFORM_ROUND}"
)


print(
    f"Total firms: "
    f"{len(firm_states)}"
)


print(
    f"Permanent honest winners: "
    f"{len(honest_winner_ids)}"
)


print(
    f"Eligible losing firms: "
    f"{len(eligible_losing_firm_ids)}"
)


print(
    f"Initial propensity: "
    f"{INITIAL_PROPENSITY:.2f}"
)


print(
    f"Minimum propensity for attempt: "
    f"{MINIMUM_PROPENSITY:.2f}"
)


print(
    f"Success learning rate: "
    f"{LAMBDA_SUCCESS:.2f}"
)


print(
    f"Failure learning-rate range: "
    f"{MIN_FAILURE_LAMBDA:.2f}–"
    f"{MAX_FAILURE_LAMBDA:.2f}"
)


# ============================================================
# 28. INSTITUTIONAL REGIMES
# ============================================================

print(
    "\nINSTITUTIONAL REGIMES"
)


print(
    f"Pre-reform: "
    f"p={PRE_REFORM_P:.0%}, "
    f"F={PRE_REFORM_SANCTION}, "
    f"pF="
    f"{PRE_REFORM_P * PRE_REFORM_SANCTION:.2f}"
)


print(
    f"Post-reform: "
    f"p={POST_REFORM_P:.0%}, "
    f"F={POST_REFORM_SANCTION}, "
    f"pF="
    f"{POST_REFORM_P * POST_REFORM_SANCTION:.2f}"
)


# ============================================================
# 29. KEY ROUNDS
# ============================================================

print(
    "\n"
    + "=" * 108
)

print(
    "KEY ROUNDS"
)

print(
    "=" * 108
)


key_rounds = (
    round_results[
        round_results[
            "round"
        ]
        .isin(
            [
                1,
                25,
                50,
                51,
                52,
                55,
                60,
                65,
                70,
                75,
                80,
                90,
                100
            ]
        )
    ]
)


print(
    key_rounds[
        [
            "round",
            "regime",
            "corruption_attempts",
            "accepted_bribes",
            "distorted_awards",
            "final_public_value",
            "eligible_average_propensity",
            "eligible_losing_firms_above_threshold"
        ]
    ]
    .to_string(
        index=False,
        formatters={
            "final_public_value":
                "{:.2f}".format,

            "eligible_average_propensity":
                "{:.3f}".format
        }
    )
)


# ============================================================
# 30. ADAPTATION MILESTONES
# ============================================================

print(
    "\n"
    + "=" * 108
)

print(
    "ADAPTATION MILESTONES"
)

print(
    "=" * 108
)


print(
    f"First post-reform round "
    f"with fewer than 100 attempts: "
    f"{first_reduced_attempt_round}"
)


print(
    f"First post-reform round "
    f"with fewer than 200 eligible losing firms "
    f"above threshold: "
    f"{first_below_half_pool_round}"
)


print(
    f"First post-reform round "
    f"with zero attempts: "
    f"{first_zero_attempt_round}"
)


print(
    f"Adjustment delay after reform: "
    f"{adjustment_delay} rounds"
)


# ============================================================
# 31. PERIOD SUMMARY
# ============================================================

print(
    "\n"
    + "=" * 108
)

print(
    "PERIOD SUMMARY"
)

print(
    "=" * 108
)


print(
    period_summary
    .to_string(
        index=False,
        formatters={
            "total_corruption_loss":
                "{:.2f}".format,

            "average_public_value":
                "{:.2f}".format,

            "average_eligible_propensity":
                "{:.3f}".format,

            "average_eligible_firms_above_threshold":
                "{:.1f}".format
        }
    )
)


# ============================================================
# 32. FINAL ROUND BEHAVIOR
# ============================================================

print(
    "\n"
    + "=" * 108
)

print(
    "FINAL BEHAVIORAL STATE"
)

print(
    "=" * 108
)


print(
    f"Round 100 corruption attempts: "
    f"{int(round_100['corruption_attempts'])}"
)


print(
    f"Round 100 accepted bribes: "
    f"{int(round_100['accepted_bribes'])}"
)


print(
    f"Round 100 eligible average propensity: "
    f"{round_100['eligible_average_propensity']:.3f}"
)


print(
    f"Round 100 eligible losing firms "
    f"above threshold: "
    f"{int(round_100['eligible_losing_firms_above_threshold'])}"
)


# ============================================================
# 33. VALIDATIONS
# ============================================================

print(
    "\nVALIDATIONS"
)


print(
    "Pre-reform corruption remains strategically effective."
)


print(
    "Accepted corruption falls immediately to zero "
    "at the reform."
)


print(
    "Behavioral adaptation is measured only among "
    "corruption-eligible losing firms."
)


print(
    "Firm adaptation speeds are heterogeneous but "
    "fully deterministic."
)


print(
    "All theoretical and accounting validations passed."
)


# ============================================================
# 34. IMPORTANT WARNING
# ============================================================

print(
    "\nIMPORTANT"
)


print(
    "The behavioral adaptation mechanism and heterogeneous "
    "learning rates are synthetic assumptions."
)


print(
    "They are used to study persistence and adaptation "
    "mechanisms, not to estimate real-world behavior."
)


# ============================================================
# 35. FILES GENERATED
# ============================================================

print(
    "\nFILES GENERATED"
)


print(
    "results/"
    "dynamic_round_results.csv"
)


print(
    "results/"
    "dynamic_tender_results.csv"
)


print(
    "results/"
    "dynamic_firm_propensities.csv"
)


print(
    "results/"
    "dynamic_period_summary.csv"
)


print()


print(
    "figures/"
    "dynamic_corruption_attempts.png"
)


print(
    "figures/"
    "dynamic_accepted_bribes.png"
)


print(
    "figures/"
    "dynamic_public_value.png"
)


print(
    "figures/"
    "dynamic_average_propensity.png"
)


print(
    "figures/"
    "dynamic_eligible_firms_above_threshold.png"
)


print(
    "figures/"
    "dynamic_all_vs_eligible_firms.png"
)


print(
    "\nExperiment 9B completed correctly."
)


print(
    "=" * 108
    + "\n"
)