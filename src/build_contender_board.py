from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
)

ROTATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "projected_rotations_2026.csv"
)

BULLPEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "bullpen_scores_2026.csv"
)

OFFENSE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "offensive_momentum_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contender_scores_2026.csv"
)


# =========================================================
# SETTINGS
# =========================================================

ALL_STAR_DATE = pd.Timestamp("2026-07-14")

PRE_ASB_WEIGHT = 0.5
POST_ASB_WEIGHT = 1.0


# =========================================================
# OCTOBER SHIFT SCORE WEIGHTS
# =========================================================
#
# Pitching = 25% total
#
# Starting rotation:        20%
# Bullpen:                   5%
#
# Offensive momentum = 15%
#
# Team performance = 60%
#
# Run differential:        20%
# Post-ASB performance:    15%
# Last 10 games:           10%
# Quality-weighted wins:    5%
# Overall record:          10%
#
# TOTAL:                   100%
# =========================================================

ROTATION_WEIGHT = 0.20
BULLPEN_WEIGHT = 0.05
OFFENSE_WEIGHT = 0.15

RUN_DIFF_WEIGHT = 0.20
POST_ASB_WEIGHT_SCORE = 0.15
LAST_10_WEIGHT = 0.10
QUALITY_WEIGHT = 0.05
OVERALL_RECORD_WEIGHT = 0.10


# =========================================================
# LOAD DATA
# =========================================================

def load_games():

    games = pd.read_csv(
        GAMES_FILE
    )

    games["date"] = pd.to_datetime(
        games["date"]
    )

    games = games.sort_values(
        [
            "date",
            "game_id",
        ]
    ).reset_index(drop=True)

    return games


def load_rotation_scores():

    rotation = pd.read_csv(
        ROTATION_FILE
    )

    return rotation


def load_bullpen_scores():

    bullpen = pd.read_csv(
        BULLPEN_FILE
    )

    return bullpen


def load_offense_scores():

    offense = pd.read_csv(
        OFFENSE_FILE
    )

    return offense


# =========================================================
# TEAM STATE
# =========================================================

def make_state():

    return {
        "games": 0,
        "wins": 0,

        "runs_scored": 0,
        "runs_allowed": 0,

        "post_asb_games": 0,
        "post_asb_wins": 0,

        "results": [],

        "quality_weighted_wins": 0.0,
        "quality_weight_total": 0.0,
    }


def win_pct(state):

    if state["games"] == 0:
        return 0.500

    return (
        state["wins"]
        / state["games"]
    )


# =========================================================
# BUILD TEAM METRICS
# =========================================================

