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
    / "pitcher_features_2026.csv"
)


HIT_EVENTS = {
    "single",
    "double",
    "triple",
    "home_run",
}

WALK_EVENTS = {
    "walk",
    "intent_walk",
}

STRIKEOUT_EVENTS = {
    "strikeout",
    "strikeout_double_play",
}


def load_data():
    print("Loading pitching data...")

    pitches = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters = pd.read_csv(
        STARTERS_FILE,
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
        f"Loaded {len(starters):,} games with starter info."
    )

    return pitches, starters


def build_game_lines(pitches, starters):
    print("\nBuilding starter game lines...")

    starter_rows = []

    for _, game in starters.dropna(
        subset=[
            "home_starter_id",
            "away_starter_id",
        ]
    ).iterrows():

        game_pk = int(game["game_pk"])

        starter_rows.append(
            {
                "game_pk": game_pk,
                "date": game["date"],
                "pitcher_id": int(
                    game["home_starter_id"]
                ),
                "pitcher_name":
                    game["home_starter_name"],
                "team_side": "home",
            }
        )

        starter_rows.append(
            {
                "game_pk": game_pk,
                "date": game["date"],
                "pitcher_id": int(
                    game["away_starter_id"]
                ),
                "pitcher_name":
                    game["away_starter_name"],
                "team_side": "away",
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

    print(
        f"Found {len(starter_pitches):,} "
        "pitches thrown by starters."
    )

    plate_appearances = (
        starter_pitches
        .dropna(subset=["events"])
        .copy()
    )

    game_lines = []

    grouped = starter_pitches.groupby(
        [
            "game_pk",
            "pitcher_id",
        ]
    )

    print(
        f"Building {len(grouped):,} "
        "starter appearances..."
    )

    for (
        game_pk,
        pitcher_id,
    ), pitcher_game in grouped:

        info = starter_index[
            (
                starter_index["game_pk"]
                == game_pk
            )
            & (
                starter_index["pitcher_id"]
                == pitcher_id
            )
        ].iloc[0]

        pa = plate_appearances[
            (
                plate_appearances["game_pk"]
                == game_pk
            )
            & (
                plate_appearances["pitcher"]
                == pitcher_id
            )
        ]

        events = pa["events"].fillna("")

        game_lines.append(
            {
                "game_pk": game_pk,
                "date": info["date"],
                "pitcher_id": pitcher_id,
                "pitcher_name":
                    info["pitcher_name"],
                "team_side":
                    info["team_side"],

                "batters_faced":
                    len(pa),

                "strikeouts":
                    events.isin(
                        STRIKEOUT_EVENTS
                    ).sum(),

                "walks":
                    events.isin(
                        WALK_EVENTS
                    ).sum(),

                "hits":
                    events.isin(
                        HIT_EVENTS
                    ).sum(),

                "home_runs":
                    (
                        events
                        == "home_run"
                    ).sum(),

                "hit_by_pitch":
                    (
                        events
                        == "hit_by_pitch"
                    ).sum(),

                "pitch_count":
                    len(pitcher_game),
            }
        )

    return pd.DataFrame(
        game_lines
    )


def summarize_history(history):
    if len(history) == 0:
        return {
            "k_rate": None,
            "walk_rate": None,
            "hit_rate": None,
            "hr_rate": None,
            "baserunner_rate": None,
            "pitches_per_batter": None,
            "batters_faced": 0,
        }

    batters_faced = history[
        "batters_faced"
    ].sum()

    if batters_faced == 0:
        return {
            "k_rate": None,
            "walk_rate": None,
            "hit_rate": None,
            "hr_rate": None,
            "baserunner_rate": None,
            "pitches_per_batter": None,
            "batters_faced": 0,
        }

    strikeouts = history[
        "strikeouts"
    ].sum()

    walks = history[
        "walks"
    ].sum()

    hits = history[
        "hits"
    ].sum()

    home_runs = history[
        "home_runs"
    ].sum()

    hit_by_pitch = history[
        "hit_by_pitch"
    ].sum()

    pitch_count = history[
        "pitch_count"
    ].sum()

    return {
        "k_rate":
            strikeouts / batters_faced,

        "walk_rate":
            walks / batters_faced,

        "hit_rate":
            hits / batters_faced,

        "hr_rate":
            home_runs / batters_faced,

        "baserunner_rate":
            (
                walks
                + hits
                + hit_by_pitch
            )
            / batters_faced,

        "pitches_per_batter":
            pitch_count
            / batters_faced,

        "batters_faced":
            batters_faced,
    }


def build_pre_game_features(game_lines):
    print(
        "\nBuilding season and recent "
        "pitcher history..."
    )

    game_lines = game_lines.sort_values(
        [
            "date",
            "game_pk",
        ]
    ).reset_index(drop=True)

    pitcher_histories = {}

    rows = []

    for _, appearance in game_lines.iterrows():

        pitcher_id = int(
            appearance["pitcher_id"]
        )

        if pitcher_id not in pitcher_histories:
            pitcher_histories[
                pitcher_id
            ] = []

        history = pitcher_histories[
            pitcher_id
        ]

        history_df = pd.DataFrame(
            history
        )

        season_stats = summarize_history(
            history_df
        )

        recent_history = (
            history_df.tail(3)
            if len(history_df) > 0
            else history_df
        )

        recent_stats = summarize_history(
            recent_history
        )

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

                # ----------------------
                # SEASON-TO-DATE
                # ----------------------

                "season_k_rate":
                    season_stats[
                        "k_rate"
                    ],

                "season_walk_rate":
                    season_stats[
                        "walk_rate"
                    ],

                "season_baserunner_rate":
                    season_stats[
                        "baserunner_rate"
                    ],

                "season_hr_rate":
                    season_stats[
                        "hr_rate"
                    ],

                "season_pitches_per_batter":
                    season_stats[
                        "pitches_per_batter"
                    ],

                # ----------------------
                # LAST 3 STARTS
                # ----------------------

                "recent_k_rate":
                    recent_stats[
                        "k_rate"
                    ],

                "recent_walk_rate":
                    recent_stats[
                        "walk_rate"
                    ],

                "recent_baserunner_rate":
                    recent_stats[
                        "baserunner_rate"
                    ],

                "recent_hr_rate":
                    recent_stats[
                        "hr_rate"
                    ],

                "recent_pitches_per_batter":
                    recent_stats[
                        "pitches_per_batter"
                    ],

                "recent_batters_faced":
                    recent_stats[
                        "batters_faced"
                    ],
            }
        )

        history.append(
            {
                "batters_faced":
                    appearance[
                        "batters_faced"
                    ],

                "strikeouts":
                    appearance[
                        "strikeouts"
                    ],

                "walks":
                    appearance[
                        "walks"
                    ],

                "hits":
                    appearance[
                        "hits"
                    ],

                "home_runs":
                    appearance[
                        "home_runs"
                    ],

                "hit_by_pitch":
                    appearance[
                        "hit_by_pitch"
                    ],

                "pitch_count":
                    appearance[
                        "pitch_count"
                    ],
            }
        )

    return pd.DataFrame(
        rows
    )


