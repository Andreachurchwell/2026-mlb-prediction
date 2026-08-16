from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PITCHING_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)


def load_data():

    print("Loading pitching data...")

    pitches = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    games = pd.read_csv(
        GAMES_FILE
    )

    print(
        f"Loaded {len(pitches):,} pitches."
    )

    print(
        f"Loaded {len(games):,} games."
    )

    return pitches, games


def find_starters(pitches):

    print("\nFinding starting pitchers...")

    # Sort pitches so the first pitch
    # of each half inning appears first.
    pitches = pitches.sort_values(
        [
            "game_date",
            "game_pk",
            "inning",
            "at_bat_number",
            "pitch_number",
        ]
    )

    # -----------------------------
    # HOME STARTER
    # -----------------------------
    # Home team pitches in the
    # TOP of the first inning.

    home_starters = (
        pitches[
            (pitches["inning"] == 1)
            & (pitches["inning_topbot"] == "Top")
        ]
        .groupby("game_pk")
        .first()
        .reset_index()
    )

    home_starters = home_starters[
        [
            "game_pk",
            "pitcher",
            "player_name",
        ]
    ].rename(
        columns={
            "pitcher":
                "home_starter_id",

            "player_name":
                "home_starter_name",
        }
    )

    # -----------------------------
    # AWAY STARTER
    # -----------------------------
    # Away team pitches in the
    # BOTTOM of the first inning.

    away_starters = (
        pitches[
            (pitches["inning"] == 1)
            & (pitches["inning_topbot"] == "Bot")
        ]
        .groupby("game_pk")
        .first()
        .reset_index()
    )

    away_starters = away_starters[
        [
            "game_pk",
            "pitcher",
            "player_name",
        ]
    ].rename(
        columns={
            "pitcher":
                "away_starter_id",

            "player_name":
                "away_starter_name",
        }
    )

    starters = home_starters.merge(
        away_starters,
        on="game_pk",
        how="outer",
    )

    return starters


def add_game_information(
    starters,
    games,
):

    games = games[
        [
            "game_id",
            "date",
            "home_team",
            "away_team",
        ]
    ].copy()

    games = games.rename(
        columns={
            "game_id": "game_pk"
        }
    )

    starters = games.merge(
        starters,
        on="game_pk",
        how="left",
    )

    return starters


def main():

    pitches, games = load_data()

    starters = find_starters(
        pitches
    )

    starters = add_game_information(
        starters,
        games,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    starters.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nSAMPLE STARTERS\n")

    print(
        starters[
            [
                "date",
                "away_team",
                "away_starter_name",
                "home_team",
                "home_starter_name",
            ]
        ]
        .tail(15)
        .to_string(index=False)
    )

    print("\nMISSING STARTERS")

    print(
        starters[
            [
                "away_starter_name",
                "home_starter_name",
            ]
        ]
        .isna()
        .sum()
    )

    print(
        f"\nSaved {len(starters):,} games."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()