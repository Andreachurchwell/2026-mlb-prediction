import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "games_2026.csv"


def main():
    df = pd.read_csv(DATA_FILE)

    print("\nSHAPE")
    print(df.shape)

    print("\nCOLUMNS")
    print(df.columns.tolist())

    print("\nMISSING VALUES")
    print(df.isna().sum())

    print("\nDUPLICATE GAME IDS")
    print(df["game_id"].duplicated().sum())

    print("\nNUMBER OF TEAMS")
    teams = sorted(
        set(df["home_team"].dropna())
        | set(df["away_team"].dropna())
    )

    print(len(teams))

    for team in teams:
        print(team)

    print("\nDATE RANGE")
    print("First game:", df["date"].min())
    print("Latest game:", df["date"].max())

    print("\nSAMPLE")
    print(df.sample(10, random_state=42))


if __name__ == "__main__":
    main()