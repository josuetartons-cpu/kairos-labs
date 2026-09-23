import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 8B — INSTITUTIONAL COSTS
#
# Objective:
# Introduce synthetic institutional costs into the policy grid
# generated in Experiment 8A.
#
# We ask:
#
# Which combination of detection probability p and sanction F
# maximizes Net Public Value?
#
# IMPORTANT:
# These institutional costs are synthetic.
# They are NOT empirical estimates for Guatemala.
# ============================================================


# ------------------------------------------------------------
# 1. COST PARAMETERS
# ------------------------------------------------------------
#
# Detection cost:
#
# C_p(p) = ALPHA * p^2
#
# Detection becomes progressively more expensive.
#
#
# Sanction cost:
#
# C_F(F) = BETA * F
#
# Higher sanction regimes impose increasing institutional cost.
# ------------------------------------------------------------

ALPHA = 1000
BETA = 0.50


HONEST_PUBLIC_VALUE_EXPECTED = 8197.05


# ------------------------------------------------------------
# 2. LOAD POLICY GRID FROM EXPERIMENT 8A
# ------------------------------------------------------------

policies = pd.read_csv(
    "results/policy_grid.csv"
)


# ------------------------------------------------------------
# 3. VALIDATE POLICY GRID
# ------------------------------------------------------------

assert len(policies) == 1701

assert (
    policies["p"]
    .nunique()
    == 21
)

assert (
    policies["sanction"]
    .nunique()
    == 81
)

assert np.allclose(
    policies[
        "honest_public_value"
    ],
    HONEST_PUBLIC_VALUE_EXPECTED,
    atol=0.02
)


# ============================================================
# 4. INSTITUTIONAL COST FUNCTIONS
# ============================================================

def detection_cost(p):
    """
    Synthetic convex cost of detection.

    C_p(p) = ALPHA * p^2
    """

    return (
        ALPHA
        * p ** 2
    )


def sanction_cost(sanction):
    """
    Synthetic linear cost of sanctions.

    C_F(F) = BETA * F
    """

    return (
        BETA
        * sanction
    )


# ============================================================
# 5. CALCULATE COSTS FOR EVERY POLICY
# ============================================================

policies[
    "detection_cost"
] = detection_cost(
    policies["p"]
)


policies[
    "sanction_cost"
] = sanction_cost(
    policies["sanction"]
)


policies[
    "institutional_cost"
] = (
    policies[
        "detection_cost"
    ]
    +
    policies[
        "sanction_cost"
    ]
)


# ------------------------------------------------------------
# 6. NET PUBLIC VALUE
# ------------------------------------------------------------
#
# NetPV =
#
# Observed Public Value
# - Detection Cost
# - Sanction Cost
# ------------------------------------------------------------

policies[
    "net_public_value"
] = (
    policies[
        "final_public_value"
    ]
    -
    policies[
        "institutional_cost"
    ]
)


# ============================================================
# 7. IDENTIFY OPTIMAL POLICY
# ============================================================

optimal_policy = (
    policies
    .sort_values(
        "net_public_value",
        ascending=False
    )
    .iloc[0]
)


# ============================================================
# 8. BEST POLICY WITH ZERO DISTORTED AWARDS
# ============================================================

clean_policies = (
    policies[
        policies[
            "distorted_awards"
        ]
        == 0
    ]
    .copy()
)


best_clean_policy = (
    clean_policies
    .sort_values(
        "net_public_value",
        ascending=False
    )
    .iloc[0]
)


# ============================================================
# 9. CHEAPEST POLICY WITH ZERO DISTORTED AWARDS
# ============================================================

cheapest_clean_policy = (
    clean_policies
    .sort_values(
        [
            "institutional_cost",
            "p",
            "sanction"
        ],
        ascending=True
    )
    .iloc[0]
)


# ============================================================
# 10. BEST POLICY THAT STILL HAS CORRUPTION
# ============================================================

corrupt_policies = (
    policies[
        policies[
            "distorted_awards"
        ]
        > 0
    ]
    .copy()
)


best_corrupt_policy = (
    corrupt_policies
    .sort_values(
        "net_public_value",
        ascending=False
    )
    .iloc[0]
)


# ============================================================
# 11. BASELINE POLICY
# ============================================================

baseline = (
    policies[
        np.isclose(
            policies["p"],
            0.10
        )
        &
        (
            policies["sanction"]
            == 100
        )
    ]
    .iloc[0]
)


# ============================================================
# 12. NO-CONTROL POLICY
# ============================================================

no_control = (
    policies[
        np.isclose(
            policies["p"],
            0
        )
        &
        (
            policies["sanction"]
            == 0
        )
    ]
    .iloc[0]
)


# ============================================================
# 13. VALIDATIONS
# ============================================================

# No-control policy should have zero institutional cost.

assert np.isclose(
    no_control[
        "institutional_cost"
    ],
    0
)


# Baseline detection cost:
#
# 1000 * 0.10^2 = 10

assert np.isclose(
    detection_cost(
        0.10
    ),
    10
)


# Baseline sanction cost:
#
# 0.5 * 100 = 50

