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
# Everything runs in dependency order.
#
# If one step fails, the updater STOPS.
# That prevents later files from rebuilding with
# incomplete or stale inputs.
#
# NOTE:
# MLB play-by-play is cached locally.
# Existing games will NOT be downloaded again.
# Only newly needed games should be fetched.
# =========================================================

PIPELINE = [

    # =====================================================
    # RAW MLB DATA
    # =====================================================

    (
        "Fetching latest MLB games",
        "src/fetch_data.py",
    ),

    (
        "Fetching latest Statcast pitching data",
        "src/fetch_pitching.py",
    ),

    # =====================================================
    # STARTING PITCHING
    # =====================================================

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

    # =====================================================
    # BULLPEN BASE DATA
    # =====================================================

    (
        "Building bullpen appearances",
        "src/build_bullpen_data.py",
    ),

    (
        "Building inherited-runner entry situations",
        "src/build_inherited_runner_data.py",
    ),

    # =====================================================
    # MLB PLAY-BY-PLAY CACHE
    # =====================================================

    (
        "Updating MLB play-by-play cache",
        "src/fetch_play_by_play.py",
    ),

    # =====================================================
    # BULLPEN PERFORMANCE
    # =====================================================

    (
        "Scoring inherited runners",
        "src/score_inherited_runners.py",
    ),

    (
        "Calculating actual relief outs",
        "src/build_reliever_outs.py",
    ),

    (
        "Building reliever run-prevention scores",
        "src/build_reliever_run_scores.py",
    ),

    (
        "Building team bullpen scores",
        "src/build_bullpen_scores.py",
    ),

    # =====================================================
    # FINAL OCTOBER SHIFT
    # =====================================================

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

    # -----------------------------------------------------
    # MAKE SURE SCRIPT EXISTS
    # -----------------------------------------------------

    if not script_path.exists():

        print()

        print(
            "ERROR: Could not find:"
        )

        print(
            script_path
        )

        return False

    # -----------------------------------------------------
    # RUN SCRIPT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # STOP PIPELINE ON FAILURE
    # -----------------------------------------------------

    if result.returncode != 0:

        print()
        print("!" * 72)

        print(
            "UPDATE STOPPED"
        )

        print()

        print(
            f"Step failed: "
            f"{label}"
        )

        print(
            f"Script: "
            f"{script}"
        )

        print(
            f"Exit code: "
            f"{result.returncode}"
        )

        print("!" * 72)

        return False

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

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

    print(
        "OCTOBER SHIFT // UPDATE SYSTEM"
    )

    print("=" * 72)

    print()

    print(
        "Updating games, Statcast, rotations, "
        "bullpens and contender rankings..."
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

    # =====================================================
    # RUN PIPELINE
    # =====================================================

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

            print()

            print(
                "Fix the failed step, then "
                "run this updater again."
            )

            sys.exit(1)

    # =====================================================
    # COMPLETE
    # =====================================================

    total_time = (
        time.time()
        - overall_start
    )

    print()
    print("=" * 72)

    print(
        "OCTOBER SHIFT UPDATE COMPLETE"
    )

    print("=" * 72)

    print()

    print(
        f"All {total} steps finished."
    )

    print(
        f"Total update time: "
        f"{total_time:.1f} seconds"
    )

    # =====================================================
    # OUTPUT FILES
    # =====================================================

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
        "Latest rotation board:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "projected_rotations_2026.csv"
    )

    print()

    print(
        "Latest bullpen board:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "bullpen_scores_2026.csv"
    )

    print()

    print(
        "Ranking history:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "processed"
        / "ranking_history_2026.csv"
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    print()

    print(
        "To open the dashboard:"
    )

    print()

    print(
        "streamlit run app.py"
    )


if __name__ == "__main__":
    main()