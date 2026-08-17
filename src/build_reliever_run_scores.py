from pathlib import Path

import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

MIN_APPEARANCES = 10

RELIABILITY_STRENGTH = 20


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

RELIEVER_OUTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliever_outs_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliever_run_scores_2026.csv"
)


# =========================================================
# LOAD
# =========================================================

def load_data():

    print(
        "Loading actual reliever innings..."
    )

    relievers = pd.read_csv(
        RELIEVER_OUTS_FILE
    )

    print(
        f"Loaded {len(relievers):,} "
        f"reliever summaries."
    )

    return relievers


# =========================================================
# FILTER QUALIFIED RELIEVERS
# =========================================================

def filter_relievers(
    relievers,
):

    print(
        "\nFiltering qualified relievers..."
    )

    qualified = relievers[
        (
            relievers[
                "appearances"
            ]
            >= MIN_APPEARANCES
        )
        &
        (
            relievers[
                "innings_pitched"
            ]
            > 0
        )
    ].copy()

    print(
        f"Qualified relievers: "
        f"{len(qualified):,}"
    )

    return qualified


# =========================================================
# RELIABILITY ADJUSTMENT
# =========================================================

def add_reliability(
    relievers,
):

    print(
        "\nApplying reliability adjustment..."
    )

    league_average = (
        relievers[
            "runs_per_9"
        ]
        .mean()
    )

    print(
        f"League-average runs per 9: "
        f"{league_average:.3f}"
    )

    relievers[
        "reliability"
    ] = (
        relievers[
            "appearances"
        ]
        /
        (
            relievers[
                "appearances"
            ]
            +
            RELIABILITY_STRENGTH
        )
    )

    relievers[
        "adjusted_runs_per_9"
    ] = (
        relievers[
            "reliability"
        ]
        *
        relievers[
            "runs_per_9"
        ]
        +
        (
            1
            -
            relievers[
                "reliability"
            ]
        )
        *
        league_average
    )

    return relievers


# =========================================================
# NORMALIZE RUN PREVENTION
# =========================================================

def normalize_scores(
    relievers,
):

    print(
        "\nCreating run-prevention scores..."
    )

    low = (
        relievers[
            "adjusted_runs_per_9"
        ]
        .min()
    )

    high = (
        relievers[
            "adjusted_runs_per_9"
        ]
        .max()
    )

    if high == low:

        relievers[
            "run_prevention_score"
        ] = 50.0

    else:

        # Lower runs per 9 is better,
        # so this normalization is reversed.

        relievers[
            "run_prevention_score"
        ] = (
            (
                high
                -
                relievers[
                    "adjusted_runs_per_9"
                ]
            )
            /
            (
                high
                -
                low
            )
            *
            100
        )

    return relievers


# =========================================================
# MAIN
# =========================================================

def main():

    relievers = load_data()

    relievers = filter_relievers(
        relievers
    )

    relievers = add_reliability(
        relievers
    )

    relievers = normalize_scores(
        relievers
    )

    relievers = (
        relievers
        .sort_values(
            "run_prevention_score",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    relievers.insert(
        0,
        "run_prevention_rank",
        range(
            1,
            len(relievers) + 1,
        ),
    )

    print()
    print(
        "=" * 95
    )

    print(
        "TOP RELIEVERS // "
        "ACTUAL-INNINGS RUN PREVENTION"
    )

    print(
        "=" * 95
    )

    print()

    columns = [
        "run_prevention_rank",
        "pitcher_name",
        "team",
        "appearances",
        "innings_pitched",
        "runs_allowed",
        "runs_per_9",
        "adjusted_runs_per_9",
        "reliability",
        "run_prevention_score",
    ]

    print(
        relievers[
            columns
        ]
        .head(30)
        .to_string(
            index=False
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    relievers.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()