from pathlib import Path

import pandas as pd


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

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "starter_run_scores_2026.csv"
)

RECENT_STARTS = 5


def load_data():

    print("Loading data...")

    pitches = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters = pd.read_csv(
        STARTERS_FILE
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
        f"Loaded {len(starters):,} games."
    )

    return pitches, starters


def run_score(runs):
    """
    Our bucketed starter-performance score.
    """

    if runs <= 2:
        return 1.0

    if runs == 3:
        return 0.8

    if runs == 4:
        return 0.6

    if runs == 5:
        return 0.4

    return 0.2


def continuous_run_score(runs):
    """
    Less abrupt version of the same idea.
    """

    return max(
        0.0,
        1.0 - (runs * 0.1)
    )


def build_starter_appearances(
    pitches,
    starters,
):

    print(
        "\nCalculating runs scored "
        "while each starter was pitching..."
    )

    rows = []

    valid_starters = starters.dropna(
        subset=[
            "home_starter_id",
            "away_starter_id",
        ]
    )

    for index, game in valid_starters.iterrows():

        if len(rows) % 500 == 0:
            print(
                f"Processed approximately "
                f"{len(rows):,} starter appearances"
            )

        game_pk = int(
            game["game_pk"]
        )

        game_pitches = pitches[
            pitches["game_pk"]
            == game_pk
        ].copy()

        # --------------------------------
        # HOME STARTER
        # Opponent is away team
        # --------------------------------

        home_id = int(
            game["home_starter_id"]
        )

        home_pitches = game_pitches[
            game_pitches["pitcher"]
            == home_id
        ].copy()

        if len(home_pitches) > 0:

            runs_allowed = (
                home_pitches[
                    "post_away_score"
                ].max()
                -
                home_pitches[
                    "post_away_score"
                ].min()
            )

            # If score began at zero while
            # starter was already pitching,
            # max is effectively runs scored.
            first_score = (
                home_pitches[
                    "post_away_score"
                ].iloc[0]
            )

            last_score = (
                home_pitches[
                    "post_away_score"
                ].iloc[-1]
            )

            runs_allowed = max(
                0,
                last_score - first_score,
            )

            rows.append(
                {
                    "game_pk": game_pk,
                    "date": game["date"],
                    "pitcher_id": home_id,
                    "pitcher_name":
                        game[
                            "home_starter_name"
                        ],
                    "team_side": "home",
                    "runs_allowed":
                        runs_allowed,
                }
            )

        # --------------------------------
        # AWAY STARTER
        # Opponent is home team
        # --------------------------------

        away_id = int(
            game["away_starter_id"]
        )

        away_pitches = game_pitches[
            game_pitches["pitcher"]
            == away_id
        ].copy()

        if len(away_pitches) > 0:

            first_score = (
                away_pitches[
                    "post_home_score"
                ].iloc[0]
            )

            last_score = (
                away_pitches[
                    "post_home_score"
                ].iloc[-1]
            )

            runs_allowed = max(
                0,
                last_score - first_score,
            )

            rows.append(
                {
                    "game_pk": game_pk,
                    "date": game["date"],
                    "pitcher_id": away_id,
                    "pitcher_name":
                        game[
                            "away_starter_name"
                        ],
                    "team_side": "away",
                    "runs_allowed":
                        runs_allowed,
                }
            )

    return pd.DataFrame(rows)


def build_history_features(
    appearances
):

    print(
        "\nBuilding historical starter scores..."
    )

    appearances = appearances.sort_values(
        [
            "date",
            "game_pk",
        ]
    )

    histories = {}

    rows = []

    for _, appearance in appearances.iterrows():

        pitcher_id = int(
            appearance["pitcher_id"]
        )

        if pitcher_id not in histories:
            histories[pitcher_id] = []

        history = histories[
            pitcher_id
        ]

        if len(history) > 0:

            season_bucket = sum(
                item["bucket_score"]
                for item in history
            ) / len(history)

            season_continuous = sum(
                item["continuous_score"]
                for item in history
            ) / len(history)

            season_runs = sum(
                item["runs_allowed"]
                for item in history
            ) / len(history)

            recent = history[
                -RECENT_STARTS:
            ]

            recent_bucket = sum(
                item["bucket_score"]
                for item in recent
            ) / len(recent)

            recent_continuous = sum(
                item["continuous_score"]
                for item in recent
            ) / len(recent)

            recent_runs = sum(
                item["runs_allowed"]
                for item in recent
            ) / len(recent)

        else:

            season_bucket = None
            season_continuous = None
            season_runs = None

            recent_bucket = None
            recent_continuous = None
            recent_runs = None

        rows.append(
            {
                "game_pk":
                    appearance["game_pk"],

                "date":
                    appearance["date"],

                "pitcher_id":
                    pitcher_id,

                "pitcher_name":
                    appearance[
                        "pitcher_name"
                    ],

                "team_side":
                    appearance[
                        "team_side"
                    ],

                "prior_starts":
                    len(history),

                "season_run_score":
                    season_bucket,

                "recent_run_score":
                    recent_bucket,

                "season_continuous_score":
                    season_continuous,

                "recent_continuous_score":
                    recent_continuous,

                "season_runs_allowed":
                    season_runs,

                "recent_runs_allowed":
                    recent_runs,
            }
        )

        runs = int(
            appearance[
                "runs_allowed"
            ]
        )

        history.append(
            {
                "runs_allowed":
                    runs,

                "bucket_score":
                    run_score(runs),

                "continuous_score":
                    continuous_run_score(
                        runs
                    ),
            }
        )

    return pd.DataFrame(rows)


def reshape(features):

    feature_columns = [
        "prior_starts",
        "season_run_score",
        "recent_run_score",
        "season_continuous_score",
        "recent_continuous_score",
        "season_runs_allowed",
        "recent_runs_allowed",
    ]

    home = features[
        features["team_side"]
        == "home"
    ].copy()

    away = features[
        features["team_side"]
        == "away"
    ].copy()

    home = home.rename(
        columns={
            "pitcher_name":
                "home_starter_name",

            **{
                column:
                    f"home_starter_{column}"
                for column
                in feature_columns
            }
        }
    )

    away = away.rename(
        columns={
            "pitcher_name":
                "away_starter_name",

            **{
                column:
                    f"away_starter_{column}"
                for column
                in feature_columns
            }
        }
    )

    home_columns = [
        "game_pk",
        "home_starter_name",
    ] + [
        f"home_starter_{column}"
        for column in feature_columns
    ]

    away_columns = [
        "game_pk",
        "away_starter_name",
    ] + [
        f"away_starter_{column}"
        for column in feature_columns
    ]

    return home[
        home_columns
    ].merge(
        away[
            away_columns
        ],
        on="game_pk",
        how="outer",
    )


def main():

    pitches, starters = load_data()

    appearances = (
        build_starter_appearances(
            pitches,
            starters,
        )
    )

    print(
        f"\nCreated "
        f"{len(appearances):,} "
        "starter appearances."
    )

    features = (
        build_history_features(
            appearances
        )
    )

    final = reshape(
        features
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nSAMPLE\n")

    columns = [
        "game_pk",

        "away_starter_name",
        "away_starter_prior_starts",
        "away_starter_season_run_score",
        "away_starter_recent_run_score",
        "away_starter_recent_runs_allowed",

        "home_starter_name",
        "home_starter_prior_starts",
        "home_starter_season_run_score",
        "home_starter_recent_run_score",
        "home_starter_recent_runs_allowed",
    ]

    print(
        final[
            columns
        ]
        .tail(15)
        .to_string(index=False)
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()