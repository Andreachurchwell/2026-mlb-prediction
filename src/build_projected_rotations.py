from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STARTER_RUN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "starter_run_scores_2026.csv"
)

QUALITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "quality_start_scores_2026.csv"
)

STARTERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)

PITCHING_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "projected_rotations_2026.csv"
)


# =========================================================
# SETTINGS
# =========================================================

MIN_STARTS = 5
MIN_AVG_PITCHES = 50
RELIABILITY_STRENGTH = 8

RUN_SCORE_WEIGHT = 0.60
QS_SCORE_WEIGHT = 0.40


# =========================================================
# HELPERS
# =========================================================

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (
            series - minimum
        )
        /
        (
            maximum - minimum
        )
        * 100
    )


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print("Loading data...")

    starter_runs = pd.read_csv(
        STARTER_RUN_FILE
    )

    starters = pd.read_csv(
        STARTERS_FILE
    )

    pitches = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    pitches["game_date"] = pd.to_datetime(
        pitches["game_date"]
    )

    print(
        f"Loaded starter-run history "
        f"for {len(starter_runs):,} games."
    )

    print(
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    print(
        f"Loaded {len(pitches):,} pitches."
    )

    return (
        starter_runs,
        starters,
        pitches,
    )


# =========================================================
# BUILD STARTER APPEARANCE INDEX
# =========================================================

def build_starter_index(starters):

    rows = []

    valid = starters.dropna(
        subset=[
            "home_starter_id",
            "away_starter_id",
        ]
    )

    for _, game in valid.iterrows():

        rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "date":
                    game["date"],

                "team":
                    game["home_team"],

                "pitcher_id":
                    int(
                        game["home_starter_id"]
                    ),

                "pitcher_name":
                    game[
                        "home_starter_name"
                    ],
            }
        )

        rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "date":
                    game["date"],

                "team":
                    game["away_team"],

                "pitcher_id":
                    int(
                        game["away_starter_id"]
                    ),

                "pitcher_name":
                    game[
                        "away_starter_name"
                    ],
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# WORKLOAD
# =========================================================

def build_workload(
    starter_index,
    pitches,
):

    print(
        "\nBuilding starter workload..."
    )

    starter_pitches = pitches.merge(
        starter_index,
        left_on=[
            "game_pk",
            "pitcher",
        ],
        right_on=[
            "game_pk",
            "pitcher_id",
        ],
        how="inner",
    )

    appearance_counts = (
        starter_pitches
        .groupby(
            [
                "game_pk",
                "pitcher_id",
                "pitcher_name",
                "team",
                "date",
            ]
        )
        .size()
        .reset_index(
            name="pitch_count"
        )
    )

    workload = (
        appearance_counts
        .groupby(
            "pitcher_name"
        )
        .agg(
            starts=(
                "game_pk",
                "count",
            ),

            avg_pitches=(
                "pitch_count",
                "mean",
            ),
        )
        .reset_index()
    )

    latest_team = (
        appearance_counts
        .sort_values(
            [
                "pitcher_name",
                "date",
            ]
        )
        .groupby(
            "pitcher_name"
        )
        .tail(1)[
            [
                "pitcher_name",
                "team",
            ]
        ]
    )

    workload = workload.merge(
        latest_team,
        on="pitcher_name",
        how="left",
    )

    return workload


# =========================================================
# RUN-SUPPRESSION PITCHER SCORE
# =========================================================

