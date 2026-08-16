from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STARTERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)

STARTER_RUN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "starter_run_scores_2026.csv"
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
    / "rotation_scores_2026.csv"
)


# =========================================================
# SETTINGS
# =========================================================

# We don't want someone with 1-2 weird starts
# being treated like an October rotation arm.
MIN_STARTS = 5

# Filters out most openers.
MIN_AVG_PITCHES = 50

# Used for reliability shrinkage.
#
# Smaller value:
# trust small samples more.
#
# Larger value:
# pull small samples harder toward league average.
RELIABILITY_STRENGTH = 8


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print("Loading starter data...")

    starters = pd.read_csv(
        STARTERS_FILE
    )

    run_scores = pd.read_csv(
        STARTER_RUN_FILE
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
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    print(
        f"Loaded run-score history "
        f"for {len(run_scores):,} games."
    )

    print(
        f"Loaded {len(pitches):,} pitches."
    )

    return (
        starters,
        run_scores,
        pitches,
    )


# =========================================================
# STARTER PITCH COUNTS
# =========================================================

def build_pitch_counts(
    starters,
    pitches,
):
    """
    Determine how many pitches each actual starter
    threw in each game.

    This lets us distinguish normal starters from
    openers who only work an inning or two.
    """

    print(
        "\nCalculating starter workloads..."
    )

    starter_rows = []

    valid_games = starters.dropna(
        subset=[
            "home_starter_id",
            "away_starter_id",
        ]
    )

    for _, game in valid_games.iterrows():

        starter_rows.append(
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

        starter_rows.append(
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

    starter_index = pd.DataFrame(
        starter_rows
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

    pitch_counts = (
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

    print(
        f"Built workload data for "
        f"{len(pitch_counts):,} "
        "starter appearances."
    )

    return pitch_counts


# =========================================================
# RUN SCORE HISTORY
# =========================================================

def build_score_history(
    starters,
    run_scores,
):
    """
    Connect each run score with the team the pitcher
    started for in that game.
    """

    print(
        "\nBuilding pitcher score history..."
    )

    score_columns = [
        "game_pk",

        "home_starter_name",
        "home_starter_prior_starts",
        "home_starter_season_run_score",
        "home_starter_season_runs_allowed",

        "away_starter_name",
        "away_starter_prior_starts",
        "away_starter_season_run_score",
        "away_starter_season_runs_allowed",
    ]

    scores = run_scores[
        score_columns
    ].copy()

    merged = starters.merge(
        scores,
        on="game_pk",
        how="left",
        suffixes=(
            "_starter",
            "_score",
        ),
    )

    rows = []

    for _, game in merged.iterrows():

        # --------------------------------
        # HOME STARTER
        # --------------------------------

        home_name = game.get(
            "home_starter_name_starter"
        )

        if pd.notna(home_name):

            rows.append(
                {
                    "game_pk":
                        int(
                            game["game_pk"]
                        ),

                    "date":
                        game["date"],

                    "team":
                        game["home_team"],

                    "pitcher_name":
                        home_name,

                    "prior_starts":
                        game.get(
                            "home_starter_prior_starts"
                        ),

                    "season_run_score":
                        game.get(
                            "home_starter_season_run_score"
                        ),

                    "season_runs_allowed":
                        game.get(
                            "home_starter_season_runs_allowed"
                        ),
                }
            )

        # --------------------------------
        # AWAY STARTER
        # --------------------------------

        away_name = game.get(
            "away_starter_name_starter"
        )

        if pd.notna(away_name):

            rows.append(
                {
                    "game_pk":
                        int(
                            game["game_pk"]
                        ),

                    "date":
                        game["date"],

                    "team":
                        game["away_team"],

                    "pitcher_name":
                        away_name,

                    "prior_starts":
                        game.get(
                            "away_starter_prior_starts"
                        ),

                    "season_run_score":
                        game.get(
                            "away_starter_season_run_score"
                        ),

                    "season_runs_allowed":
                        game.get(
                            "away_starter_season_runs_allowed"
                        ),
                }
            )

    return pd.DataFrame(
        rows
    )


# =========================================================
# PITCHER SUMMARY
# =========================================================

def build_pitcher_summary(
    score_history,
    pitch_counts,
):
    """
    Produce one row per pitcher.

    Requirements:
    - at least MIN_STARTS
    - average starter workload >= MIN_AVG_PITCHES

    Then shrink small-sample scores toward
    the league-average starter score.
    """

    print(
        "\nBuilding qualified starter summaries..."
    )

    # --------------------------------
    # WORKLOAD SUMMARY
    # --------------------------------

    workload = (
        pitch_counts
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
            median_pitches=(
                "pitch_count",
                "median",
            ),
        )
        .reset_index()
    )

    # --------------------------------
    # LATEST SEASON SCORE
    # --------------------------------

    score_history = (
        score_history
        .sort_values(
            [
                "pitcher_name",
                "date",
                "game_pk",
            ]
        )
    )

    latest_rows = []

    for (
        pitcher_name,
        history
    ) in score_history.groupby(
        "pitcher_name"
    ):

        valid_scores = (
            history
            .dropna(
                subset=[
                    "season_run_score"
                ]
            )
            .sort_values("date")
        )

        if valid_scores.empty:
            continue

        latest_score = (
            valid_scores.iloc[-1]
        )

        latest_team = (
            history
            .sort_values("date")
            .iloc[-1]["team"]
        )

        latest_rows.append(
            {
                "pitcher_name":
                    pitcher_name,

                "team":
                    latest_team,

                "raw_quality_score":
                    latest_score[
                        "season_run_score"
                    ],

                "season_runs_allowed":
                    latest_score[
                        "season_runs_allowed"
                    ],
            }
        )

    scores = pd.DataFrame(
        latest_rows
    )

    pitchers = scores.merge(
        workload,
        on="pitcher_name",
        how="left",
    )

    # --------------------------------
    # QUALIFY REAL STARTERS
    # --------------------------------

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

    # --------------------------------
    # LEAGUE AVERAGE
    # --------------------------------

    league_average = (
        pitchers[
            "raw_quality_score"
        ]
        .mean()
    )

    print(
        f"League-average qualified "
        f"starter score: "
        f"{league_average:.3f}"
    )

    # --------------------------------
    # RELIABILITY ADJUSTMENT
    # --------------------------------
    #
    # Example:
    #
    # 5 starts gets less trust than
    # 20 starts.
    #
    # reliability =
    # starts / (starts + strength)
    #

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
        "adjusted_quality_score"
    ] = (
        pitchers[
            "reliability"
        ]
        * pitchers[
            "raw_quality_score"
        ]

        +

        (
            1
            - pitchers[
                "reliability"
            ]
        )
        * league_average
    )

    pitchers = (
        pitchers
        .sort_values(
            "adjusted_quality_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return pitchers


# =========================================================
# TEAM ROTATION SCORE
# =========================================================

def build_team_rotation_scores(
    pitchers,
):
    """
    Rank each team's true starters and calculate
    postseason rotation ceiling.

    The score intentionally rewards teams with
    multiple strong arms, not just one ace.
    """

    print(
        "\nBuilding postseason rotation scores..."
    )

    rows = []

    for team, group in pitchers.groupby(
        "team"
    ):

        group = (
            group
            .sort_values(
                "adjusted_quality_score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        if group.empty:
            continue

        # =================================
        # ACE
        # =================================

        ace = group.iloc[0]

        ace_name = (
            ace["pitcher_name"]
        )

        ace_score = (
            ace[
                "adjusted_quality_score"
            ]
        )

        # =================================
        # TOP THREE
        # =================================

        top_3 = group.head(3)

        top_3_score = (
            top_3[
                "adjusted_quality_score"
            ]
            .mean()
        )

        # =================================
        # TOP FOUR
        # =================================

        top_4 = group.head(4)

        top_4_score = (
            top_4[
                "adjusted_quality_score"
            ]
            .mean()
        )

        # =================================
        # ROTATION DEPTH
        # =================================
        #
        # Specifically rewards teams whose
        # #3 and #4 starters are strong.
        #

        if len(group) >= 4:

            rotation_depth_score = (
                group.iloc[2][
                    "adjusted_quality_score"
                ]
                +
                group.iloc[3][
                    "adjusted_quality_score"
                ]
            ) / 2

        elif len(group) == 3:

            rotation_depth_score = (
                group.iloc[2][
                    "adjusted_quality_score"
                ]
            )

        elif len(group) == 2:

            rotation_depth_score = (
                group.iloc[1][
                    "adjusted_quality_score"
                ]
            )

        else:

            rotation_depth_score = (
                ace_score
            )

        # =================================
        # DEPTH AVAILABILITY PENALTY
        # =================================
        #
        # A team with only one or two
        # qualified starters should not
        # receive the same ceiling as a
        # team with four.
        #

        qualified_count = len(group)

        if qualified_count >= 4:
            depth_multiplier = 1.00

        elif qualified_count == 3:
            depth_multiplier = 0.96

        elif qualified_count == 2:
            depth_multiplier = 0.90

        else:
            depth_multiplier = 0.82

        # =================================
        # FINAL POSTSEASON ROTATION SCORE
        # =================================

        raw_rotation_score = (
            top_3_score
            * 0.35

            + ace_score
            * 0.25

            + top_4_score
            * 0.25

            + rotation_depth_score
            * 0.15
        )

        postseason_rotation_score = (
            raw_rotation_score
            * depth_multiplier
        )

        # =================================
        # DISPLAY INFO
        # =================================

        top_names = (
            group[
                "pitcher_name"
            ]
            .head(4)
            .tolist()
        )

        top_scores = (
            group[
                "adjusted_quality_score"
            ]
            .head(4)
            .round(3)
            .tolist()
        )

        top_raw_scores = (
            group[
                "raw_quality_score"
            ]
            .head(4)
            .round(3)
            .tolist()
        )

        top_starts = (
            group[
                "starts"
            ]
            .head(4)
            .astype(int)
            .tolist()
        )

        rows.append(
            {
                "team":
                    team,

                "qualified_starters":
                    qualified_count,

                "ace_name":
                    ace_name,

                "ace_score":
                    ace_score,

                "top_3_score":
                    top_3_score,

                "top_4_score":
                    top_4_score,

                "rotation_depth_score":
                    rotation_depth_score,

                "depth_multiplier":
                    depth_multiplier,

                "postseason_rotation_score":
                    postseason_rotation_score,

                "top_4_starters":
                    " | ".join(
                        top_names
                    ),

                "top_4_adjusted_scores":
                    " | ".join(
                        str(score)
                        for score
                        in top_scores
                    ),

                "top_4_raw_scores":
                    " | ".join(
                        str(score)
                        for score
                        in top_raw_scores
                    ),

                "top_4_starts":
                    " | ".join(
                        str(start)
                        for start
                        in top_starts
                    ),
            }
        )

    rotation_scores = pd.DataFrame(
        rows
    )

    rotation_scores = (
        rotation_scores
        .sort_values(
            "postseason_rotation_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    rotation_scores.insert(
        0,
        "rotation_rank",
        range(
            1,
            len(rotation_scores) + 1
        ),
    )

    return rotation_scores


# =========================================================
# MAIN
# =========================================================

def main():

    (
        starters,
        run_scores,
        pitches,
    ) = load_data()

    pitch_counts = (
        build_pitch_counts(
            starters,
            pitches,
        )
    )

    score_history = (
        build_score_history(
            starters,
            run_scores,
        )
    )

    pitchers = (
        build_pitcher_summary(
            score_history,
            pitch_counts,
        )
    )

    print(
        f"\nQualified true starters: "
        f"{len(pitchers):,}"
    )

    print(
        "\nTOP QUALIFIED STARTERS\n"
    )

    starter_display = [
        "pitcher_name",
        "team",
        "starts",
        "avg_pitches",
        "raw_quality_score",
        "reliability",
        "adjusted_quality_score",
    ]

    print(
        pitchers[
            starter_display
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    rotation_scores = (
        build_team_rotation_scores(
            pitchers
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rotation_scores.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\n2026 POSTSEASON ROTATION RANKINGS\n"
    )

    display_columns = [
        "rotation_rank",
        "team",
        "qualified_starters",
        "ace_name",
        "ace_score",
        "top_3_score",
        "top_4_score",
        "rotation_depth_score",
        "postseason_rotation_score",
        "top_4_starters",
        "top_4_starts",
    ]

    print(
        rotation_scores[
            display_columns
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