def reshape_for_games(features):
    home = features[
        features["team_side"]
        == "home"
    ].copy()

    away = features[
        features["team_side"]
        == "away"
    ].copy()

    feature_columns = [
        "prior_starts",

        "season_k_rate",
        "season_walk_rate",
        "season_baserunner_rate",
        "season_hr_rate",
        "season_pitches_per_batter",

        "recent_k_rate",
        "recent_walk_rate",
        "recent_baserunner_rate",
        "recent_hr_rate",
        "recent_pitches_per_batter",
        "recent_batters_faced",
    ]

    home = home.rename(
        columns={
            "pitcher_id":
                "home_starter_id",

            "pitcher_name":
                "home_starter_name",

            **{
                column:
                    f"home_starter_{column}"
                for column
                in feature_columns
            },
        }
    )

    away = away.rename(
        columns={
            "pitcher_id":
                "away_starter_id",

            "pitcher_name":
                "away_starter_name",

            **{
                column:
                    f"away_starter_{column}"
                for column
                in feature_columns
            },
        }
    )

    home_columns = [
        "game_pk",
        "home_starter_id",
        "home_starter_name",
    ] + [
        f"home_starter_{column}"
        for column
        in feature_columns
    ]

    away_columns = [
        "game_pk",
        "away_starter_id",
        "away_starter_name",
    ] + [
        f"away_starter_{column}"
        for column
        in feature_columns
    ]

    final = home[
        home_columns
    ].merge(
        away[
            away_columns
        ],
        on="game_pk",
        how="outer",
    )

    return final


def main():

    pitches, starters = load_data()

    game_lines = build_game_lines(
        pitches,
        starters,
    )

    features = build_pre_game_features(
        game_lines
    )

    final = reshape_for_games(
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

    print(
        f"\nCreated pitcher features "
        f"for {len(final):,} games."
    )

    print("\nSAMPLE\n")

    display_columns = [
        "game_pk",

        "away_starter_name",
        "away_starter_prior_starts",
        "away_starter_season_k_rate",
        "away_starter_recent_k_rate",
        "away_starter_recent_baserunner_rate",

        "home_starter_name",
        "home_starter_prior_starts",
        "home_starter_season_k_rate",
        "home_starter_recent_k_rate",
        "home_starter_recent_baserunner_rate",
    ]

    print(
        final[
            display_columns
        ]
        .tail(15)
        .to_string(index=False)
    )

    print("\nRECENT PITCHING MISSING VALUES\n")

    print(
        final[
            [
                "away_starter_recent_k_rate",
                "home_starter_recent_k_rate",
            ]
        ]
        .isna()
        .sum()
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()