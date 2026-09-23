from pathlib import Path
import shutil


# ============================================================
# KAIROS CORRUPTION LAB
# FINAL RESULT SELECTION
#
# Purpose:
# Copy approved result files from results/
# into curated folders for publication.
#
# Original files are NEVER deleted or modified.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = PROJECT_ROOT / "results"

FINAL_DIR = PROJECT_ROOT / "results_final"

MAIN_DIR = FINAL_DIR / "main"

TECHNICAL_DIR = FINAL_DIR / "technical"


# ------------------------------------------------------------
# 2. MAIN PUBLICATION RESULTS
# ------------------------------------------------------------

MAIN_RESULTS = [
    "honest_market.csv",
    "honest_market_summary.csv",
    "corruption_summary.csv",
    "equivalent_policies.csv",
    "institutional_cost_summary.csv",
    "institutional_cost_sensitivity.csv",
    "dynamic_period_summary.csv",
]


# ------------------------------------------------------------
# 3. TECHNICAL RESULTS
# ------------------------------------------------------------
#
# Technical includes all main files plus additional
# reproducibility, sweep, grid, and dynamic-detail outputs.
# ------------------------------------------------------------

TECHNICAL_ONLY_RESULTS = [
    "honest_market_winners.csv",
    "honest_market_all_bids.csv",

    "detection_sweep.csv",
    "detection_policy_sweep.csv",
    "sanction_policy_sweep.csv",

    "corruption_market.csv",

    "firm_penalty_grid.csv",
    "official_penalty_grid.csv",
    "strategic_regions.csv",

    "policy_grid.csv",
    "policy_grid_with_costs.csv",
    "top_10_net_public_value_policies.csv",

    "dynamic_round_results.csv",
    "dynamic_tender_results.csv",
    "dynamic_firm_propensities.csv",
]


TECHNICAL_RESULTS = (
    MAIN_RESULTS
    + TECHNICAL_ONLY_RESULTS
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

def copy_result(
    filename,
    destination_dir
):
    """
    Copy one result file from results/ to destination.

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
# 6. HEADER
# ============================================================

print(
    "\n"
    + "=" * 90
)

print(
    "KAIROS CORRUPTION LAB"
)

print(
    "FINAL RESULT SELECTION"
)

print(
    "=" * 90
)


# ============================================================
# 7. COPY MAIN RESULTS
# ============================================================

print(
    "\nMAIN PUBLICATION"
)


main_copied = 0

main_missing = []


for filename in MAIN_RESULTS:

    copied = copy_result(
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
# 8. COPY TECHNICAL RESULTS
# ============================================================

print(
    "\nTECHNICAL PUBLICATION"
)


technical_copied = 0

technical_missing = []


for filename in TECHNICAL_RESULTS:

    copied = copy_result(
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
# 9. SUMMARY
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
    f"\nMain results requested: "
    f"{len(MAIN_RESULTS)}"
)

print(
    f"Main results copied: "
    f"{main_copied}"
)

print(
    f"Main results missing: "
    f"{len(main_missing)}"
)


print(
    f"\nTechnical results requested: "
    f"{len(TECHNICAL_RESULTS)}"
)

print(
    f"Technical results copied: "
    f"{technical_copied}"
)

print(
    f"Technical results missing: "
    f"{len(technical_missing)}"
)


# ============================================================
# 10. REPORT MISSING FILES
# ============================================================

if main_missing:

    print(
        "\nMISSING MAIN RESULTS"
    )

    for filename in main_missing:

        print(
            f" - {filename}"
        )


if technical_missing:

    print(
        "\nMISSING TECHNICAL RESULTS"
    )

    for filename in technical_missing:

        print(
            f" - {filename}"
        )


# ============================================================
# 11. OUTPUT FOLDERS
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


# ============================================================
# 12. FINAL STATUS
# ============================================================

if (
    len(main_missing) == 0
    and
    len(technical_missing) == 0
):

    print(
        "\nAll approved result files were copied successfully."
    )

else:

    print(
        "\nSelection completed with missing files."
    )


print(
    "\nOriginal files in results/ were not modified."
)

print(
    "=" * 90
    + "\n"
)