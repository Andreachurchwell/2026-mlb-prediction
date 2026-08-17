from pathlib import Path
import subprocess
import sys
import time


# =========================================================
# PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent


# =========================================================
# UPDATE PIPELINE
# =========================================================
#
# These run in order.
#
# If one step fails, the updater STOPS.
# We do not want later files rebuilding from bad or
# incomplete data.
# =========================================================

PIPELINE = [
    (
        "Fetching latest MLB games",
        "src/fetch_data.py",
    ),
    (
        "Fetching latest Statcast pitching data",
        "src/fetch_pitching.py",
    ),
    (
        "Finding starting pitchers",
        "src/build_pitcher_starts.py",
    ),
    (
        "Building starter run scores",
        "src/build_starter_run_scores.py",
    ),
    (
        "Building projected postseason rotations",
        "src/build_projected_rotations.py",
    ),
    (
        "Building October Shift contender board",
        "src/build_contender_board.py",
    ),
    (
        "Saving ranking history",
        "src/save_ranking_history.py",
    ),
]


# =========================================================
# RUN ONE STEP
# =========================================================

def run_step(
    number,
    total,
    label,
    script,
):

    print()
    print("=" * 72)
    print(
        f"[{number}/{total}] "
        f"{label}"
    )
    print("=" * 72)

    script_path = (
        PROJECT_ROOT
        / script
    )

    if not script_path.exists():

        print(
            f"\nERROR: Could not find:\n"
            f"{script_path}"
        )

        return False

    start = time.time()

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
    )

    elapsed = (
        time.time()
        - start
    )

    if result.returncode != 0:

        print()
        print("!" * 72)
        print(
            f"UPDATE STOPPED"
        )
        print()
        print(
            f"Step failed: {label}"
        )
        print(
            f"Script: {script}"
        )
        print(
            f"Exit code: "
            f"{result.returncode}"
        )
        print("!" * 72)

        return False

    print()
    print(
        f"Finished in "
        f"{elapsed:.1f} seconds."
    )

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 72)
    print("OCTOBER SHIFT // UPDATE SYSTEM")
    print("=" * 72)

    print()
    print(
        "Updating games, pitching, rotations "
        "and contender rankings..."
    )

    print(
        f"\nProject: "
        f"{PROJECT_ROOT}"
    )

    total = len(
        PIPELINE
    )

    overall_start = (
        time.time()
    )

    for number, (
        label,
        script,
    ) in enumerate(
        PIPELINE,
        start=1,
    ):

        success = run_step(
            number,
            total,
            label,
            script,
        )

        if not success:

            print()
            print(
                "October Shift was NOT "
                "fully updated."
            )

            sys.exit(1)

    total_time = (
        time.time()
        - overall_start
    )

    print()
    print("=" * 72)
    print("OCTOBER SHIFT UPDATE COMPLETE")
    print("=" * 72)

    print()
    print(
        f"All {total} steps finished."
    )

    print(
        f"Total update time: "
        f"{total_time:.1f} seconds"
    )

    print()
    print(
        "Latest contender board:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "contender_scores_2026.csv"
    )

    print()
    print(
        "To open the dashboard:"
    )

    print(
        "streamlit run app.py"
    )


if __name__ == "__main__":
    main()