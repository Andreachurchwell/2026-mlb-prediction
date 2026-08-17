from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BOARD_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contender_scores_2026.csv"
)

HISTORY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ranking_history_2026.csv"
)

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
)


def main():

    print("Saving October Shift ranking history...")

    board = pd.read_csv(
        BOARD_FILE
    )

    games = pd.read_csv(
        GAMES_FILE
    )

    games["date"] = pd.to_datetime(
        games["date"]
    )

    snapshot_date = (
        games["date"]
        .max()
        .date()
        .isoformat()
    )

    print(
        f"Snapshot date: "
        f"{snapshot_date}"
    )

    columns = [
        "team",
        "rank",
        "october_shift_score",
        "wins",
        "losses",
        "projected_rotation_rank",
        "projected_rotation_score",
    ]

    snapshot = (
        board[
            columns
        ]
        .copy()
    )

    snapshot.insert(
        0,
        "snapshot_date",
        snapshot_date,
    )

    # --------------------------------
    # LOAD EXISTING HISTORY
    # --------------------------------

    if HISTORY_FILE.exists():

        history = pd.read_csv(
            HISTORY_FILE
        )

        # If today's snapshot already exists,
        # replace it instead of duplicating it.
        history = history[
            history[
                "snapshot_date"
            ].astype(str)
            != snapshot_date
        ]

        history = pd.concat(
            [
                history,
                snapshot,
            ],
            ignore_index=True,
        )

    else:

        history = snapshot

    # --------------------------------
    # SORT
    # --------------------------------

    history[
        "snapshot_date"
    ] = pd.to_datetime(
        history[
            "snapshot_date"
        ]
    )

    history = (
        history
        .sort_values(
            [
                "snapshot_date",
                "rank",
            ]
        )
        .reset_index(drop=True)
    )

    history[
        "snapshot_date"
    ] = (
        history[
            "snapshot_date"
        ]
        .dt.date
        .astype(str)
    )

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    history.to_csv(
        HISTORY_FILE,
        index=False,
    )

    print(
        f"Saved {len(snapshot)} teams."
    )

    print(
        f"Total history rows: "
        f"{len(history)}"
    )

    print(
        f"File: "
        f"{HISTORY_FILE}"
    )


if __name__ == "__main__":
    main()