from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RUN_SCORES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliever_run_scores_2026.csv"
)

INHERITED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_inherited_runner_summary_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "bullpen_scores_2026.csv"
)


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print(
        "Loading reliever run-prevention scores..."
    )

    relievers = pd.read_csv(
        RUN_SCORES_FILE
    )

    print(
        f"Loaded {len(relievers):,} "
        f"qualified relievers."
    )

    print(
        "\nLoading inherited-runner team scores..."
    )

    inherited = pd.read_csv(
        INHERITED_FILE
    )

    print(
        f"Loaded {len(inherited):,} teams."
    )

    return relievers, inherited


# =========================================================
# BUILD TEAM RUN-PREVENTION DEPTH
# =========================================================

def build_team_depth(
    relievers,
):

    print(
        "\nBuilding bullpen depth..."
    )

    rows = []

    for team, group in relievers.groupby(
        "team"
    ):

        group = (
            group
            .sort_values(
                "run_prevention_score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        # -----------------------------------------
        # BEST RELIEVER
        # -----------------------------------------

        best_reliever = (
            group.iloc[0]
        )

        best_score = (
            best_reliever[
                "run_prevention_score"
            ]
        )

        # -----------------------------------------
        # TOP 3
        # -----------------------------------------

        top_three = (
            group
            .head(3)
        )

        top_three_score = (
            top_three[
                "run_prevention_score"
            ]
            .mean()
        )

        # -----------------------------------------
        # TOP 5
        # -----------------------------------------

        top_five = (
            group
            .head(5)
        )

        top_five_score = (
            top_five[
                "run_prevention_score"
            ]
            .mean()
        )

        # -----------------------------------------
        # NAMES
        # -----------------------------------------

        top_five_names = (
            top_five[
                "pitcher_name"
            ]
            .tolist()
        )

        rows.append(
            {
                "team":
                    team,

                "best_reliever":
                    best_reliever[
                        "pitcher_name"
                    ],

                "best_reliever_score":
                    best_score,

                "top_3_run_prevention":
                    top_three_score,

                "top_5_run_prevention":
                    top_five_score,

                "qualified_relievers":
                    len(group),

                "projected_top_5":
                    " | ".join(
                        top_five_names
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


# =========================================================
# NORMALIZE STRAND RATE
# =========================================================

def add_strand_score(
    inherited,
):

    inherited = inherited.copy()

    low = (
        inherited[
            "strand_rate"
        ]
        .min()
    )

    high = (
        inherited[
            "strand_rate"
        ]
        .max()
    )

    if high == low:

        inherited[
            "strand_score"
        ] = 50.0

    else:

        inherited[
            "strand_score"
        ] = (
            (
                inherited[
                    "strand_rate"
                ]
                - low
            )
            /
            (
                high
                - low
            )
            *
            100
        )

    return inherited


# =========================================================
# COMBINE DATA
# =========================================================

def build_board(
    depth,
    inherited,
):

    inherited = add_strand_score(
        inherited
    )

    inherited_columns = [
        "team",
        "inherited_runners",
        "inherited_scored",
        "inherited_stranded",
        "strand_rate",
        "strand_score",
    ]

    board = depth.merge(
        inherited[
            inherited_columns
        ],
        on="team",
        how="left",
    )

    return board


# =========================================================
# MAIN
# =========================================================

def main():

    relievers, inherited = (
        load_data()
    )

    depth = build_team_depth(
        relievers
    )

    board = build_board(
        depth,
        inherited,
    )

    # -----------------------------------------
    # TEMPORARY NEUTRAL SCORE
    #
    # This is ONLY for inspection.
    # We are not locking in final bullpen
    # weights yet.
    # -----------------------------------------

    board[
        "neutral_bullpen_score"
    ] = (
        board[
            "best_reliever_score"
        ]
        * 0.25
        +
        board[
            "top_3_run_prevention"
        ]
        * 0.30
        +
        board[
            "top_5_run_prevention"
        ]
        * 0.30
        +
        board[
            "strand_score"
        ]
        * 0.15
    )

    board = (
        board
        .sort_values(
            "neutral_bullpen_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    board.insert(
        0,
        "bullpen_rank",
        range(
            1,
            len(board) + 1,
        ),
    )

    print()
    print(
        "=" * 105
    )

    print(
        "OCTOBER SHIFT // "
        "NEUTRAL BULLPEN BOARD"
    )

    print(
        "=" * 105
    )

    print()

    columns = [
        "bullpen_rank",
        "team",
        "best_reliever",
        "best_reliever_score",
        "top_3_run_prevention",
        "top_5_run_prevention",
        "strand_rate",
        "strand_score",
        "qualified_relievers",
        "neutral_bullpen_score",
    ]

    print(
        board[
            columns
        ]
        .to_string(
            index=False
        )
    )

    print()
    print(
        "=" * 105
    )

    print(
        "TOP FIVE RELIEVERS BY TEAM"
    )

    print(
        "=" * 105
    )

    print()

    print(
        board[
            [
                "bullpen_rank",
                "team",
                "projected_top_5",
            ]
        ]
        .head(15)
        .to_string(
            index=False
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    board.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()