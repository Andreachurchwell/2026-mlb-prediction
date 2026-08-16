from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "games_2026.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "team_stats_2026.csv"

ALL_STAR_DATE = pd.Timestamp("2026-07-14")

PRE_ASB_WEIGHT = 0.5
POST_ASB_WEIGHT = 1.0


def load_games():
    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])

    return df


def create_team_game_rows(df):
    """
    Convert each MLB game into two rows:
    one from the home team's perspective
    and one from the away team's perspective.
    """

    home = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "date": df["date"],
            "team": df["home_team"],
            "opponent": df["away_team"],
            "runs_scored": df["home_score"],
            "runs_allowed": df["away_score"],
            "home": 1,
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
            "home": 0,
        }
    )

    team_games = pd.concat([home, away], ignore_index=True)

    team_games["win"] = (
        team_games["runs_scored"] > team_games["runs_allowed"]
    ).astype(int)

    team_games["run_diff"] = (
        team_games["runs_scored"] - team_games["runs_allowed"]
    )

    team_games["post_asb"] = (
        team_games["date"] > ALL_STAR_DATE
    ).astype(int)

    team_games["game_weight"] = team_games["post_asb"].map(
        {
            0: PRE_ASB_WEIGHT,
            1: POST_ASB_WEIGHT,
        }
    )

    team_games = team_games.sort_values(
        ["team", "date", "game_id"]
    ).reset_index(drop=True)

    return team_games


def build_team_stats(team_games):
    rows = []

    for team, games in team_games.groupby("team"):

        games = games.sort_values("date")

        total_games = len(games)
        wins = games["win"].sum()
        losses = total_games - wins

        pre_asb = games[games["post_asb"] == 0]
        post_asb = games[games["post_asb"] == 1]

        last_10 = games.tail(10)

        weighted_wins = (
            games["win"] * games["game_weight"]
        ).sum()

        total_weight = games["game_weight"].sum()

        weighted_win_pct = (
            weighted_wins / total_weight
            if total_weight > 0
            else 0
        )

        rows.append(
            {
                "team": team,

                "games": total_games,
                "wins": wins,
                "losses": losses,

                "win_pct": wins / total_games,

                "runs_scored": games["runs_scored"].sum(),
                "runs_allowed": games["runs_allowed"].sum(),

                "run_diff": games["run_diff"].sum(),

                "runs_per_game": (
                    games["runs_scored"].mean()
                ),

                "runs_allowed_per_game": (
                    games["runs_allowed"].mean()
                ),

                "pre_asb_win_pct": (
                    pre_asb["win"].mean()
                    if len(pre_asb) > 0
                    else 0
                ),

                "post_asb_win_pct": (
                    post_asb["win"].mean()
                    if len(post_asb) > 0
                    else 0
                ),

                "last_10_win_pct": (
                    last_10["win"].mean()
                    if len(last_10) > 0
                    else 0
                ),

                "weighted_win_pct": weighted_win_pct,
            }
        )

    stats = pd.DataFrame(rows)

    stats = stats.sort_values(
        "weighted_win_pct",
        ascending=False
    ).reset_index(drop=True)

    return stats


def main():
    print("Loading 2026 MLB games...")

    games = load_games()

    print(f"Loaded {len(games):,} games.")

    team_games = create_team_game_rows(games)

    print(
        f"Created {len(team_games):,} team-game observations."
    )

    stats = build_team_stats(team_games)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stats.to_csv(OUTPUT_FILE, index=False)

    print("\nTOP 10 BY WEIGHTED WIN PERCENTAGE\n")

    print(
        stats[
            [
                "team",
                "wins",
                "losses",
                "win_pct",
                "pre_asb_win_pct",
                "post_asb_win_pct",
                "last_10_win_pct",
                "weighted_win_pct",
                "run_diff",
            ]
        ].head(10).to_string(index=False)
    )

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()