def build_team_metrics(games):

    teams = sorted(
        set(games["home_team"])
        | set(games["away_team"])
    )

    states = {
        team: make_state()
        for team in teams
    }

    for _, game in games.iterrows():

        home_team = game["home_team"]
        away_team = game["away_team"]

        home = states[home_team]
        away = states[away_team]

        # --------------------------------
        # OPPONENT STRENGTH BEFORE GAME
        # --------------------------------

        home_opponent_pct = (
            win_pct(away)
        )

        away_opponent_pct = (
            win_pct(home)
        )

        # --------------------------------
        # RESULT
        # --------------------------------

        home_win = int(
            game["home_score"]
            > game["away_score"]
        )

        away_win = 1 - home_win

        # --------------------------------
        # RECENCY WEIGHT
        # --------------------------------

        if game["date"] > ALL_STAR_DATE:

            recency_weight = (
                POST_ASB_WEIGHT
            )

        else:

            recency_weight = (
                PRE_ASB_WEIGHT
            )

        # --------------------------------
        # QUALITY WEIGHT
        # --------------------------------

        home_quality_weight = (
            recency_weight
            * (
                0.5
                + home_opponent_pct
            )
        )

        away_quality_weight = (
            recency_weight
            * (
                0.5
                + away_opponent_pct
            )
        )

        # --------------------------------
        # UPDATE HOME TEAM
        # --------------------------------

        home["games"] += 1
        home["wins"] += home_win

        home["runs_scored"] += (
            game["home_score"]
        )

        home["runs_allowed"] += (
            game["away_score"]
        )

        home["results"].append(
            home_win
        )

        home[
            "quality_weighted_wins"
        ] += (
            home_win
            * home_quality_weight
        )

        home[
            "quality_weight_total"
        ] += (
            home_quality_weight
        )

        # --------------------------------
        # UPDATE AWAY TEAM
        # --------------------------------

        away["games"] += 1
        away["wins"] += away_win

        away["runs_scored"] += (
            game["away_score"]
        )

        away["runs_allowed"] += (
            game["home_score"]
        )

        away["results"].append(
            away_win
        )

        away[
            "quality_weighted_wins"
        ] += (
            away_win
            * away_quality_weight
        )

        away[
            "quality_weight_total"
        ] += (
            away_quality_weight
        )

        # --------------------------------
        # POST ALL-STAR RECORD
        # --------------------------------

        if game["date"] > ALL_STAR_DATE:

            home["post_asb_games"] += 1

            home["post_asb_wins"] += (
                home_win
            )

            away["post_asb_games"] += 1

            away["post_asb_wins"] += (
                away_win
            )

    rows = []

    for team, state in states.items():

        recent = (
            state["results"][-10:]
        )

        rows.append(
            {
                "team":
                    team,

                "games":
                    state["games"],

                "wins":
                    state["wins"],

                "losses":
                    (
                        state["games"]
                        - state["wins"]
                    ),

                "win_pct":
                    win_pct(state),

                "run_diff_per_game":
                    (
                        (
                            state["runs_scored"]
                            - state["runs_allowed"]
                        )
                        / state["games"]
                    ),

                "post_asb_win_pct":
                    (
                        state[
                            "post_asb_wins"
                        ]
                        / state[
                            "post_asb_games"
                        ]
                        if state[
                            "post_asb_games"
                        ] > 0
                        else 0.500
                    ),

                "last_10_win_pct":
                    (
                        sum(recent)
                        / len(recent)
                    ),

                "quality_weighted_win_pct":
                    (
                        state[
                            "quality_weighted_wins"
                        ]
                        / state[
                            "quality_weight_total"
                        ]
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =========================================================
# NORMALIZE
# =========================================================

def normalize(series):
    """
    Convert feature values to a relative
    0-100 scale across MLB.
    """

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
# BUILD OCTOBER SHIFT SCORES
# =========================================================

def build_contender_scores(
    team_metrics,
    rotation_scores,
    bullpen_scores,
    offense_scores,
):

    # --------------------------------
    # MERGE ROTATION
    # --------------------------------

    df = team_metrics.merge(
        rotation_scores,
        on="team",
        how="left",
    )

    # --------------------------------
    # MERGE BULLPEN
    # --------------------------------

    bullpen_columns = [
        "team",
        "bullpen_rank",
        "best_reliever",
        "best_reliever_score",
        "top_3_run_prevention",
        "top_5_run_prevention",
        "strand_rate",
        "strand_score",
        "qualified_relievers",
        "neutral_bullpen_score",
    ]

    df = df.merge(
        bullpen_scores[
            bullpen_columns
        ],
        on="team",
        how="left",
    )

    # --------------------------------
    # MERGE OFFENSIVE MOMENTUM
    # --------------------------------

    offense_columns = [
        "team",
        "offensive_momentum_rank",
        "offensive_momentum_score",
        "offense_level",
        "offense_direction",
        "season_offense_score",
        "last_15_offense_score",
        "last_7_offense_score",
        "last_15_runs_per_game",
        "last_15_ops",
        "last_15_iso",
        "last_15_walk_rate",
        "last_15_strikeout_rate",
        "trend_raw",
        "acceleration_raw",
    ]

    available_offense_columns = [
        column
        for column in offense_columns
        if column in offense_scores.columns
    ]

    df = df.merge(
        offense_scores[
            available_offense_columns
        ],
        on="team",
        how="left",
    )

    # --------------------------------
    # HANDLE MISSING ROTATION DATA
    # --------------------------------

    rotation_median = (
        df[
            "projected_rotation_score"
        ]
        .median()
    )

    df[
        "projected_rotation_score"
    ] = (
        df[
            "projected_rotation_score"
        ]
        .fillna(
            rotation_median
        )
    )

    # --------------------------------
    # HANDLE MISSING BULLPEN DATA
    # --------------------------------

    bullpen_median = (
        df[
            "neutral_bullpen_score"
        ]
        .median()
    )

    df[
        "neutral_bullpen_score"
    ] = (
        df[
            "neutral_bullpen_score"
        ]
        .fillna(
            bullpen_median
        )
    )

    # --------------------------------
    # HANDLE MISSING OFFENSE DATA
    # --------------------------------

    offense_median = (
        df[
            "offensive_momentum_score"
        ]
        .median()
    )

    df[
        "offensive_momentum_score"
    ] = (
        df[
            "offensive_momentum_score"
        ]
        .fillna(
            offense_median
        )
    )

    # =====================================================
    # NORMALIZED COMPONENT SCORES
    # =====================================================

    df["rotation_component"] = (
        normalize(
            df[
                "projected_rotation_score"
            ]
        )
    )

    df["bullpen_component"] = (
        normalize(
            df[
                "neutral_bullpen_score"
            ]
        )
    )

    df["offense_component"] = (
        normalize(
            df[
                "offensive_momentum_score"
            ]
        )
    )

    df["run_diff_component"] = (
        normalize(
            df[
                "run_diff_per_game"
            ]
        )
    )

    df["post_asb_component"] = (
        normalize(
            df[
                "post_asb_win_pct"
            ]
        )
    )

    df["last_10_component"] = (
        normalize(
            df[
                "last_10_win_pct"
            ]
        )
    )

    df["quality_component"] = (
        normalize(
            df[
                "quality_weighted_win_pct"
            ]
        )
    )

    df["overall_record_component"] = (
        normalize(
            df[
                "win_pct"
            ]
        )
    )

    # =====================================================
    # FINAL OCTOBER SHIFT SCORE
    # =====================================================
    #
    # 20% Starting Rotation
    #  5% Bullpen
    # 15% Offensive Momentum
    # 20% Run Differential
    # 15% Post-ASB Performance
    # 10% Last 10 Games
    #  5% Quality-Weighted Wins
    # 10% Overall Record
    #
    # TOTAL = 100%
    # =====================================================

    df["october_shift_score"] = (

        df["rotation_component"]
        * ROTATION_WEIGHT

        +

        df["bullpen_component"]
        * BULLPEN_WEIGHT

        +

        df["offense_component"]
        * OFFENSE_WEIGHT

        +

        df["run_diff_component"]
        * RUN_DIFF_WEIGHT

        +

        df["post_asb_component"]
        * POST_ASB_WEIGHT_SCORE

        +

        df["last_10_component"]
        * LAST_10_WEIGHT

        +

        df["quality_component"]
        * QUALITY_WEIGHT

        +

        df["overall_record_component"]
        * OVERALL_RECORD_WEIGHT
    )

    # Keep contender_score for compatibility
    # with the Streamlit application.

    df["contender_score"] = (
        df["october_shift_score"]
    )

    # --------------------------------
    # SORT + RANK
    # --------------------------------

    df = (
        df
        .sort_values(
            "october_shift_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    df.insert(
        0,
        "rank",
        range(
            1,
            len(df) + 1
        ),
    )

    return df


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Building October Shift..."
    )

    # --------------------------------
    # GAMES
    # --------------------------------

    games = load_games()

    print(
        f"Loaded {len(games):,} games."
    )

    # --------------------------------
    # ROTATIONS
    # --------------------------------

    rotation_scores = (
        load_rotation_scores()
    )

    print(
        f"Loaded rotation scores "
        f"for {len(rotation_scores):,} teams."
    )

    # --------------------------------
    # BULLPENS
    # --------------------------------

    bullpen_scores = (
        load_bullpen_scores()
    )

    print(
        f"Loaded bullpen scores "
        f"for {len(bullpen_scores):,} teams."
    )

    # --------------------------------
    # OFFENSIVE MOMENTUM
    # --------------------------------

    offense_scores = (
        load_offense_scores()
    )

    print(
        f"Loaded offensive momentum scores "
        f"for {len(offense_scores):,} teams."
    )

    # --------------------------------
    # TEAM METRICS
    # --------------------------------

    team_metrics = (
        build_team_metrics(
            games
        )
    )

    # --------------------------------
    # FINAL BOARD
    # --------------------------------

    board = (
        build_contender_scores(
            team_metrics,
            rotation_scores,
            bullpen_scores,
            offense_scores,
        )
    )

    # --------------------------------
    # SAVE
    # --------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    board.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # =====================================================
    # MAIN CONTENDER BOARD
    # =====================================================

    print(
        "\nOCTOBER SHIFT // "
        "2026 WORLD SERIES CONTENDER BOARD\n"
    )

    display_columns = [
        "rank",
        "team",
        "wins",
        "losses",
        "post_asb_win_pct",
        "last_10_win_pct",
        "run_diff_per_game",
        "quality_weighted_win_pct",
        "projected_rotation_rank",
        "bullpen_rank",
        "offensive_momentum_rank",
        "projected_rotation_score",
        "neutral_bullpen_score",
        "offensive_momentum_score",
        "offense_level",
        "offense_direction",
        "october_shift_score",
    ]

    print(
        board[
            display_columns
        ]
        .head(15)
        .to_string(
            index=False
        )
    )

    # =====================================================
    # TOP ROTATIONS
    # =====================================================

    print(
        "\nTOP ROTATIONS IN CONTENDER BOARD\n"
    )

    rotation_display = [
        "team",
        "projected_rotation_rank",
        "projected_ace",
        "projected_top_3_score",
        "projected_top_4_score",
        "projected_rotation_score",
        "projected_top_4",
    ]

    print(
        board[
            rotation_display
        ]
        .sort_values(
            "projected_rotation_rank"
        )
        .head(10)
        .to_string(
            index=False
        )
    )

    # =====================================================
    # TOP BULLPENS
    # =====================================================

    print(
        "\nTOP BULLPENS IN CONTENDER BOARD\n"
    )

    bullpen_display = [
        "team",
        "bullpen_rank",
        "best_reliever",
        "top_3_run_prevention",
        "top_5_run_prevention",
        "strand_rate",
        "qualified_relievers",
        "neutral_bullpen_score",
    ]

    print(
        board[
            bullpen_display
        ]
        .sort_values(
            "bullpen_rank"
        )
        .head(10)
        .to_string(
            index=False
        )
    )

    # =====================================================
    # TOP OFFENSIVE MOMENTUM
    # =====================================================

    print(
        "\nTOP OFFENSIVE MOMENTUM IN CONTENDER BOARD\n"
    )

    offense_display = [
        "team",
        "offensive_momentum_rank",
        "offensive_momentum_score",
        "offense_level",
        "offense_direction",
        "last_15_runs_per_game",
        "last_15_ops",
    ]

    print(
        board[
            offense_display
        ]
        .sort_values(
            "offensive_momentum_rank"
        )
        .head(10)
        .to_string(
            index=False
        )
    )

    # =====================================================
    # MODEL WEIGHTS
    # =====================================================

    print(
        "\nOCTOBER SHIFT MODEL WEIGHTS\n"
    )

    print(
        "Starting Rotation:      20%"
    )

    print(
        "Bullpen:                 5%"
    )

    print(
        "Offensive Momentum:     15%"
    )

    print(
        "Run Differential:       20%"
    )

    print(
        "Post-ASB Performance:   15%"
    )

    print(
        "Last 10 Games:          10%"
    )

    print(
        "Quality-Weighted Wins:   5%"
    )

    print(
        "Overall Record:         10%"
    )

    print(
        "\nTOTAL:                  100%"
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()