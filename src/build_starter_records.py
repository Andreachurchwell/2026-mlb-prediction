from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
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
    / "starter_records_2026.csv"
)


ALL_STAR_DATE = pd.Timestamp(
    "2026-07-14"
)

PRE_ASB_WEIGHT = 0.5
POST_ASB_WEIGHT = 1.0

RECENT_STARTS = 5


def load_data():

    print("Loading games...")

    games = pd.read_csv(
        GAMES_FILE
    )

    starters = pd.read_csv(
        STARTERS_FILE
    )

    games["date"] = pd.to_datetime(
        games["date"]
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    print(
        f"Loaded {len(games):,} games."
    )

    print(
        f"Loaded starter info for "
        f"{len(starters):,} games."
    )

    return games, starters


def merge_data(games, starters):

    starter_columns = [
        "game_pk",
        "home_starter_id",
        "home_starter_name",
        "away_starter_id",
        "away_starter_name",
    ]

    starters = starters[
        starter_columns
    ].copy()

    starters = starters.rename(
        columns={
            "game_pk": "game_id"
        }
    )

    df = games.merge(
        starters,
        on="game_id",
        how="left",
    )

    df = df.sort_values(
        [
            "date",
            "game_id",
        ]
    ).reset_index(drop=True)

    return df


def make_state():

    return {
        "starts": 0,
        "team_wins": 0,

        "weighted_wins": 0.0,
        "total_weight": 0.0,

        "results": [],
    }


def get_features(state):

    if state["starts"] == 0:

        return {
            "starts": 0,
            "team_win_pct": None,
            "weighted_team_win_pct": None,
            "recent_team_win_pct": None,
        }

    recent_results = (
        state["results"][
            -RECENT_STARTS:
        ]
    )

    return {
        "starts":
            state["starts"],

        "team_win_pct":
            (
                state["team_wins"]
                / state["starts"]
            ),

        "weighted_team_win_pct":
            (
                state["weighted_wins"]
                / state["total_weight"]
            ),

        "recent_team_win_pct":
            (
                sum(recent_results)
                / len(recent_results)
            ),
    }


def update_state(
    state,
    team_win,
    game_date,
):

    if game_date > ALL_STAR_DATE:

        weight = POST_ASB_WEIGHT

    else:

        weight = PRE_ASB_WEIGHT

    state["starts"] += 1

    state["team_wins"] += (
        team_win
    )

    state["weighted_wins"] += (
        team_win * weight
    )

    state["total_weight"] += (
        weight
    )

    state["results"].append(
        team_win
    )


def build_starter_records(df):

    pitcher_states = {}

    rows = []

    for index, game in df.iterrows():

        if index % 250 == 0:

            print(
                f"Processing game "
                f"{index:,} / "
                f"{len(df):,}"
            )

        home_id = (
            game["home_starter_id"]
        )

        away_id = (
            game["away_starter_id"]
        )

        # Missing starter information
        if (
            pd.isna(home_id)
            or pd.isna(away_id)
        ):
            continue

        home_id = int(home_id)
        away_id = int(away_id)

        if home_id not in pitcher_states:
            pitcher_states[
                home_id
            ] = make_state()

        if away_id not in pitcher_states:
            pitcher_states[
                away_id
            ] = make_state()

        home_state = pitcher_states[
            home_id
        ]

        away_state = pitcher_states[
            away_id
        ]

        # --------------------------------
        # FEATURES BEFORE THIS GAME
        # --------------------------------

        home_features = get_features(
            home_state
        )

        away_features = get_features(
            away_state
        )

        rows.append(
            {
                "game_id":
                    game["game_id"],

                "date":
                    game["date"],

                "home_team":
                    game["home_team"],

                "away_team":
                    game["away_team"],

                "home_starter_id":
                    home_id,

                "home_starter_name":
                    game[
                        "home_starter_name"
                    ],

                "away_starter_id":
                    away_id,

                "away_starter_name":
                    game[
                        "away_starter_name"
                    ],

                # HOME STARTER

                "home_starter_prior_starts":
                    home_features[
                        "starts"
                    ],

                "home_starter_team_win_pct":
                    home_features[
                        "team_win_pct"
                    ],

                "home_starter_weighted_team_win_pct":
                    home_features[
                        "weighted_team_win_pct"
                    ],

                "home_starter_recent_team_win_pct":
                    home_features[
                        "recent_team_win_pct"
                    ],

                # AWAY STARTER

                "away_starter_prior_starts":
                    away_features[
                        "starts"
                    ],

                "away_starter_team_win_pct":
                    away_features[
                        "team_win_pct"
                    ],

                "away_starter_weighted_team_win_pct":
                    away_features[
                        "weighted_team_win_pct"
                    ],

                "away_starter_recent_team_win_pct":
                    away_features[
                        "recent_team_win_pct"
                    ],
            }
        )

        # --------------------------------
        # GAME RESULT
        # --------------------------------

        home_win = int(
            game["home_score"]
            > game["away_score"]
        )

        away_win = 1 - home_win

        # --------------------------------
        # UPDATE ONLY AFTER FEATURES
        # --------------------------------

        update_state(
            home_state,
            home_win,
            game["date"],
        )

        update_state(
            away_state,
            away_win,
            game["date"],
        )

    return pd.DataFrame(
        rows
    )


def main():

    games, starters = load_data()

    df = merge_data(
        games,
        starters,
    )

    print(
        "\nBuilding starter records...\n"
    )

    records = build_starter_records(
        df
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    records.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nCreated starter records "
        f"for {len(records):,} games."
    )

    print("\nSAMPLE\n")

    display_columns = [
        "date",

        "away_starter_name",
        "away_starter_prior_starts",
        "away_starter_team_win_pct",
        "away_starter_weighted_team_win_pct",
        "away_starter_recent_team_win_pct",

        "home_starter_name",
        "home_starter_prior_starts",
        "home_starter_team_win_pct",
        "home_starter_weighted_team_win_pct",
        "home_starter_recent_team_win_pct",
    ]

    print(
        records[
            display_columns
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