assert np.isclose(
    sanction_cost(
        100
    ),
    50
)


# Therefore baseline institutional cost = 60

baseline_cost = (
    detection_cost(
        baseline["p"]
    )
    +
    sanction_cost(
        baseline["sanction"]
    )
)

assert np.isclose(
    baseline_cost,
    60
)


# Optimal Net Public Value must not exceed
# honest public value before institutional cost.

assert (
    optimal_policy[
        "net_public_value"
    ]
    <= HONEST_PUBLIC_VALUE_EXPECTED
)


# ============================================================
# 14. TOP 10 POLICIES
# ============================================================

top_10 = (
    policies
    .sort_values(
        "net_public_value",
        ascending=False
    )
    .head(10)
    .copy()
)


# ============================================================
# 15. SAVE RESULTS
# ============================================================

policies.to_csv(
    "results/policy_grid_with_costs.csv",
    index=False
)


top_10.to_csv(
    "results/top_10_net_public_value_policies.csv",
    index=False
)


summary = pd.DataFrame(
    [
        {
            "policy":
                "Optimal policy",

            "p":
                optimal_policy["p"],

            "sanction":
                optimal_policy["sanction"],

            "institutional_cost":
                optimal_policy[
                    "institutional_cost"
                ],

            "distorted_awards":
                optimal_policy[
                    "distorted_awards"
                ],

            "public_value":
                optimal_policy[
                    "final_public_value"
                ],

            "net_public_value":
                optimal_policy[
                    "net_public_value"
                ]
        },

        {
            "policy":
                "Best clean policy",

            "p":
                best_clean_policy["p"],

            "sanction":
                best_clean_policy["sanction"],

            "institutional_cost":
                best_clean_policy[
                    "institutional_cost"
                ],

            "distorted_awards":
                best_clean_policy[
                    "distorted_awards"
                ],

            "public_value":
                best_clean_policy[
                    "final_public_value"
                ],

            "net_public_value":
                best_clean_policy[
                    "net_public_value"
                ]
        },

        {
            "policy":
                "Cheapest clean policy",

            "p":
                cheapest_clean_policy["p"],

            "sanction":
                cheapest_clean_policy[
                    "sanction"
                ],

            "institutional_cost":
                cheapest_clean_policy[
                    "institutional_cost"
                ],

            "distorted_awards":
                cheapest_clean_policy[
                    "distorted_awards"
                ],

            "public_value":
                cheapest_clean_policy[
                    "final_public_value"
                ],

            "net_public_value":
                cheapest_clean_policy[
                    "net_public_value"
                ]
        },

        {
            "policy":
                "Best corrupt policy",

            "p":
                best_corrupt_policy["p"],

            "sanction":
                best_corrupt_policy[
                    "sanction"
                ],

            "institutional_cost":
                best_corrupt_policy[
                    "institutional_cost"
                ],

            "distorted_awards":
                best_corrupt_policy[
                    "distorted_awards"
                ],

            "public_value":
                best_corrupt_policy[
                    "final_public_value"
                ],

            "net_public_value":
                best_corrupt_policy[
                    "net_public_value"
                ]
        },

        {
            "policy":
                "Baseline",

            "p":
                baseline["p"],

            "sanction":
                baseline["sanction"],

            "institutional_cost":
                baseline[
                    "institutional_cost"
                ],

            "distorted_awards":
                baseline[
                    "distorted_awards"
                ],

            "public_value":
                baseline[
                    "final_public_value"
                ],

            "net_public_value":
                baseline[
                    "net_public_value"
                ]
        },

        {
            "policy":
                "No control",

            "p":
                no_control["p"],

            "sanction":
                no_control["sanction"],

            "institutional_cost":
                no_control[
                    "institutional_cost"
                ],

            "distorted_awards":
                no_control[
                    "distorted_awards"
                ],

            "public_value":
                no_control[
                    "final_public_value"
                ],

            "net_public_value":
                no_control[
                    "net_public_value"
                ]
        }
    ]
)


summary.to_csv(
    "results/institutional_cost_summary.csv",
    index=False
)


# ============================================================
# 16. MATRICES FOR FIGURES
# ============================================================

net_value_matrix = (
    policies
    .pivot(
        index="sanction",
        columns="p",
        values="net_public_value"
    )
)


institutional_cost_matrix = (
    policies
    .pivot(
        index="sanction",
        columns="p",
        values="institutional_cost"
    )
)


# ============================================================
# 17. FIGURE — NET PUBLIC VALUE MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    net_value_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        policies["p"].min(),
        policies["p"].max(),
        policies["sanction"].min(),
        policies["sanction"].max()
    ]
)


plt.scatter(
    optimal_policy["p"],
    optimal_policy["sanction"],
    marker="x",
    s=100,
    label="Optimal policy"
)


plt.xlabel(
    "Probability of detection"
)

plt.ylabel(
    "Sanction"
)

