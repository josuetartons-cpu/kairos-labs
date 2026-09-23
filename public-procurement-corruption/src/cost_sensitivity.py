import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# KAIROS CORRUPTION LAB
# EXPERIMENT 8C — INSTITUTIONAL COST SENSITIVITY
#
# Objective:
# Test whether the optimal combination of detection p
# and sanction F changes when the relative costs of
# detection and sanctions change.
#
# IMPORTANT:
# These cost functions remain synthetic.
# This experiment studies robustness inside the artificial
# economy. It is NOT an empirical policy recommendation.
# ============================================================


# ------------------------------------------------------------
# 1. LOAD POLICY GRID FROM EXPERIMENT 8A
# ------------------------------------------------------------

policies = pd.read_csv(
    "results/policy_grid.csv"
)


# ------------------------------------------------------------
# 2. VALIDATE POLICY GRID
# ------------------------------------------------------------

HONEST_PUBLIC_VALUE = 8197.05

assert len(policies) == 1701

assert policies["p"].nunique() == 21

assert policies["sanction"].nunique() == 81

assert np.allclose(
    policies["honest_public_value"],
    HONEST_PUBLIC_VALUE,
    atol=0.02
)


# ============================================================
# 3. COST SENSITIVITY PARAMETERS
# ============================================================
#
# Detection:
#
# C_p(p) = alpha * p^2
#
# Sanctions:
#
# C_F(F) = beta * F
#
#
# We test:
#
# alpha = 500, 1000, 2000
#
# beta = 0.25, 0.50, 1.00
#
# Total:
#
# 3 x 3 = 9 cost structures
# ============================================================

ALPHA_VALUES = [
    500,
    1000,
    2000
]

BETA_VALUES = [
    0.25,
    0.50,
    1.00
]


# ============================================================
# 4. COST FUNCTIONS
# ============================================================

def detection_cost(
    p,
    alpha
):
    """
    Synthetic convex detection cost.

    C_p(p) = alpha * p^2
    """

    return (
        alpha
        * p ** 2
    )


def sanction_cost(
    sanction,
    beta
):
    """
    Synthetic linear sanction cost.

    C_F(F) = beta * F
    """

    return (
        beta
        * sanction
    )


# ============================================================
# 5. RUN COST-SENSITIVITY EXPERIMENT
# ============================================================

sensitivity_records = []


