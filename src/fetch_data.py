from pathlib import Path

import pandas as pd
import requests


SEASON = 2026

BASE_URL = "https://statsapi.mlb.com/api/v1/schedule"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "games_2026.csv"


def fetch_schedule():
    params = {
        "sportId": 1,
        "season": SEASON,
        "gameType": "R",
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def parse_games(schedule_data):
    games = []

    for date_group in schedule_data.get("dates", []):
        game_date = date_group.get("date")

        for game in date_group.get("games", []):
            status = game.get("status", {}).get("detailedState")

            # Only keep finished games
            if status not in {"Final", "Game Over", "Completed Early"}:
                continue

            home = game.get("teams", {}).get("home", {})
            away = game.get("teams", {}).get("away", {})

            home_team = home.get("team", {}).get("name")
            away_team = away.get("team", {}).get("name")

            home_score = home.get("score")
            away_score = away.get("score")

            if home_score is None or away_score is None:
                continue

            if home_score > away_score:
                winner = home_team
            else:
                winner = away_team

            games.append(
                {
                    "game_id": game.get("gamePk"),
                    "date": game_date,
                    "away_team": away_team,
                    "away_score": away_score,
                    "home_team": home_team,
                    "home_score": home_score,
                    "winner": winner,
                    "status": status,
                }
            )

    return pd.DataFrame(games)


def save_games(df):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = df.drop_duplicates(subset="game_id")
    df = df.sort_values(["date", "game_id"])

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(df):,} completed games.")
    print(f"File: {OUTPUT_FILE}")


def main():
    print("Fetching 2026 MLB games...")

    schedule_data = fetch_schedule()
    games_df = parse_games(schedule_data)

    if games_df.empty:
        print("No completed games were returned.")
        return

    print()
    print(games_df.head())
    print()

    save_games(games_df)


if __name__ == "__main__":
    main()