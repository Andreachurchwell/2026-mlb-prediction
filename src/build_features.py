from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GAMES_FILE = PROJECT_ROOT / "data" / "raw" / "games_2026.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "team_features_2026.csv"


def load_games():
    df = pd.read_csv(GAMES_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df


def create_team_games(df):
    """
    Turn each MLB game into two rows:
    one for the home team and one for the away team.
    """

    home = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "date": df["date"],
            "team": df["home_team"],
            "opponent": df["away_team"],
            "runs_scored": df["home_score"],
            "runs_allowed": df["away_score"],
        }
    )

    away = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "date": df["date"],
            "team": df["away_team"],
            "opponent": df["home_team"],
            "runs_scored": df["away_score"],
            "runs_allowed": df["home_score"],
        }
    )

    team_games = pd.concat([home, away], ignore_index=True)

    team_games["win"] = (
        team_games["runs_scored"] > team_games["runs_allowed"]
    ).astype(int)

    return team_games


def calculate_team_records(team_games):
    """
    Calculate each team's current winning percentage.
    """

    records = (
        team_games.groupby("team")
        .agg(
            games=("win", "count"),
            wins=("win", "sum"),
        )
        .reset_index()
    )

    records["win_pct"] = records["wins"] / records["games"]

    return records


def add_opponent_strength(team_games, records):
    """
    Attach each opponent's winning percentage to every game.
    """

    opponent_records = records[
        ["team", "win_pct"]
    ].rename(
        columns={
            "team": "opponent",
            "win_pct": "opponent_win_pct",
        }
    )

    return team_games.merge(
        opponent_records,
        on="opponent",
        how="left",
    )


def build_team_features(team_games):
    """
    Build strength-of-schedule and quality-win features.
    """

    # A quality win = beating a team currently above .500
    team_games["quality_win"] = (
        (team_games["win"] == 1)
        & (team_games["opponent_win_pct"] > 0.500)
    ).astype(int)

    features = (
        team_games.groupby("team")
        .agg(
            strength_of_schedule=(
                "opponent_win_pct",
                "mean",
            ),
            quality_wins=(
                "quality_win",
                "sum",
            ),
        )
        .reset_index()
    )

    return features


def main():
    print("Loading games...")

    games = load_games()

    print(f"Loaded {len(games):,} games.")

    team_games = create_team_games(games)

    records = calculate_team_records(team_games)

    team_games = add_opponent_strength(
        team_games,
        records,
    )

    features = build_team_features(team_games)

    # Bring in the stats we made in the previous step
    stats_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "team_stats_2026.csv"
    )

    stats = pd.read_csv(stats_file)

    final = stats.merge(
        features,
        on="team",
        how="left",
    )

    final = final.sort_values(
        "weighted_win_pct",
        ascending=False,
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    final.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nTOP 10\n")

    columns = [
        "team",
        "wins",
        "losses",
        "weighted_win_pct",
        "strength_of_schedule",
        "quality_wins",
        "run_diff",
    ]

    print(
        final[columns]
        .head(10)
        .to_string(index=False)
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()