plt.title(
    "Kairos Corruption Lab — "
    "Net Public Value Across Institutional Policies"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    "figures/"
    "net_public_value_policy_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 18. FIGURE — INSTITUTIONAL COST MAP
# ============================================================

plt.figure(
    figsize=(11, 8)
)

plt.imshow(
    institutional_cost_matrix.values,
    origin="lower",
    aspect="auto",
    extent=[
        policies["p"].min(),
        policies["p"].max(),
        policies["sanction"].min(),
        policies["sanction"].max()
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
    "Institutional Cost Across Policies"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "institutional_cost_policy_map.png",
    dpi=300
)

plt.close()


# ============================================================
# 19. FIGURE — TOP 10 POLICIES
# ============================================================

top_10_plot = (
    top_10
    .copy()
    .reset_index(drop=True)
)


top_10_plot[
    "policy_label"
] = (
    "p="
    + (
        top_10_plot["p"]
        * 100
    )
    .round()
    .astype(int)
    .astype(str)
    + "%, F="
    + top_10_plot[
        "sanction"
    ]
    .astype(int)
    .astype(str)
)


plt.figure(
    figsize=(11, 7)
)

plt.barh(
    top_10_plot[
        "policy_label"
    ],
    top_10_plot[
        "net_public_value"
    ]
)

plt.xlabel(
    "Net Public Value"
)

plt.ylabel(
    "Policy"
)

plt.title(
    "Kairos Corruption Lab — "
    "Top 10 Institutional Policies"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "top_10_net_public_value_policies.png",
    dpi=300
)

plt.close()


# ============================================================
# 20. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 92
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 8B — "
    "INSTITUTIONAL COSTS"
)

print(
    "=" * 92
)


print(
    "\nSYNTHETIC COST FUNCTIONS"
)

print(
    f"Detection cost: "
    f"C_p(p) = {ALPHA} * p^2"
)

print(
    f"Sanction cost: "
    f"C_F(F) = {BETA} * F"
)


print(
    "\n"
    + "=" * 92
)

print(
    "POLICY COMPARISON"
)

print(
    "=" * 92
)


print(
    summary.to_string(
        index=False,
        formatters={
            "p":
                "{:.0%}".format,

            "institutional_cost":
                "{:.2f}".format,

            "public_value":
                "{:.2f}".format,

            "net_public_value":
                "{:.2f}".format
        }
    )
)


# ============================================================
# 21. OPTIMAL POLICY DETAILS
# ============================================================

print(
    "\n"
    + "=" * 92
)

print(
    "OPTIMAL POLICY"
)

print(
    "=" * 92
)


print(
    f"Detection probability: "
    f"{optimal_policy['p']:.0%}"
)

print(
    f"Sanction: "
    f"{optimal_policy['sanction']:.0f}"
)

print(
    f"Expected penalty pF: "
    f"{optimal_policy['expected_penalty']:.2f}"
)

print(
    f"Detection cost: "
    f"{optimal_policy['detection_cost']:.2f}"
)

print(
    f"Sanction cost: "
    f"{optimal_policy['sanction_cost']:.2f}"
)

print(
    f"Total institutional cost: "
    f"{optimal_policy['institutional_cost']:.2f}"
)

print(
    f"Distorted awards: "
    f"{int(optimal_policy['distorted_awards'])}"
)

print(
    f"Gross Public Value: "
    f"{optimal_policy['final_public_value']:.2f}"
)

print(
    f"Net Public Value: "
    f"{optimal_policy['net_public_value']:.2f}"
)


# ============================================================
# 22. TOP 10
# ============================================================

print(
    "\n"
    + "=" * 92
)

print(
    "TOP 10 POLICIES BY NET PUBLIC VALUE"
)

print(
    "=" * 92
)


print(
    top_10[
        [
            "p",
            "sanction",
            "expected_penalty",
            "institutional_cost",
            "distorted_awards",
            "final_public_value",
            "net_public_value"
        ]
    ]
    .to_string(
        index=False,
        formatters={
            "p":
                "{:.0%}".format,

            "expected_penalty":
                "{:.2f}".format,

            "institutional_cost":
                "{:.2f}".format,

            "final_public_value":
                "{:.2f}".format,

            "net_public_value":
                "{:.2f}".format
        }
    )
)


# ============================================================
# 23. IMPORTANT INTERPRETATION WARNING
# ============================================================

print(
    "\nIMPORTANT"
)

print(
    "The optimal policy is optimal only inside this "
    "synthetic model and under the chosen cost functions."
)

print(
    "It is NOT an empirical policy recommendation."
)


# ============================================================
# 24. FILES GENERATED
# ============================================================

print(
    "\nFILES GENERATED"
)

print(
    "results/"
    "policy_grid_with_costs.csv"
)

print(
    "results/"
    "top_10_net_public_value_policies.csv"
)

print(
    "results/"
    "institutional_cost_summary.csv"
)

print()

print(
    "figures/"
    "net_public_value_policy_map.png"
)

print(
    "figures/"
    "institutional_cost_policy_map.png"
)

print(
    "figures/"
    "top_10_net_public_value_policies.png"
)


print(
    "\nExperiment 8B completed correctly."
)

print(
    "=" * 92
    + "\n"
)