def build_run_scores(
    starter_runs,
    workload,
    starter_index,
):

    print(
        "\nBuilding pitcher run-suppression scores..."
    )

    home = starter_runs[
        [
            "game_pk",
            "home_starter_name",
            "home_starter_season_run_score",
        ]
    ].rename(
        columns={
            "home_starter_name":
                "pitcher_name",

            "home_starter_season_run_score":
                "raw_run_score",
        }
    )

    away = starter_runs[
        [
            "game_pk",
            "away_starter_name",
            "away_starter_season_run_score",
        ]
    ].rename(
        columns={
            "away_starter_name":
                "pitcher_name",

            "away_starter_season_run_score":
                "raw_run_score",
        }
    )

    history = pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    )

    history = history.dropna(
        subset=[
            "pitcher_name",
            "raw_run_score",
        ]
    )

    # Attach game date so we can get the
    # pitcher's actual latest season-to-date score.

    game_dates = (
        starter_index[
            [
                "game_pk",
                "date",
            ]
        ]
        .drop_duplicates(
            subset=["game_pk"]
        )
    )

    history = history.merge(
        game_dates,
        on="game_pk",
        how="left",
    )

    history = history.sort_values(
        [
            "pitcher_name",
            "date",
            "game_pk",
        ]
    )

    latest = (
        history
        .groupby(
            "pitcher_name"
        )
        .tail(1)
        [
            [
                "pitcher_name",
                "raw_run_score",
            ]
        ]
    )

    pitchers = workload.merge(
        latest,
        on="pitcher_name",
        how="left",
    )

    pitchers = pitchers[
        (
            pitchers["starts"]
            >= MIN_STARTS
        )
        &
        (
            pitchers["avg_pitches"]
            >= MIN_AVG_PITCHES
        )
    ].copy()

    league_average = (
        pitchers[
            "raw_run_score"
        ]
        .mean()
    )

    pitchers[
        "reliability"
    ] = (
        pitchers["starts"]
        /
        (
            pitchers["starts"]
            + RELIABILITY_STRENGTH
        )
    )

    pitchers[
        "adjusted_run_score"
    ] = (
        pitchers[
            "reliability"
        ]
        *
        pitchers[
            "raw_run_score"
        ]

        +

        (
            1
            - pitchers[
                "reliability"
            ]
        )
        *
        league_average
    )

    return pitchers


# =========================================================
# REBUILD QS PITCHER SCORES
# =========================================================

def build_qs_scores(
    starters,
    pitches,
    workload,
):

    print(
        "\nBuilding pitcher quality-start scores..."
    )

    starter_rows = []

    for _, game in starters.dropna(
        subset=[
            "home_starter_id",
            "away_starter_id",
        ]
    ).iterrows():

        starter_rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "team":
                    game["home_team"],

                "side":
                    "home",

                "pitcher_id":
                    int(
                        game["home_starter_id"]
                    ),

                "pitcher_name":
                    game[
                        "home_starter_name"
                    ],
            }
        )

        starter_rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "team":
                    game["away_team"],

                "side":
                    "away",

                "pitcher_id":
                    int(
                        game["away_starter_id"]
                    ),

                "pitcher_name":
                    game[
                        "away_starter_name"
                    ],
            }
        )

    index = pd.DataFrame(
        starter_rows
    )

    starter_pitches = pitches.merge(
        index,
        left_on=[
            "game_pk",
            "pitcher",
        ],
        right_on=[
            "game_pk",
            "pitcher_id",
        ],
        how="inner",
    )

    starter_pitches = starter_pitches.sort_values(
        [
            "game_pk",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "pitch_number",
        ]
    )

    rows = []

    for (
        game_pk,
        pitcher_id,
    ), pitcher_game in starter_pitches.groupby(
        [
            "game_pk",
            "pitcher_id",
        ]
    ):

        info = index[
            (
                index["game_pk"]
                == game_pk
            )
            &
            (
                index["pitcher_id"]
                == pitcher_id
            )
        ].iloc[0]

        # --------------------------------
        # INNINGS
        # --------------------------------
        #
        # A practical Statcast estimate:
        #
        # inning number tells us how deep
        # into the game the starter reached.
        #
        # outs_when_up tells us the out state
        # of the final plate appearance.
        # --------------------------------

        last_pitch = (
            pitcher_game
            .iloc[-1]
        )

        final_inning = int(
            last_pitch["inning"]
        )

        final_out_state = int(
            last_pitch[
                "outs_when_up"
            ]
        )

        # completed innings before the final inning
        completed_before = (
            final_inning - 1
        )

        innings_pitched = (
            completed_before
            +
            (
                final_out_state
                / 3
            )
        )

        # Give credit if the starter completed
        # the half-inning and there was no next
        # pitcher before the inning ended.
        if final_out_state == 2:

            terminal_event = (
                last_pitch[
                    "events"
                ]
            )

            out_events = {
                "field_out",
                "force_out",
                "strikeout",
                "grounded_into_double_play",
                "double_play",
                "strikeout_double_play",
                "fielders_choice_out",
                "sac_fly",
                "sac_bunt",
            }

            if terminal_event in out_events:

                innings_pitched += (
                    1 / 3
                )

        # --------------------------------
        # RUNS
        # --------------------------------

        if info["side"] == "home":

            score_column = (
                "post_away_score"
            )

        else:

            score_column = (
                "post_home_score"
            )

        runs_allowed = (
            pitcher_game[
                score_column
            ]
            .max()
        )

        if pd.isna(runs_allowed):
            runs_allowed = 0

        quality_start = int(
            (
                innings_pitched
                >= 6.0
            )
            and
            (
                runs_allowed
                <= 3
            )
        )

        rows.append(
            {
                "pitcher_name":
                    info[
                        "pitcher_name"
                    ],

                "innings_pitched":
                    innings_pitched,

                "quality_start":
                    quality_start,
            }
        )

    appearances = pd.DataFrame(
        rows
    )

    summary = (
        appearances
        .groupby(
            "pitcher_name"
        )
        .agg(
            qs_starts=(
                "quality_start",
                "count",
            ),

            quality_starts=(
                "quality_start",
                "sum",
            ),

            avg_innings=(
                "innings_pitched",
                "mean",
            ),
        )
        .reset_index()
    )

    summary[
        "quality_start_rate"
    ] = (
        summary[
            "quality_starts"
        ]
        /
        summary[
            "qs_starts"
        ]
    )

    qualified = workload[
        (
            workload["starts"]
            >= MIN_STARTS
        )
        &
        (
            workload["avg_pitches"]
            >= MIN_AVG_PITCHES
        )
    ].copy()

    summary = qualified.merge(
        summary,
        on="pitcher_name",
        how="left",
    )

    league_average = (
        summary[
            "quality_start_rate"
        ]
        .mean()
    )

    summary[
        "reliability"
    ] = (
        summary[
            "starts"
        ]
        /
        (
            summary[
                "starts"
            ]
            + RELIABILITY_STRENGTH
        )
    )

    summary[
        "adjusted_qs_rate"
    ] = (
        summary[
            "reliability"
        ]
        *
        summary[
            "quality_start_rate"
        ]

        +

        (
            1
            - summary[
                "reliability"
            ]
        )
        *
        league_average
    )

    minimum_ip = (
        summary[
            "avg_innings"
        ]
        .min()
    )

    maximum_ip = (
        summary[
            "avg_innings"
        ]
        .max()
    )

    if maximum_ip == minimum_ip:

        summary[
            "innings_score"
        ] = 50.0

    else:

        summary[
            "innings_score"
        ] = (
            (
                summary[
                    "avg_innings"
                ]
                - minimum_ip
            )
            /
            (
                maximum_ip
                - minimum_ip
            )
        )

    summary[
        "qs_starter_score"
    ] = (
        summary[
            "adjusted_qs_rate"
        ]
        * 0.80

        +

        summary[
            "innings_score"
        ]
        * 0.20
    )

    return summary


