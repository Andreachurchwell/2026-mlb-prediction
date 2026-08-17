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
    / "bullpen_appearances_2026.csv"
)


# =========================================================
# LOAD DATA
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

    print(
        f"Loaded {len(pitching):,} pitches."
    )

    print(
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    return pitching, starters


# =========================================================
# BUILD PITCHER APPEARANCES
# =========================================================

def build_appearances(
    pitching,
):

    print(
        "\nBuilding pitcher appearances..."
    )

    pitching = pitching.copy()

    pitching["game_date"] = pd.to_datetime(
        pitching["game_date"]
    )

    # Sort every pitch into game order.
    pitching = pitching.sort_values(
        [
            "game_pk",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "pitch_number",
        ]
    )

    appearances = []

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

        first = group.iloc[0]
        last = group.iloc[-1]

        appearances.append(
            {
                "game_pk":
                    game_pk,

                "game_date":
                    first[
                        "game_date"
                    ],

                "pitcher_id":
                    pitcher_id,

                "pitcher_name":
                    pitcher_name,

                "pitches":
                    len(group),

                "first_inning":
                    group[
                        "inning"
                    ].min(),

                "last_inning":
                    group[
                        "inning"
                    ].max(),

                "inning_topbot":
                    first[
                        "inning_topbot"
                    ],

                "score_before_away":
                    first[
                        "post_away_score"
                    ],

                "score_before_home":
                    first[
                        "post_home_score"
                    ],

                "score_after_away":
                    last[
                        "post_away_score"
                    ],

                "score_after_home":
                    last[
                        "post_home_score"
                    ],
            }
        )

    appearances = pd.DataFrame(
        appearances
    )

    print(
        f"Created "
        f"{len(appearances):,} "
        f"pitcher appearances."
    )

    return appearances


# =========================================================
# ATTACH TEAM + STARTER
# =========================================================

def attach_game_info(
    appearances,
    starters,
):

    print(
        "\nIdentifying bullpen appearances..."
    )

    home = starters[
        [
            "game_pk",
            "home_team",
            "home_starter_id",
            "home_starter_name",
        ]
    ].rename(
        columns={
            "home_team":
                "team",

            "home_starter_id":
                "starter_id",

            "home_starter_name":
                "starter_name",
        }
    )

    home["pitching_side"] = "home"

    away = starters[
        [
            "game_pk",
            "away_team",
            "away_starter_id",
            "away_starter_name",
        ]
    ].rename(
        columns={
            "away_team":
                "team",

            "away_starter_id":
                "starter_id",

            "away_starter_name":
                "starter_name",
        }
    )

    away["pitching_side"] = "away"

    game_teams = pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    )

    # A home pitcher throws during the TOP
    # half of an inning.
    #
    # An away pitcher throws during the BOTTOM
    # half.

    appearances["pitching_side"] = (
        appearances[
            "inning_topbot"
        ]
        .map(
            {
                "Top":
                    "home",

                "Bot":
                    "away",
            }
        )
    )

    appearances = appearances.merge(
        game_teams,
        on=[
            "game_pk",
            "pitching_side",
        ],
        how="left",
    )

    appearances["is_starter"] = (
        appearances[
            "pitcher_id"
        ]
        .astype("Int64")
        ==
        appearances[
            "starter_id"
        ]
        .astype("Int64")
    )

    bullpen = appearances[
        ~appearances["is_starter"]
    ].copy()

    bullpen = bullpen.dropna(
        subset=[
            "team",
            "pitcher_name",
        ]
    )

    print(
        f"Found "
        f"{len(bullpen):,} "
        f"bullpen appearances."
    )

    return bullpen


# =========================================================
# SIMPLE RUNS WHILE PITCHING
# =========================================================

def add_run_context(
    bullpen,
):

    bullpen = bullpen.copy()

    # Home pitchers defend against the away team.
    # Away pitchers defend against the home team.

    bullpen[
        "runs_scored_while_pitching"
    ] = 0

    home_mask = (
        bullpen[
            "pitching_side"
        ]
        == "home"
    )

    away_mask = (
        bullpen[
            "pitching_side"
        ]
        == "away"
    )

    bullpen.loc[
        home_mask,
        "runs_scored_while_pitching",
    ] = (
        bullpen.loc[
            home_mask,
            "score_after_away",
        ]
        -
        bullpen.loc[
            home_mask,
            "score_before_away",
        ]
    )

    bullpen.loc[
        away_mask,
        "runs_scored_while_pitching",
    ] = (
        bullpen.loc[
            away_mask,
            "score_after_home",
        ]
        -
        bullpen.loc[
            away_mask,
            "score_before_home",
        ]
    )

    bullpen[
        "runs_scored_while_pitching"
    ] = (
        bullpen[
            "runs_scored_while_pitching"
        ]
        .clip(lower=0)
    )

    return bullpen


# =========================================================
# SUMMARY
# =========================================================

def print_summary(
    bullpen,
):

    print()
    print(
        "TOP RELIEVERS BY APPEARANCES"
    )
    print()

    summary = (
        bullpen
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

            pitches=(
                "pitches",
                "sum",
            ),

            runs_while_pitching=(
                "runs_scored_while_pitching",
                "sum",
            ),

            avg_entry_inning=(
                "first_inning",
                "mean",
            ),
        )
        .reset_index()
    )

    summary = (
        summary
        .sort_values(
            [
                "appearances",
                "pitches",
            ],
            ascending=False,
        )
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

    appearances = (
        build_appearances(
            pitching
        )
    )

    bullpen = (
        attach_game_info(
            appearances,
            starters,
        )
    )

    bullpen = (
        add_run_context(
            bullpen
        )
    )

    bullpen = bullpen.sort_values(
        [
            "game_date",
            "game_pk",
            "team",
            "first_inning",
        ]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    bullpen.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print_summary(
        bullpen
    )

    print()
    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()