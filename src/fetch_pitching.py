from pathlib import Path

import pandas as pd

from pybaseball import statcast, cache

cache.enable()


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

START_DATE = "2026-03-25"
END_DATE = "2026-08-16"


def main():

    print("Fetching 2026 Statcast data...")
    print("This is a bulk download, so it may still take a minute.\n")

    data = statcast(
        start_dt=START_DATE,
        end_dt=END_DATE,
    )

    print(f"Downloaded {len(data):,} pitches.")

    # Keep only columns we are likely to need.
    columns = [
        "game_date",
        "game_pk",
        "pitcher",
        "player_name",
        "inning",
        "inning_topbot",
        "at_bat_number",
        "pitch_number",
        "events",
        "description",
        "balls",
        "strikes",
        "post_away_score",
        "post_home_score"
    ]

    available_columns = [
        column
        for column in columns
        if column in data.columns
    ]

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