# =========================================================
# BUILD ONE SHARED PITCHER BOARD
# =========================================================

def combine_pitcher_scores(
    run_scores,
    qs_scores,
):

    print(
        "\nCreating neutral starter ranking..."
    )

    columns = [
        "pitcher_name",
        "team",
        "starts",
        "avg_pitches",
        "adjusted_run_score",
    ]

    combined = (
        run_scores[
            columns
        ]
        .merge(
            qs_scores[
                [
                    "pitcher_name",
                    "qs_starter_score",
                    "quality_start_rate",
                    "avg_innings",
                ]
            ],
            on="pitcher_name",
            how="inner",
        )
    )

    # Normalize PLAYER scores, not team scores.
    combined[
        "run_score_normalized"
    ] = normalize(
        combined[
            "adjusted_run_score"
        ]
    )

    combined[
        "qs_score_normalized"
    ] = normalize(
        combined[
            "qs_starter_score"
        ]
    )

    combined[
        "selection_score"
    ] = (
        combined[
            "run_score_normalized"
        ]
        * RUN_SCORE_WEIGHT

        +

        combined[
            "qs_score_normalized"
        ]
        * QS_SCORE_WEIGHT
    )

    return (
        combined
        .sort_values(
            "selection_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# =========================================================
# PICK SAME FOUR FOR BOTH SYSTEMS
# =========================================================

def build_projected_rotations(
    pitchers,
):

    print(
        "\nSelecting projected top four "
        "for each team..."
    )

    rows = []

    for team, group in pitchers.groupby(
        "team"
    ):

        group = (
            group
            .sort_values(
                "selection_score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        top_four = (
            group.head(4)
        )

        if top_four.empty:
            continue

        names = (
            top_four[
                "pitcher_name"
            ]
            .tolist()
        )

        # --------------------------------
        # SAME FOUR: RUN SCORE
        # --------------------------------

        run_rotation_score = (
            top_four[
                "run_score_normalized"
            ]
            .mean()
        )

        # --------------------------------
        # SAME FOUR: QS SCORE
        # --------------------------------

        qs_rotation_score = (
            top_four[
                "qs_score_normalized"
            ]
            .mean()
        )

        # --------------------------------
        # ACE
        # --------------------------------

        ace = (
            top_four.iloc[0]
        )

        ace_score = (
            ace[
                "selection_score"
            ]
        )

        # --------------------------------
        # TOP 3
        # --------------------------------

        top_3_score = (
            top_four
            .head(3)[
                "selection_score"
            ]
            .mean()
        )

        # --------------------------------
        # TOP 4
        # --------------------------------

        top_4_score = (
            top_four[
                "selection_score"
            ]
            .mean()
        )

        # --------------------------------
        # DEPTH
        # --------------------------------
        #
        # This specifically rewards teams
        # whose #3 and #4 starters are good.
        # --------------------------------

        if len(top_four) >= 4:

            depth_score = (
                top_four.iloc[2][
                    "selection_score"
                ]
                +
                top_four.iloc[3][
                    "selection_score"
                ]
            ) / 2

        elif len(top_four) == 3:

            depth_score = (
                top_four.iloc[2][
                    "selection_score"
                ]
            )

        elif len(top_four) == 2:

            depth_score = (
                top_four.iloc[1][
                    "selection_score"
                ]
            )

        else:

            depth_score = (
                ace_score
            )

        # --------------------------------
        # FINAL POSTSEASON ROTATION SCORE
        # --------------------------------
        #
        # Each individual pitcher's
        # selection_score is already:
        #
        # 60% run suppression
        # 40% quality-start / depth ability
        #
        # Now we shape the TEAM rotation.
        #
        # Top 3 matters most because playoff
        # rotations usually shorten.
        #
        # Ace gets extra weight.
        #
        # Top 4 + depth reward teams that have
        # more than just one or two good arms.
        # --------------------------------

        final_rotation_score = (
            top_3_score
            * 0.40

            +

            ace_score
            * 0.25

            +

            top_4_score
            * 0.20

            +

            depth_score
            * 0.15
        )

        rows.append(
            {
                "team":
                    team,

                "projected_ace":
                    ace[
                        "pitcher_name"
                    ],

                "projected_ace_score":
                    ace_score,

                "projected_top_3_score":
                    top_3_score,

                "projected_top_4_score":
                    top_4_score,

                "projected_depth_score":
                    depth_score,

                "projected_run_score":
                    run_rotation_score,

                "projected_qs_score":
                    qs_rotation_score,

                "projected_rotation_score":
                    final_rotation_score,

                "projected_top_4":
                    " | ".join(
                        names
                    ),

                "starter_1":
                    names[0]
                    if len(names) >= 1
                    else "",

                "starter_2":
                    names[1]
                    if len(names) >= 2
                    else "",

                "starter_3":
                    names[2]
                    if len(names) >= 3
                    else "",

                "starter_4":
                    names[3]
                    if len(names) >= 4
                    else "",
            }
        )

    result = pd.DataFrame(
        rows
    )

    result = (
        result
        .sort_values(
            "projected_rotation_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "projected_rotation_rank",
        range(
            1,
            len(result) + 1
        ),
    )

    return result


# =========================================================
# MAIN
# =========================================================

def main():

    (
        starter_runs,
        starters,
        pitches,
    ) = load_data()

    starter_index = (
        build_starter_index(
            starters
        )
    )

    workload = (
        build_workload(
            starter_index,
            pitches,
        )
    )

    run_scores = (
        build_run_scores(
            starter_runs,
            workload,
            starter_index,
        )
    )

    qs_scores = (
        build_qs_scores(
            starters,
            pitches,
            workload,
        )
    )

    pitchers = (
        combine_pitcher_scores(
            run_scores,
            qs_scores,
        )
    )

    print(
        f"\nQualified shared starter pool: "
        f"{len(pitchers):,}"
    )

    print(
        "\nTOP NEUTRAL STARTERS\n"
    )

    display_pitchers = [
        "pitcher_name",
        "team",
        "starts",
        "avg_pitches",
        "run_score_normalized",
        "qs_score_normalized",
        "selection_score",
    ]

    print(
        pitchers[
            display_pitchers
        ]
        .head(25)
        .to_string(
            index=False
        )
    )

    rotations = (
        build_projected_rotations(
            pitchers
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rotations.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nPROJECTED POSTSEASON ROTATIONS\n"
    )

    display_rotations = [
    "projected_rotation_rank",
    "team",
    "projected_ace",
    "projected_ace_score",
    "projected_top_3_score",
    "projected_top_4_score",
    "projected_depth_score",
    "projected_rotation_score",
    "projected_top_4",
]

    print(
        rotations[
            display_rotations
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()