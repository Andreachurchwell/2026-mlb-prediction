from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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

CURRENT_ROTATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rotation_scores_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "quality_start_scores_2026.csv"
)


# =========================================================
# SETTINGS
# =========================================================

MIN_STARTS = 5

# Helps filter out openers.
MIN_AVG_PITCHES = 50

# Pulls small samples toward league average.
RELIABILITY_STRENGTH = 8

# Experimental blend.
#
# We are NOT changing October Shift with this yet.
CURRENT_ROTATION_BLEND = 0.60
QUALITY_START_BLEND = 0.40


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print("Loading data...")

    pitches = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters = pd.read_csv(
        STARTERS_FILE,
    )

    rotations = pd.read_csv(
        CURRENT_ROTATION_FILE,
    )

    pitches["game_date"] = pd.to_datetime(
        pitches["game_date"]
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    print(
        f"Loaded {len(pitches):,} pitches."
    )

    print(
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    print(
        f"Loaded current rotation scores "
        f"for {len(rotations):,} teams."
    )

    return (
        pitches,
        starters,
        rotations,
    )


# =========================================================
# STARTER INDEX
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

        # HOME STARTER
        rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "date":
                    game["date"],

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

        # AWAY STARTER
        rows.append(
            {
                "game_pk":
                    int(game["game_pk"]),

                "date":
                    game["date"],

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

    return pd.DataFrame(
        rows
    )


# =========================================================
# CALCULATE OUTS FROM STATCAST
# =========================================================

def add_outs_recorded(pitches):
    """
    Statcast's outs_when_up tells us how many outs
    existed BEFORE each pitch.

    We sort every pitch in each half inning and compare
    the current pitch with the next pitch.

    Example:

    current pitch: 0 outs
    next pitch:    1 out

    That means one out happened after the current pitch.

    If there is no next pitch in the half inning, we
    normally know the half inning ended at 3 outs.

    This also catches many baserunning outs that are
    awkward to reconstruct from the 'events' column.
    """

    print(
        "\nCalculating outs from "
        "Statcast pitch sequence..."
    )

    data = pitches.copy()

    data = data.sort_values(
        [
            "game_pk",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "pitch_number",
        ]
    ).reset_index(drop=True)

    half_inning_keys = [
        "game_pk",
        "inning",
        "inning_topbot",
    ]

    data[
        "next_outs_when_up"
    ] = (
        data
        .groupby(
            half_inning_keys
        )[
            "outs_when_up"
        ]
        .shift(-1)
    )

    # If there is another pitch in the same
    # half inning, its outs_when_up tells us
    # how many outs exist after this pitch.
    data[
        "outs_after_pitch"
    ] = data[
        "next_outs_when_up"
    ]

    # If this is the final pitch in the half
    # inning, normally the inning ended with
    # three outs.
    #
    # Rare walk-off situations can end before
    # three outs, but that should have almost
    # no effect on our starter QS calculation.
    data[
        "outs_after_pitch"
    ] = (
        data[
            "outs_after_pitch"
        ]
        .fillna(3)
    )

    data[
        "outs_recorded_on_pitch"
    ] = (
        data[
            "outs_after_pitch"
        ]
        - data[
            "outs_when_up"
        ]
    )

    # Defensive protection against unusual
    # Statcast sequences.
    data[
        "outs_recorded_on_pitch"
    ] = (
        data[
            "outs_recorded_on_pitch"
        ]
        .clip(
            lower=0,
            upper=3,
        )
    )

    return data


# =========================================================
# BUILD STARTER GAME LINES
# =========================================================

def build_game_lines(
    pitches,
    starter_index,
):

    print(
        "\nMatching pitches to starters..."
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

    print(
        f"Found {len(starter_pitches):,} "
        "pitches thrown by starters."
    )

    grouped = (
        starter_pitches
        .groupby(
            [
                "game_pk",
                "pitcher_id",
            ]
        )
    )

    print(
        f"Building {len(grouped):,} "
        "starter appearances..."
    )

    rows = []

    for (
        game_pk,
        pitcher_id,
    ), pitcher_game in grouped:

        info = starter_index[
            (
                starter_index["game_pk"]
                == game_pk
            )
            &
            (
                starter_index["pitcher_id"]
                == pitcher_id
            )
        ].iloc[0]

        pitcher_game = (
            pitcher_game
            .sort_values(
                [
                    "inning",
                    "at_bat_number",
                    "pitch_number",
                ]
            )
        )

        # --------------------------------
        # PITCH COUNT
        # --------------------------------

        pitch_count = len(
            pitcher_game
        )

        # --------------------------------
        # OUTS RECORDED
        # --------------------------------

        outs_recorded = (
            pitcher_game[
                "outs_recorded_on_pitch"
            ]
            .sum()
        )

        innings_pitched = (
            outs_recorded
            / 3.0
        )

        # --------------------------------
        # RUNS SCORED WHILE STARTER
        # WAS ON THE MOUND
        # --------------------------------
        #
        # Home starter faces away hitters.
        # Away starter faces home hitters.
        #
        # Because the opposing team begins
        # the game with zero runs, the max
        # opponent score reached while this
        # pitcher was still pitching gives
        # our run-suppression proxy.
        #
        # This is NOT official earned runs.
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

        runs_allowed = int(
            runs_allowed
        )

        # --------------------------------
        # QUALITY START PROXY
        # --------------------------------
        #
        # Official QS:
        #
        # 6+ innings
        # <= 3 EARNED runs
        #
        # We do not yet have clean earned-run
        # attribution, so ours is:
        #
        # 6+ innings
        # <= 3 runs scored while starter
        # was pitching
        # --------------------------------

        quality_start_proxy = int(
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
                "game_pk":
                    game_pk,

                "date":
                    info["date"],

                "team":
                    info["team"],

                "pitcher_id":
                    pitcher_id,

                "pitcher_name":
                    info[
                        "pitcher_name"
                    ],

                "pitch_count":
                    pitch_count,

                "outs_recorded":
                    outs_recorded,

                "innings_pitched":
                    innings_pitched,

                "runs_allowed":
                    runs_allowed,

                "quality_start_proxy":
                    quality_start_proxy,
            }
        )

    return pd.DataFrame(
        rows
    )


# =========================================================
# PITCHER SUMMARY
# =========================================================

def build_pitcher_summary(
    game_lines,
):

    print(
        "\nBuilding pitcher "
        "quality-start summaries..."
    )

    summaries = (
        game_lines
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

            avg_innings=(
                "innings_pitched",
                "mean",
            ),

            avg_runs_allowed=(
                "runs_allowed",
                "mean",
            ),

            quality_starts=(
                "quality_start_proxy",
                "sum",
            ),
        )
        .reset_index()
    )

    # --------------------------------
    # CURRENT TEAM
    # --------------------------------

    latest_team = (
        game_lines
        .sort_values(
            [
                "pitcher_name",
                "date",
                "game_pk",
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

    summaries = summaries.merge(
        latest_team,
        on="pitcher_name",
        how="left",
    )

    # --------------------------------
    # FILTER OUT OPENERS
    # --------------------------------

    summaries = summaries[
        (
            summaries["starts"]
            >= MIN_STARTS
        )
        &
        (
            summaries["avg_pitches"]
            >= MIN_AVG_PITCHES
        )
    ].copy()

    # --------------------------------
    # QUALITY START RATE
    # --------------------------------

    summaries[
        "quality_start_rate"
    ] = (
        summaries[
            "quality_starts"
        ]
        /
        summaries[
            "starts"
        ]
    )

    # --------------------------------
    # LEAGUE AVERAGE
    # --------------------------------

    league_qs_rate = (
        summaries[
            "quality_start_rate"
        ]
        .mean()
    )

    print(
        f"League-average QS proxy rate: "
        f"{league_qs_rate:.3f}"
    )

    # --------------------------------
    # SAMPLE RELIABILITY
    # --------------------------------

    summaries[
        "reliability"
    ] = (
        summaries[
            "starts"
        ]
        /
        (
            summaries[
                "starts"
            ]
            + RELIABILITY_STRENGTH
        )
    )

    summaries[
        "adjusted_qs_rate"
    ] = (
        summaries[
            "reliability"
        ]
        *
        summaries[
            "quality_start_rate"
        ]

        +

        (
            1
            - summaries[
                "reliability"
            ]
        )
        *
        league_qs_rate
    )

    # --------------------------------
    # INNINGS DEPTH SCORE
    # --------------------------------

    min_ip = (
        summaries[
            "avg_innings"
        ]
        .min()
    )

    max_ip = (
        summaries[
            "avg_innings"
        ]
        .max()
    )

    if max_ip == min_ip:

        summaries[
            "innings_depth_score"
        ] = 0.5

    else:

        summaries[
            "innings_depth_score"
        ] = (
            (
                summaries[
                    "avg_innings"
                ]
                - min_ip
            )
            /
            (
                max_ip
                - min_ip
            )
        )

    # --------------------------------
    # QS STARTER SCORE
    # --------------------------------
    #
    # Most of the score comes from
    # producing quality-start-type games.
    #
    # A smaller portion rewards pitchers
    # who consistently pitch deeper.
    # --------------------------------

    summaries[
        "qs_starter_score"
    ] = (
        summaries[
            "adjusted_qs_rate"
        ]
        * 0.80

        +

        summaries[
            "innings_depth_score"
        ]
        * 0.20
    )

    return (
        summaries
        .sort_values(
            "qs_starter_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# =========================================================
# BUILD QUALITY-START ROTATIONS
# =========================================================

def build_qs_rotation_scores(
    pitchers,
):

    print(
        "\nBuilding quality-start "
        "rotation rankings..."
    )

    rows = []

    for team, group in pitchers.groupby(
        "team"
    ):

        group = (
            group
            .sort_values(
                "qs_starter_score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        if group.empty:
            continue

        # --------------------------------
        # ACE
        # --------------------------------

        ace = group.iloc[0]

        ace_score = (
            ace[
                "qs_starter_score"
            ]
        )

        # --------------------------------
        # TOP 3
        # --------------------------------

        top_3 = group.head(3)

        top_3_score = (
            top_3[
                "qs_starter_score"
            ]
            .mean()
        )

        # --------------------------------
        # TOP 4
        # --------------------------------

        top_4 = group.head(4)

        top_4_score = (
            top_4[
                "qs_starter_score"
            ]
            .mean()
        )

        # --------------------------------
        # DEPTH
        # --------------------------------

        if len(group) >= 4:

            depth_score = (
                group.iloc[2][
                    "qs_starter_score"
                ]
                +
                group.iloc[3][
                    "qs_starter_score"
                ]
            ) / 2

        elif len(group) == 3:

            depth_score = (
                group.iloc[2][
                    "qs_starter_score"
                ]
            )

        elif len(group) == 2:

            depth_score = (
                group.iloc[1][
                    "qs_starter_score"
                ]
            )

        else:

            depth_score = (
                ace_score
            )

        # --------------------------------
        # NUMBER OF QUALIFIED STARTERS
        # --------------------------------

        qualified_count = len(
            group
        )

        if qualified_count >= 4:

            depth_multiplier = 1.00

        elif qualified_count == 3:

            depth_multiplier = 0.96

        elif qualified_count == 2:

            depth_multiplier = 0.90

        else:

            depth_multiplier = 0.82

        # --------------------------------
        # ROTATION SCORE
        # --------------------------------

        raw_rotation_score = (
            top_3_score
            * 0.35

            +

            ace_score
            * 0.25

            +

            top_4_score
            * 0.25

            +

            depth_score
            * 0.15
        )

        qs_rotation_score = (
            raw_rotation_score
            * depth_multiplier
        )

        names = (
            group[
                "pitcher_name"
            ]
            .head(4)
            .tolist()
        )

        rows.append(
            {
                "team":
                    team,

                "qs_qualified_starters":
                    qualified_count,

                "qs_ace":
                    ace[
                        "pitcher_name"
                    ],

                "qs_ace_score":
                    ace_score,

                "qs_top_3_score":
                    top_3_score,

                "qs_top_4_score":
                    top_4_score,

                "qs_depth_score":
                    depth_score,

                "qs_rotation_score":
                    qs_rotation_score,

                "qs_top_4_starters":
                    " | ".join(
                        names
                    ),
            }
        )

    result = pd.DataFrame(
        rows
    )

    result = (
        result
        .sort_values(
            "qs_rotation_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "qs_rotation_rank",
        range(
            1,
            len(result) + 1
        ),
    )

    return result


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_0_100(series):

    minimum = (
        series.min()
    )

    maximum = (
        series.max()
    )

    if maximum == minimum:

        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (
            series
            - minimum
        )
        /
        (
            maximum
            - minimum
        )
        * 100
    )


# =========================================================
# FAIR COMPARISON / BLEND
# =========================================================

def compare_rotation_models(
    qs_rotations,
    current_rotations,
):

    current = current_rotations[
        [
            "team",
            "rotation_rank",
            "postseason_rotation_score",
            "ace_name",
            "top_4_starters",
        ]
    ].copy()

    comparison = (
        qs_rotations
        .merge(
            current,
            on="team",
            how="outer",
        )
    )

    # --------------------------------
    # MISSING VALUES
    # --------------------------------

    comparison[
        "postseason_rotation_score"
    ] = (
        comparison[
            "postseason_rotation_score"
        ]
        .fillna(
            comparison[
                "postseason_rotation_score"
            ]
            .median()
        )
    )

    comparison[
        "qs_rotation_score"
    ] = (
        comparison[
            "qs_rotation_score"
        ]
        .fillna(
            comparison[
                "qs_rotation_score"
            ]
            .median()
        )
    )

    # --------------------------------
    # NORMALIZE BOTH TO 0-100
    # --------------------------------

    comparison[
        "current_rotation_normalized"
    ] = (
        normalize_0_100(
            comparison[
                "postseason_rotation_score"
            ]
        )
    )

    comparison[
        "qs_rotation_normalized"
    ] = (
        normalize_0_100(
            comparison[
                "qs_rotation_score"
            ]
        )
    )

    # --------------------------------
    # TRUE 60 / 40 BLEND
    # --------------------------------

    comparison[
        "blended_rotation_score"
    ] = (
        comparison[
            "current_rotation_normalized"
        ]
        * CURRENT_ROTATION_BLEND

        +

        comparison[
            "qs_rotation_normalized"
        ]
        * QUALITY_START_BLEND
    )

    comparison = (
        comparison
        .sort_values(
            "blended_rotation_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    comparison.insert(
        0,
        "blended_rotation_rank",
        range(
            1,
            len(comparison) + 1
        ),
    )

    return comparison


# =========================================================
# MAIN
# =========================================================

def main():

    (
        pitches,
        starters,
        rotations,
    ) = load_data()

    # --------------------------------
    # CALCULATE OUTS
    # --------------------------------

    pitches = (
        add_outs_recorded(
            pitches
        )
    )

    # --------------------------------
    # STARTERS
    # --------------------------------

    starter_index = (
        build_starter_index(
            starters
        )
    )

    # --------------------------------
    # GAME LINES
    # --------------------------------

    game_lines = (
        build_game_lines(
            pitches,
            starter_index,
        )
    )

    print(
        f"\nCreated "
        f"{len(game_lines):,} "
        "starter game lines."
    )

    # --------------------------------
    # PITCHER SCORES
    # --------------------------------

    pitchers = (
        build_pitcher_summary(
            game_lines
        )
    )

    print(
        f"\nQualified starters: "
        f"{len(pitchers):,}"
    )

    print(
        "\nTOP QUALITY-START "
        "STARTERS\n"
    )

    pitcher_columns = [
        "pitcher_name",
        "team",
        "starts",
        "avg_pitches",
        "avg_innings",
        "avg_runs_allowed",
        "quality_starts",
        "quality_start_rate",
        "adjusted_qs_rate",
        "qs_starter_score",
    ]

    print(
        pitchers[
            pitcher_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    # --------------------------------
    # QS ROTATIONS
    # --------------------------------

    qs_rotations = (
        build_qs_rotation_scores(
            pitchers
        )
    )

    # --------------------------------
    # FAIR MODEL COMPARISON
    # --------------------------------

    comparison = (
        compare_rotation_models(
            qs_rotations,
            rotations,
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nFAIR ROTATION MODEL "
        "COMPARISON\n"
    )

    display_columns = [
        "blended_rotation_rank",
        "team",

        "rotation_rank",
        "postseason_rotation_score",
        "current_rotation_normalized",

        "qs_rotation_rank",
        "qs_rotation_score",
        "qs_rotation_normalized",

        "blended_rotation_score",

        "qs_ace",
    ]

    print(
        comparison[
            display_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    print(
        "\nBLENDED TOP 10 ROTATIONS\n"
    )

    top_columns = [
        "blended_rotation_rank",
        "team",
        "blended_rotation_score",
        "ace_name",
        "qs_ace",
        "top_4_starters",
        "qs_top_4_starters",
    ]

    print(
        comparison[
            top_columns
        ]
        .head(10)
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