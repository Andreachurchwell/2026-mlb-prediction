from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

PITCHING_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

STARTERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "inherited_runner_entries_2026.csv"
)


# =========================================================
# LOAD
# =========================================================

def load_data():

    print("Loading data...")

    pitching = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters = pd.read_csv(
        STARTERS_FILE
    )

    pitching["game_date"] = pd.to_datetime(
        pitching["game_date"]
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    print(
        f"Loaded {len(pitching):,} pitches."
    )

    print(
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    return pitching, starters


# =========================================================
# TEAM / STARTER LOOKUP
# =========================================================

def build_game_team_lookup(
    starters,
):

    home = starters[
        [
            "game_pk",
            "home_team",
            "home_starter_id",
        ]
    ].rename(
        columns={
            "home_team":
                "team",

            "home_starter_id":
                "starter_id",
        }
    )

    home["pitching_side"] = "home"

    away = starters[
        [
            "game_pk",
            "away_team",
            "away_starter_id",
        ]
    ].rename(
        columns={
            "away_team":
                "team",

            "away_starter_id":
                "starter_id",
        }
    )

    away["pitching_side"] = "away"

    return pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    )


# =========================================================
# BUILD RELIEVER ENTRIES
# =========================================================

def build_reliever_entries(
    pitching,
    starters,
):

    print(
        "\nFinding reliever entry situations..."
    )

    pitching = pitching.sort_values(
        [
            "game_pk",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "pitch_number",
        ]
    ).copy()

    rows = []

    grouped = pitching.groupby(
        [
            "game_pk",
            "pitcher",
            "player_name",
        ],
        dropna=False,
    )

    for (
        game_pk,
        pitcher_id,
        pitcher_name,
    ), group in grouped:

        group = group.sort_values(
            [
                "inning",
                "at_bat_number",
                "pitch_number",
            ]
        )

        first_pitch = group.iloc[0]

        inning_topbot = (
            first_pitch[
                "inning_topbot"
            ]
        )

        if inning_topbot == "Top":
            pitching_side = "home"

        else:
            pitching_side = "away"

        rows.append(
            {
                "game_pk":
                    game_pk,

                "game_date":
                    first_pitch[
                        "game_date"
                    ],

                "pitcher_id":
                    pitcher_id,

                "pitcher_name":
                    pitcher_name,

                "pitching_side":
                    pitching_side,

                "entry_inning":
                    first_pitch[
                        "inning"
                    ],

                "entry_outs":
                    first_pitch[
                        "outs_when_up"
                    ],

                "on_1b":
                    first_pitch[
                        "on_1b"
                    ],

                "on_2b":
                    first_pitch[
                        "on_2b"
                    ],

                "on_3b":
                    first_pitch[
                        "on_3b"
                    ],
            }
        )

    entries = pd.DataFrame(
        rows
    )

    lookup = build_game_team_lookup(
        starters
    )

    entries = entries.merge(
        lookup,
        on=[
            "game_pk",
            "pitching_side",
        ],
        how="left",
    )

    entries["is_starter"] = (
        entries[
            "pitcher_id"
        ]
        .astype("Int64")
        ==
        entries[
            "starter_id"
        ]
        .astype("Int64")
    )

    relievers = entries[
        ~entries["is_starter"]
    ].copy()

    relievers = relievers.dropna(
        subset=[
            "team",
            "pitcher_name",
        ]
    )

    # Count occupied bases when the
    # reliever throws his first pitch.

    relievers[
        "inherited_runners"
    ] = (
        relievers[
            [
                "on_1b",
                "on_2b",
                "on_3b",
            ]
        ]
        .notna()
        .sum(axis=1)
    )

    relievers[
        "entered_with_runners"
    ] = (
        relievers[
            "inherited_runners"
        ]
        > 0
    )

    return relievers


# =========================================================
# SUMMARY
# =========================================================

def print_summary(
    relievers,
):

    print()
    print(
        "INHERITED RUNNER SUMMARY"
    )
    print()

    summary = (
        relievers
        .groupby(
            [
                "pitcher_name",
                "team",
            ]
        )
        .agg(
            appearances=(
                "game_pk",
                "nunique",
            ),

            entries_with_runners=(
                "entered_with_runners",
                "sum",
            ),

            inherited_runners=(
                "inherited_runners",
                "sum",
            ),

            avg_entry_inning=(
                "entry_inning",
                "mean",
            ),

            avg_entry_outs=(
                "entry_outs",
                "mean",
            ),
        )
        .reset_index()
    )

    summary[
        "traffic_entry_rate"
    ] = (
        summary[
            "entries_with_runners"
        ]
        /
        summary[
            "appearances"
        ]
    )

    summary = summary.sort_values(
        [
            "inherited_runners",
            "entries_with_runners",
        ],
        ascending=False,
    )

    print(
        summary
        .head(30)
        .to_string(
            index=False
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    pitching, starters = (
        load_data()
    )

    relievers = (
        build_reliever_entries(
            pitching,
            starters,
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    relievers.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nCreated "
        f"{len(relievers):,} "
        f"reliever entries."
    )

    print_summary(
        relievers
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()