from pathlib import Path
import shutil


# ============================================================
# KAIROS CORRUPTION LAB
# FINAL FIGURE SELECTION
#
# Purpose:
# Copy approved editorial figures from figures/
# into curated folders for publication.
#
# Original figures are NEVER deleted or modified.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = PROJECT_ROOT / "figures"

FINAL_DIR = PROJECT_ROOT / "figures_final"

MAIN_DIR = FINAL_DIR / "main"

TECHNICAL_DIR = FINAL_DIR / "technical"


# ------------------------------------------------------------
# 2. MAIN PUBLICATION FIGURES
# ------------------------------------------------------------

MAIN_FIGURES = [
    "honest_vs_corrupt_public_value.png",
    "corruption_vs_detection.png",
    "corruption_vs_sanction.png",
    "net_public_value_policy_map.png",
    "dynamic_public_value.png",
    "dynamic_corruption_attempts.png",

    # Optional but approved:
    "dynamic_eligible_firms_above_threshold.png",
]


# ------------------------------------------------------------
# 3. TECHNICAL FIGURES
# ------------------------------------------------------------
#
# Technical includes all main figures plus additional
# methodology, sensitivity, benchmark, and dynamics figures.
# ------------------------------------------------------------

TECHNICAL_ONLY_FIGURES = [
    "detection_payoffs.png",
    "strategic_regions.png",

    "honest_public_value_distribution.png",
    "corruption_loss_by_tender.png",

    "policy_distorted_awards_map.png",
    "policy_firms_willing_map.png",

    "institutional_cost_policy_map.png",

    "cost_sensitivity_optimal_detection.png",
    "cost_sensitivity_optimal_sanction.png",
    "cost_sensitivity_net_public_value.png",

    "dynamic_accepted_bribes.png",
    "dynamic_average_propensity.png",
    "dynamic_all_vs_eligible_firms.png",
]


TECHNICAL_FIGURES = (
    MAIN_FIGURES
    + TECHNICAL_ONLY_FIGURES
)


# ============================================================
# 4. CREATE OUTPUT FOLDERS
# ============================================================

MAIN_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TECHNICAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 5. COPY FUNCTION
# ============================================================

def copy_figure(
    filename,
    destination_dir
):
    """
    Copy one figure from figures/ to destination.

    Returns:
        True  -> copied successfully
        False -> source file missing
    """

    source = (
        SOURCE_DIR
        / filename
    )

    destination = (
        destination_dir
        / filename
    )


    if not source.exists():

        print(
            f"[MISSING] {filename}"
        )

        return False


    shutil.copy2(
        source,
        destination
    )


    print(
        f"[COPIED] "
        f"{filename} "
        f"-> "
        f"{destination.relative_to(PROJECT_ROOT)}"
    )

    return True


# ============================================================
# 6. COPY MAIN FIGURES
# ============================================================

print(
    "\n"
    + "=" * 90
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "FINAL FIGURE SELECTION"
)

print(
    "=" * 90
)


print(
    "\nMAIN PUBLICATION"
)


main_copied = 0

main_missing = []


for filename in MAIN_FIGURES:

    copied = copy_figure(
        filename,
        MAIN_DIR
    )

    if copied:

        main_copied += 1

    else:

        main_missing.append(
            filename
        )


# ============================================================
# 7. COPY TECHNICAL FIGURES
# ============================================================

print(
    "\nTECHNICAL PUBLICATION"
)


technical_copied = 0

technical_missing = []


for filename in TECHNICAL_FIGURES:

    copied = copy_figure(
        filename,
        TECHNICAL_DIR
    )

    if copied:

        technical_copied += 1

    else:

        technical_missing.append(
            filename
        )


# ============================================================
# 8. SUMMARY
# ============================================================

print(
    "\n"
    + "=" * 90
)

print(
    "SUMMARY"
)

print(
    "=" * 90
)


print(
    f"\nMain figures requested: "
    f"{len(MAIN_FIGURES)}"
)

print(
    f"Main figures copied: "
    f"{main_copied}"
)

print(
    f"Main figures missing: "
    f"{len(main_missing)}"
)


print(
    f"\nTechnical figures requested: "
    f"{len(TECHNICAL_FIGURES)}"
)

print(
    f"Technical figures copied: "
    f"{technical_copied}"
)

print(
    f"Technical figures missing: "
    f"{len(technical_missing)}"
)


# ============================================================
# 9. REPORT MISSING FILES
# ============================================================

if main_missing:

    print(
        "\nMISSING MAIN FIGURES"
    )

    for filename in main_missing:

        print(
            f" - {filename}"
        )


if technical_missing:

    print(
        "\nMISSING TECHNICAL FIGURES"
    )

    for filename in technical_missing:

        print(
            f" - {filename}"
        )


# ============================================================
# 10. FINAL STATUS
# ============================================================

print(
    "\nOUTPUT FOLDERS"
)

print(
    f"Main:"
    f"      "
    f"{MAIN_DIR.relative_to(PROJECT_ROOT)}"
)

print(
    f"Technical:"
    f" "
    f"{TECHNICAL_DIR.relative_to(PROJECT_ROOT)}"
)


if (
    len(main_missing) == 0
    and
    len(technical_missing) == 0
):

    print(
        "\nAll approved figures were copied successfully."
    )

else:

    print(
        "\nSelection completed with missing files."
    )


print(
    "\nOriginal files in figures/ were not modified."
)

print(
    "=" * 90
    + "\n"
)