for alpha in ALPHA_VALUES:

    for beta in BETA_VALUES:

        scenario = policies.copy()


        # ----------------------------------------------------
        # Detection cost
        # ----------------------------------------------------

        scenario[
            "detection_cost"
        ] = detection_cost(
            scenario["p"],
            alpha
        )


        # ----------------------------------------------------
        # Sanction cost
        # ----------------------------------------------------

        scenario[
            "sanction_cost"
        ] = sanction_cost(
            scenario["sanction"],
            beta
        )


        # ----------------------------------------------------
        # Total institutional cost
        # ----------------------------------------------------

        scenario[
            "institutional_cost"
        ] = (
            scenario[
                "detection_cost"
            ]
            +
            scenario[
                "sanction_cost"
            ]
        )


        # ----------------------------------------------------
        # Net Public Value
        # ----------------------------------------------------

        scenario[
            "net_public_value"
        ] = (
            scenario[
                "final_public_value"
            ]
            -
            scenario[
                "institutional_cost"
            ]
        )


        # ----------------------------------------------------
        # Overall optimal policy
        # ----------------------------------------------------

        optimal = (
            scenario
            .sort_values(
                [
                    "net_public_value",
                    "institutional_cost"
                ],
                ascending=[
                    False,
                    True
                ]
            )
            .iloc[0]
        )


        # ----------------------------------------------------
        # Best policy with zero distorted awards
        # ----------------------------------------------------

        clean_policies = (
            scenario[
                scenario[
                    "distorted_awards"
                ]
                == 0
            ]
            .copy()
        )


        best_clean = (
            clean_policies
            .sort_values(
                [
                    "net_public_value",
                    "institutional_cost"
                ],
                ascending=[
                    False,
                    True
                ]
            )
            .iloc[0]
        )


        # ----------------------------------------------------
        # Cheapest clean policy
        # ----------------------------------------------------

        cheapest_clean = (
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


        # ----------------------------------------------------
        # Save scenario
        # ----------------------------------------------------

        sensitivity_records.append(
            {
                "alpha":
                    alpha,

                "beta":
                    beta,

                "optimal_p":
                    optimal["p"],

                "optimal_sanction":
                    optimal["sanction"],

                "optimal_expected_penalty":
                    optimal[
                        "expected_penalty"
                    ],

                "optimal_detection_cost":
                    optimal[
                        "detection_cost"
                    ],

                "optimal_sanction_cost":
                    optimal[
                        "sanction_cost"
                    ],

                "optimal_institutional_cost":
                    optimal[
                        "institutional_cost"
                    ],

                "optimal_distorted_awards":
                    optimal[
                        "distorted_awards"
                    ],

                "optimal_public_value":
                    optimal[
                        "final_public_value"
                    ],

                "optimal_net_public_value":
                    optimal[
                        "net_public_value"
                    ],

                "best_clean_p":
                    best_clean["p"],

                "best_clean_sanction":
                    best_clean[
                        "sanction"
                    ],

                "best_clean_institutional_cost":
                    best_clean[
                        "institutional_cost"
                    ],

                "best_clean_net_public_value":
                    best_clean[
                        "net_public_value"
                    ],

                "cheapest_clean_p":
                    cheapest_clean[
                        "p"
                    ],

                "cheapest_clean_sanction":
                    cheapest_clean[
                        "sanction"
                    ],

                "cheapest_clean_cost":
                    cheapest_clean[
                        "institutional_cost"
                    ]
            }
        )


# ============================================================
# 6. RESULTS DATAFRAME
# ============================================================

sensitivity = pd.DataFrame(
    sensitivity_records
)


# ============================================================
# 7. VALIDATIONS
# ============================================================

assert len(
    sensitivity
) == 9


# ------------------------------------------------------------
# Baseline cost structure from Experiment 8B:
#
# alpha = 1000
# beta = 0.50
#
# Expected optimum:
#
# p = 20%
# F = 100
# Net Public Value = 8107.05
# ------------------------------------------------------------

baseline_cost_case = (
    sensitivity[
        (
            sensitivity["alpha"]
            == 1000
        )
        &
        (
            np.isclose(
                sensitivity["beta"],
                0.50
            )
        )
    ]
    .iloc[0]
)


assert np.isclose(
    baseline_cost_case[
        "optimal_p"
    ],
    0.20
)


assert np.isclose(
    baseline_cost_case[
        "optimal_sanction"
    ],
    100
)


assert np.isclose(
    baseline_cost_case[
        "optimal_net_public_value"
    ],
    8107.05,
    atol=0.02
)


# ------------------------------------------------------------
# Net Public Value cannot exceed gross honest value
# ------------------------------------------------------------

assert (
    sensitivity[
        "optimal_net_public_value"
    ]
    <= HONEST_PUBLIC_VALUE
).all()


# ============================================================
# 8. POLICY LABELS
# ============================================================

sensitivity[
    "optimal_policy"
] = (
    "p="
    + (
        sensitivity[
            "optimal_p"
        ]
        * 100
    )
    .round()
    .astype(int)
    .astype(str)
    + "%, F="
    + sensitivity[
        "optimal_sanction"
    ]
    .astype(int)
    .astype(str)
)


sensitivity[
    "cost_structure"
] = (
    "α="
    + sensitivity[
        "alpha"
    ]
    .astype(int)
    .astype(str)
    + ", β="
    + sensitivity[
        "beta"
    ]
    .astype(str)
)


# ============================================================
# 9. SAVE RESULTS
# ============================================================

sensitivity.to_csv(
    "results/"
    "institutional_cost_sensitivity.csv",
    index=False
)


# ============================================================
# 10. OPTIMAL DETECTION MATRIX
# ============================================================

detection_matrix = (
    sensitivity
    .pivot(
        index="beta",
        columns="alpha",
        values="optimal_p"
    )
)


# ============================================================
# 11. OPTIMAL SANCTION MATRIX
# ============================================================

sanction_matrix = (
    sensitivity
    .pivot(
        index="beta",
        columns="alpha",
        values="optimal_sanction"
    )
)


# ============================================================
# 12. NET PUBLIC VALUE MATRIX
# ============================================================

net_value_matrix = (
    sensitivity
    .pivot(
        index="beta",
        columns="alpha",
        values="optimal_net_public_value"
    )
)


# ============================================================
# 13. FIGURE — OPTIMAL DETECTION
# ============================================================

plt.figure(
    figsize=(8, 6)
)

plt.imshow(
    detection_matrix.values,
    origin="lower",
    aspect="auto"
)

plt.xticks(
    range(
        len(
            detection_matrix.columns
        )
    ),
    [
        str(int(x))
        for x
        in detection_matrix.columns
    ]
)

plt.yticks(
    range(
        len(
            detection_matrix.index
        )
    ),
    [
        str(x)
        for x
        in detection_matrix.index
    ]
)

plt.xlabel(
    "Detection cost parameter α"
)

plt.ylabel(
    "Sanction cost parameter β"
)

plt.title(
    "Kairos Corruption Lab — "
    "Optimal Detection Under Alternative Costs"
)

plt.colorbar(
    label="Optimal detection probability"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "cost_sensitivity_optimal_detection.png",
    dpi=300
)

plt.close()


# ============================================================
# 14. FIGURE — OPTIMAL SANCTION
# ============================================================

plt.figure(
    figsize=(8, 6)
)

plt.imshow(
    sanction_matrix.values,
    origin="lower",
    aspect="auto"
)

plt.xticks(
    range(
        len(
            sanction_matrix.columns
        )
    ),
    [
        str(int(x))
        for x
        in sanction_matrix.columns
    ]
)

plt.yticks(
    range(
        len(
            sanction_matrix.index
        )
    ),
    [
        str(x)
        for x
        in sanction_matrix.index
    ]
)

plt.xlabel(
    "Detection cost parameter α"
)

plt.ylabel(
    "Sanction cost parameter β"
)

plt.title(
    "Kairos Corruption Lab — "
    "Optimal Sanction Under Alternative Costs"
)

plt.colorbar(
    label="Optimal sanction"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "cost_sensitivity_optimal_sanction.png",
    dpi=300
)

plt.close()


# ============================================================
# 15. FIGURE — OPTIMAL NET PUBLIC VALUE
# ============================================================

plt.figure(
    figsize=(8, 6)
)

plt.imshow(
    net_value_matrix.values,
    origin="lower",
    aspect="auto"
)

plt.xticks(
    range(
        len(
            net_value_matrix.columns
        )
    ),
    [
        str(int(x))
        for x
        in net_value_matrix.columns
    ]
)

plt.yticks(
    range(
        len(
            net_value_matrix.index
        )
    ),
    [
        str(x)
        for x
        in net_value_matrix.index
    ]
)

plt.xlabel(
    "Detection cost parameter α"
)

plt.ylabel(
    "Sanction cost parameter β"
)

plt.title(
    "Kairos Corruption Lab — "
    "Optimal Net Public Value"
)

plt.colorbar(
    label="Net Public Value"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "cost_sensitivity_net_public_value.png",
    dpi=300
)

plt.close()


# ============================================================
# 16. FIGURE — NINE OPTIMAL POLICIES
# ============================================================

plot_data = (
    sensitivity
    .sort_values(
        [
            "alpha",
            "beta"
        ]
    )
    .reset_index(
        drop=True
    )
)


plt.figure(
    figsize=(11, 7)
)

plt.barh(
    plot_data[
        "cost_structure"
    ],
    plot_data[
        "optimal_net_public_value"
    ]
)

plt.xlabel(
    "Optimal Net Public Value"
)

plt.ylabel(
    "Cost structure"
)

plt.title(
    "Kairos Corruption Lab — "
    "Sensitivity of Optimal Institutional Policy"
)

plt.tight_layout()

plt.savefig(
    "figures/"
    "cost_sensitivity_optimal_policies.png",
    dpi=300
)

plt.close()


# ============================================================
# 17. TERMINAL OUTPUT
# ============================================================

print(
    "\n"
    + "=" * 105
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "EXPERIMENT 8C — "
    "INSTITUTIONAL COST SENSITIVITY"
)

print(
    "=" * 105
)


print(
    "\nCOST STRUCTURES"
)

print(
    f"Alpha values: "
    f"{ALPHA_VALUES}"
)

print(
    f"Beta values: "
    f"{BETA_VALUES}"
)

print(
    f"Total sensitivity scenarios: "
    f"{len(sensitivity)}"
)


# ============================================================
# 18. OPTIMAL POLICIES TABLE
# ============================================================

print(
    "\n"
    + "=" * 105
)

print(
    "OPTIMAL POLICY UNDER EACH COST STRUCTURE"
)

print(
    "=" * 105
)


display_columns = [
    "alpha",
    "beta",
    "optimal_p",
    "optimal_sanction",
    "optimal_expected_penalty",
    "optimal_institutional_cost",
    "optimal_distorted_awards",
    "optimal_net_public_value"
]


print(
    sensitivity[
        display_columns
    ]
    .sort_values(
        [
            "alpha",
            "beta"
        ]
    )
    .to_string(
        index=False,
        formatters={
            "beta":
                "{:.2f}".format,

            "optimal_p":
                "{:.0%}".format,

            "optimal_expected_penalty":
                "{:.2f}".format,

            "optimal_institutional_cost":
                "{:.2f}".format,

            "optimal_net_public_value":
                "{:.2f}".format
        }
    )
)


# ============================================================
# 19. UNIQUE OPTIMAL POLICIES
# ============================================================

unique_optima = (
    sensitivity[
        [
            "optimal_p",
            "optimal_sanction"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "optimal_p",
            "optimal_sanction"
        ]
    )
)


print(
    "\n"
    + "=" * 105
)

print(
    "UNIQUE OPTIMAL POLICIES"
)

print(
    "=" * 105
)


print(
    unique_optima
    .to_string(
        index=False,
        formatters={
            "optimal_p":
                "{:.0%}".format
        }
    )
)


# ============================================================
# 20. INTERPRETATION CHECK
# ============================================================

number_unique_optima = (
    len(
        unique_optima
    )
)


print(
    "\nINTERPRETATION"
)


if number_unique_optima == 1:

    print(
        "The same policy remains optimal across all "
        "nine tested cost structures."
    )

else:

    print(
        f"The optimal policy changes across the "
        f"tested cost structures."
    )

    print(
        f"Number of distinct optimal policies: "
        f"{number_unique_optima}"
    )


clean_optima = (
    sensitivity[
        "optimal_distorted_awards"
    ]
    == 0
).all()


print(
    f"All optimal policies eliminate distorted awards: "
    f"{clean_optima}"
)


print(
    "\nBaseline sensitivity validation passed:"
)

print(
    "alpha = 1000, beta = 0.50"
)

print(
    f"Optimal p = "
    f"{baseline_cost_case['optimal_p']:.0%}"
)

print(
    f"Optimal F = "
    f"{baseline_cost_case['optimal_sanction']:.0f}"
)

print(
    f"Optimal Net Public Value = "
    f"{baseline_cost_case['optimal_net_public_value']:.2f}"
)


# ============================================================
# 21. IMPORTANT WARNING
# ============================================================

print(
    "\nIMPORTANT"
)

print(
    "These results describe robustness inside the "
    "synthetic economy only."
)

print(
    "Alpha and beta are assumed cost parameters, "
    "not empirical estimates."
)


# ============================================================
# 22. FILES GENERATED
# ============================================================

print(
    "\nFILES GENERATED"
)

print(
    "results/"
    "institutional_cost_sensitivity.csv"
)

print()

print(
    "figures/"
    "cost_sensitivity_optimal_detection.png"
)

print(
    "figures/"
    "cost_sensitivity_optimal_sanction.png"
)

print(
    "figures/"
    "cost_sensitivity_net_public_value.png"
)

print(
    "figures/"
    "cost_sensitivity_optimal_policies.png"
)


print(
    "\nExperiment 8C completed correctly."
)

print(
    "=" * 105
    + "\n"
)