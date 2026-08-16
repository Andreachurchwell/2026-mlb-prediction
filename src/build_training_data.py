from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "games_2026.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "training_data_2026.csv"

ALL_STAR_DATE = pd.Timestamp("2026-07-14")

PRE_ASB_WEIGHT = 0.5
POST_ASB_WEIGHT = 1.0

MIN_GAMES = 10


def load_games():
    df = pd.read_csv(INPUT_FILE)
    df["date"] = pd.to_datetime(df["date"])

    return df.sort_values(
        ["date", "game_id"]
    ).reset_index(drop=True)


def make_team_state():
    return {
        "games": 0,
        "wins": 0,
        "runs_scored": 0,
        "runs_allowed": 0,
        "weighted_wins": 0.0,
        "recency_weight_total": 0.0,
        "quality_weighted_wins": 0.0,
        "quality_weight_total": 0.0,
        "results": [],
    }


def current_win_pct(state):
    if state["games"] == 0:
        return 0.500

    return state["wins"] / state["games"]


def get_features(state):
    if state["games"] < MIN_GAMES:
        return None

    recent_results = state["results"][-10:]

    return {
        "win_pct": (
            state["wins"]
            / state["games"]
        ),

        "weighted_win_pct": (
            state["weighted_wins"]
            / state["recency_weight_total"]
        ),

        "quality_weighted_win_pct": (
            state["quality_weighted_wins"]
            / state["quality_weight_total"]
        ),

        "recent_win_pct": (
            sum(recent_results)
            / len(recent_results)
        ),

        "run_diff_per_game": (
            (
                state["runs_scored"]
                - state["runs_allowed"]
            )
            / state["games"]
        ),

        "runs_scored_per_game": (
            state["runs_scored"]
            / state["games"]
        ),

        "runs_allowed_per_game": (
            state["runs_allowed"]
            / state["games"]
        ),
    }


def update_team_state(
    state,
    win,
    runs_scored,
    runs_allowed,
    game_date,
    opponent_win_pct,
):
    if game_date > ALL_STAR_DATE:
        recency_weight = POST_ASB_WEIGHT
    else:
        recency_weight = PRE_ASB_WEIGHT

    opponent_strength_weight = (
        0.5 + opponent_win_pct
    )

    quality_weight = (
        recency_weight
        * opponent_strength_weight
    )

    state["games"] += 1
    state["wins"] += win

    state["runs_scored"] += runs_scored
    state["runs_allowed"] += runs_allowed

    state["weighted_wins"] += (
        win * recency_weight
    )

    state["recency_weight_total"] += (
        recency_weight
    )

    state["quality_weighted_wins"] += (
        win * quality_weight
    )

    state["quality_weight_total"] += (
        quality_weight
    )

    state["results"].append(win)


def build_training_data(games):
    teams = sorted(
        set(games["home_team"])
        | set(games["away_team"])
    )

    states = {
        team: make_team_state()
        for team in teams
    }

    rows = []

    total_games = len(games)

    for index, game in games.iterrows():

        if index % 100 == 0:
            print(
                f"Processing game "
                f"{index:,} / {total_games:,}"
            )

        game_date = game["date"]

        home_team = game["home_team"]
        away_team = game["away_team"]

        home_state = states[home_team]
        away_state = states[away_team]

        # --------------------------------
        # FEATURES BEFORE THIS GAME
        # --------------------------------

        home_features = get_features(
            home_state
        )

        away_features = get_features(
            away_state
        )

        if (
            home_features is not None
            and away_features is not None
        ):

            rows.append(
                {
                    "game_id":
                        game["game_id"],

                    "date":
                        game_date,

                    "home_team":
                        home_team,

                    "away_team":
                        away_team,

                    "home_win_pct":
                        home_features[
                            "win_pct"
                        ],

                    "away_win_pct":
                        away_features[
                            "win_pct"
                        ],

                    "home_weighted_win_pct":
                        home_features[
                            "weighted_win_pct"
                        ],

                    "away_weighted_win_pct":
                        away_features[
                            "weighted_win_pct"
                        ],

                    "home_quality_weighted_win_pct":
                        home_features[
                            "quality_weighted_win_pct"
                        ],

                    "away_quality_weighted_win_pct":
                        away_features[
                            "quality_weighted_win_pct"
                        ],

                    "home_recent_win_pct":
                        home_features[
                            "recent_win_pct"
                        ],

                    "away_recent_win_pct":
                        away_features[
                            "recent_win_pct"
                        ],

                    "home_run_diff_per_game":
                        home_features[
                            "run_diff_per_game"
                        ],

                    "away_run_diff_per_game":
                        away_features[
                            "run_diff_per_game"
                        ],

                    "home_runs_scored_per_game":
                        home_features[
                            "runs_scored_per_game"
                        ],

                    "away_runs_scored_per_game":
                        away_features[
                            "runs_scored_per_game"
                        ],

                    "home_runs_allowed_per_game":
                        home_features[
                            "runs_allowed_per_game"
                        ],

                    "away_runs_allowed_per_game":
                        away_features[
                            "runs_allowed_per_game"
                        ],

                    "home_win": int(
                        game["home_score"]
                        > game["away_score"]
                    ),
                }
            )

        # --------------------------------
        # OPPONENT RECORDS BEFORE GAME
        # --------------------------------

        home_opponent_win_pct = (
            current_win_pct(
                away_state
            )
        )

        away_opponent_win_pct = (
            current_win_pct(
                home_state
            )
        )

        # --------------------------------
        # ACTUAL RESULT
        # --------------------------------

        home_win = int(
            game["home_score"]
            > game["away_score"]
        )

        away_win = 1 - home_win

        # --------------------------------
        # UPDATE STATES AFTER GAME
        # --------------------------------

        update_team_state(
            home_state,
            home_win,
            game["home_score"],
            game["away_score"],
            game_date,
            home_opponent_win_pct,
        )

        update_team_state(
            away_state,
            away_win,
            game["away_score"],
            game["home_score"],
            game_date,
            away_opponent_win_pct,
        )

    return pd.DataFrame(rows)


def main():
    print("Loading 2026 games...")

    games = load_games()

    print(
        f"Loaded {len(games):,} games."
    )

    print(
        "\nBuilding optimized "
        "training dataset...\n"
    )

    training_df = build_training_data(
        games
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nCreated "
        f"{len(training_df):,} "
        f"training examples."
    )

    print("\nDATE RANGE")

    print(
        "First:",
        training_df["date"].min()
    )

    print(
        "Latest:",
        training_df["date"].max()
    )

    print("\nSAMPLE QUALITY FEATURES\n")

    print(
        training_df[
            [
                "home_team",
                "away_team",
                "home_weighted_win_pct",
                "home_quality_weighted_win_pct",
                "away_weighted_win_pct",
                "away_quality_weighted_win_pct",
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()