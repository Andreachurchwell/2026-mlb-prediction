from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTENDER_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contender_scores_2026.csv"
)


# =========================================================
# PITCHING SPLIT TESTS
# =========================================================
#
# The current October Shift model gives starting
# rotation 25% of the total score.
#
# These tests keep the TOTAL pitching weight at 25%.
# We are only testing how much of that 25% should
# belong to the bullpen.
#
# CURRENT = 25% rotation / 0% bullpen
# A       = 20% rotation / 5% bullpen
# B       = 17.5% rotation / 7.5% bullpen
# C       = 15% rotation / 10% bullpen
#
# All other components remain unchanged.
# =========================================================

PITCHING_TESTS = {
    "current": {
        "rotation": 0.25,
        "bullpen": 0.00,
    },

    "A": {
        "rotation": 0.20,
        "bullpen": 0.05,
    },

    "B": {
        "rotation": 0.175,
        "bullpen": 0.075,
    },

    "C": {
        "rotation": 0.15,
        "bullpen": 0.10,
    },
}


# =========================================================
# NORMALIZE
# =========================================================

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (
            series - minimum
        )
        /
        (
            maximum - minimum
        )
        * 100
    )


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print(
        "Loading October Shift contender board..."
    )

    df = pd.read_csv(
        CONTENDER_FILE
    )

    print(
        f"Loaded {len(df):,} teams."
    )

    return df


# =========================================================
# PREPARE COMPONENTS
# =========================================================

def prepare_components(df):

    result = df.copy()

    # The contender board already contains the
    # normalized rotation component from the
    # real October Shift calculation.
    #
    # We normalize bullpen the same way so the
    # two pitching components are comparable.

    result["bullpen_component"] = (
        normalize(
            result[
                "neutral_bullpen_score"
            ]
        )
    )

    return result


# =========================================================
# BUILD TEST SCORES
# =========================================================

def build_test_scores(df):

    result = prepare_components(
        df
    )

    # -----------------------------------------
    # NON-PITCHING PORTION
    # -----------------------------------------
    #
    # These weights are exactly the same as
    # the current October Shift model:
    #
    # Run differential       20%
    # Post-ASB performance   20%
    # Last 10                15%
    # Quality wins           10%
    # Overall record         10%
    #
    # Total non-pitching = 75%
    # -----------------------------------------

    result[
        "non_pitching_score"
    ] = (

        result[
            "run_diff_component"
        ]
        * 0.20

        +

        result[
            "post_asb_component"
        ]
        * 0.20

        +

        result[
            "last_10_component"
        ]
        * 0.15

        +

        result[
            "quality_component"
        ]
        * 0.10

        +

        result[
            "overall_record_component"
        ]
        * 0.10
    )

    # -----------------------------------------
    # TEST EACH PITCHING SPLIT
    # -----------------------------------------

    for label, weights in (
        PITCHING_TESTS.items()
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
                "non_pitching_score"
            ]

            +

            result[
                "rotation_component"
            ]
            * weights[
                "rotation"
            ]

            +

            result[
                "bullpen_component"
            ]
            * weights[
                "bullpen"
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
# PRINT EACH TEST
# =========================================================

def print_tests(result):

    for label, weights in (
        PITCHING_TESTS.items()
    ):

        print()
        print(
            "=" * 100
        )

        if label == "current":

            print(
                "CURRENT MODEL"
            )

        else:

            print(
                f"TEST {label}"
            )

        print(
            f"ROTATION "
            f"{weights['rotation']:.1%} // "
            f"BULLPEN "
            f"{weights['bullpen']:.1%}"
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
                    "projected_rotation_rank",
                    "bullpen_rank",
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
                        "october_shift_score",

                    rank_column:
                        "rank",
                }
            )
        )

        print(
            display.to_string(
                index=False,
                formatters={
                    "october_shift_score":
                        "{:.2f}".format,
                }
            )
        )


# =========================================================
# BUILD SENSITIVITY TABLE
# =========================================================

def build_sensitivity(result):

    comparison = result[
        [
            "team",
            "rank_current",
            "rank_A",
            "rank_B",
            "rank_C",
        ]
    ].copy()

    comparison[
        "change_A"
    ] = (
        comparison[
            "rank_current"
        ]
        -
        comparison[
            "rank_A"
        ]
    )

    comparison[
        "change_B"
    ] = (
        comparison[
            "rank_current"
        ]
        -
        comparison[
            "rank_B"
        ]
    )

    comparison[
        "change_C"
    ] = (
        comparison[
            "rank_current"
        ]
        -
        comparison[
            "rank_C"
        ]
    )

    rank_columns = [
        "rank_current",
        "rank_A",
        "rank_B",
        "rank_C",
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
                "rank_current",
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
# PRINT TEAMS TO WATCH
# =========================================================

def print_watch_list(
    result,
    comparison,
):

    print()
    print(
        "=" * 100
    )

    print(
        "PITCHING SPLIT SENSITIVITY"
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
        "BIGGEST RANKING SWINGS"
    )

    print(
        "=" * 100
    )

    print()

    print(
        comparison[
            [
                "team",
                "rank_current",
                "rank_A",
                "rank_B",
                "rank_C",
                "rank_swing",
            ]
        ]
        .head(12)
        .to_string(
            index=False
        )
    )

    # -----------------------------------------
    # SPECIFIC TEAMS WE ALREADY NOTICED
    # -----------------------------------------

    teams_to_watch = [
        "Milwaukee Brewers",
        "Atlanta Braves",
        "Los Angeles Dodgers",
        "Tampa Bay Rays",
        "San Diego Padres",
        "New York Yankees",
        "Boston Red Sox",
    ]

    watch = (
        result[
            result[
                "team"
            ].isin(
                teams_to_watch
            )
        ]
        [
            [
                "team",
                "projected_rotation_rank",
                "bullpen_rank",
                "rank_current",
                "rank_A",
                "rank_B",
                "rank_C",
            ]
        ]
        .sort_values(
            "rank_current"
        )
    )

    print()
    print(
        "=" * 100
    )

    print(
        "TEAMS TO WATCH"
    )

    print(
        "=" * 100
    )

    print()

    print(
        watch.to_string(
            index=False
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    df = load_data()

    result = build_test_scores(
        df
    )

    print_tests(
        result
    )

    comparison = build_sensitivity(
        result
    )

    print_watch_list(
        result,
        comparison,
    )


if __name__ == "__main__":
    main()