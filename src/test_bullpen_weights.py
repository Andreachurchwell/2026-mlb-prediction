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

BULLPEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "bullpen_scores_2026.csv"
)


# =========================================================
# LOAD
# =========================================================

def load_data():

    print(
        "Loading bullpen board..."
    )

    bullpen = pd.read_csv(
        BULLPEN_FILE
    )

    print(
        f"Loaded {len(bullpen):,} teams."
    )

    return bullpen


# =========================================================
# WEIGHT TESTS
# =========================================================

WEIGHT_TESTS = {
    "A": {
        "best":
            0.30,

        "top3":
            0.30,

        "top5":
            0.30,

        "strand":
            0.10,
    },

    "B": {
        "best":
            0.20,

        "top3":
            0.35,

        "top5":
            0.35,

        "strand":
            0.10,
    },

    "C": {
        "best":
            0.25,

        "top3":
            0.30,

        "top5":
            0.25,

        "strand":
            0.20,
    },

    "D": {
        "best":
            0.20,

        "top3":
            0.30,

        "top5":
            0.40,

        "strand":
            0.10,
    },
}


# =========================================================
# CALCULATE SCORES
# =========================================================

def build_tests(
    bullpen,
):

    result = bullpen.copy()

    for label, weights in (
        WEIGHT_TESTS.items()
    ):

        score_column = (
            f"score_{label}"
        )

        rank_column = (
            f"rank_{label}"
        )

        result[
            score_column
        ] = (
            result[
                "best_reliever_score"
            ]
            * weights[
                "best"
            ]

            +

            result[
                "top_3_run_prevention"
            ]
            * weights[
                "top3"
            ]

            +

            result[
                "top_5_run_prevention"
            ]
            * weights[
                "top5"
            ]

            +

            result[
                "strand_score"
            ]
            * weights[
                "strand"
            ]
        )

        result[
            rank_column
        ] = (
            result[
                score_column
            ]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

    return result


# =========================================================
# PRINT EACH VERSION
# =========================================================

def print_versions(
    result,
):

    for label, weights in (
        WEIGHT_TESTS.items()
    ):

        print()
        print(
            "=" * 100
        )

        print(
            f"VERSION {label}"
        )

        print(
            f"BEST {weights['best']:.0%} // "
            f"TOP 3 {weights['top3']:.0%} // "
            f"TOP 5 {weights['top5']:.0%} // "
            f"STRAND {weights['strand']:.0%}"
        )

        print(
            "=" * 100
        )

        score_column = (
            f"score_{label}"
        )

        rank_column = (
            f"rank_{label}"
        )

        display = (
            result[
                [
                    "team",
                    "best_reliever_score",
                    "top_3_run_prevention",
                    "top_5_run_prevention",
                    "strand_score",
                    score_column,
                    rank_column,
                ]
            ]
            .sort_values(
                rank_column
            )
            .head(15)
            .rename(
                columns={
                    score_column:
                        "combined_score",

                    rank_column:
                        "rank",
                }
            )
        )

        print(
            display.to_string(
                index=False,
                formatters={
                    "best_reliever_score":
                        "{:.1f}".format,

                    "top_3_run_prevention":
                        "{:.1f}".format,

                    "top_5_run_prevention":
                        "{:.1f}".format,

                    "strand_score":
                        "{:.1f}".format,

                    "combined_score":
                        "{:.1f}".format,
                }
            )
        )


# =========================================================
# SENSITIVITY TABLE
# =========================================================

def build_sensitivity(
    result,
):

    comparison = result[
        [
            "team",
            "rank_A",
            "rank_B",
            "rank_C",
            "rank_D",
        ]
    ].copy()

    rank_columns = [
        "rank_A",
        "rank_B",
        "rank_C",
        "rank_D",
    ]

    comparison[
        "best_rank"
    ] = (
        comparison[
            rank_columns
        ]
        .min(
            axis=1
        )
    )

    comparison[
        "worst_rank"
    ] = (
        comparison[
            rank_columns
        ]
        .max(
            axis=1
        )
    )

    comparison[
        "rank_swing"
    ] = (
        comparison[
            "worst_rank"
        ]
        -
        comparison[
            "best_rank"
        ]
    )

    comparison = (
        comparison
        .sort_values(
            [
                "rank_swing",
                "rank_A",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    return comparison


# =========================================================
# MAIN
# =========================================================

def main():

    bullpen = load_data()

    result = build_tests(
        bullpen
    )

    print_versions(
        result
    )

    comparison = build_sensitivity(
        result
    )

    print()
    print(
        "=" * 100
    )

    print(
        "BULLPEN WEIGHT SENSITIVITY"
    )

    print(
        "=" * 100
    )

    print()

    print(
        comparison.to_string(
            index=False
        )
    )

    print()
    print(
        "=" * 100
    )

    print(
        "BIGGEST WEIGHT-DEPENDENT BULLPENS"
    )

    print(
        "=" * 100
    )

    print()

    print(
        comparison[
            [
                "team",
                "rank_A",
                "rank_B",
                "rank_C",
                "rank_D",
                "rank_swing",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "=" * 100
    )

    print(
        "MOST STABLE BULLPENS"
    )

    print(
        "=" * 100
    )

    print()

    stable = (
        comparison
        .sort_values(
            [
                "rank_swing",
                "rank_A",
            ]
        )
        .head(10)
    )

    print(
        stable[
            [
                "team",
                "rank_A",
                "rank_B",
                "rank_C",
                "rank_D",
                "rank_swing",
            ]
        ]
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()