from pathlib import Path
from datetime import date

import pandas as pd

from pybaseball import statcast, cache

cache.enable()


# =========================================================
# PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

START_DATE = "2026-03-25"

# Always fetch through today instead of stopping at a hard-coded date.
END_DATE = date.today().isoformat()


# =========================================================
# MAIN
# =========================================================

def main():

    print("Fetching 2026 Statcast data...")
    print(
        f"Date range: {START_DATE} through {END_DATE}"
    )
    print(
        "This is a bulk download, so it may still take a minute.\n"
    )

    data = statcast(
        start_dt=START_DATE,
        end_dt=END_DATE,
    )

    print(
        f"Downloaded {len(data):,} pitches."
    )

    # =====================================================
    # KEEP PITCHING + HITTING FIELDS
    # =====================================================

    columns = [
        # Game / pitch identity
        "game_date",
        "game_pk",
        "pitcher",
        "player_name",
        "batter",

        # Pitch / plate appearance context
        "inning",
        "inning_topbot",
        "at_bat_number",
        "pitch_number",
        "events",
        "description",
        "balls",
        "strikes",
        "outs_when_up",

        # Baserunners
        "on_1b",
        "on_2b",
        "on_3b",

        # Score state
        "bat_score",
        "fld_score",
        "post_bat_score",
        "post_fld_score",
        "post_away_score",
        "post_home_score",

        # Hitting / batted-ball fields
        "bb_type",
        "launch_speed",
        "launch_angle",
        "estimated_woba_using_speedangle",
        "woba_value",
        "woba_denom",
        "babip_value",
        "iso_value",

        # Team fields if available
        "home_team",
        "away_team",
    ]

    available_columns = [
        column
        for column in columns
        if column in data.columns
    ]

    missing_columns = [
        column
        for column in columns
        if column not in data.columns
    ]

    print(
        f"\nKeeping {len(available_columns)} columns."
    )

    if missing_columns:
        print(
            "\nColumns not returned by Statcast:"
        )

        for column in missing_columns:
            print(
                f"  - {column}"
            )

    pitching = data[
        available_columns
    ].copy()

    pitching = pitching.sort_values(
        [
            "game_date",
            "game_pk",
            "inning",
            "at_bat_number",
            "pitch_number",
        ]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pitching.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nSAMPLE\n")

    print(
        pitching.head(10)
        .to_string(index=False)
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()