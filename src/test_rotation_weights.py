from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ROTATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "projected_rotations_2026.csv"
)


# =========================================================
# LOAD
# =========================================================

print("Loading projected rotations...")

df = pd.read_csv(ROTATION_FILE)

print(f"Loaded {len(df)} teams.")


# =========================================================
# WEIGHTS TO TEST
# =========================================================

weight_tests = [
    (0.70, 0.30),
    (0.60, 0.40),
    (0.50, 0.50),
]


# =========================================================
# RUN TESTS
# =========================================================

results = []

for run_weight, qs_weight in weight_tests:

    label = (
        f"{int(run_weight * 100)}/"
        f"{int(qs_weight * 100)}"
    )

    score_column = f"score_{label}"
    rank_column = f"rank_{label}"

    df[score_column] = (
        df["projected_run_score"]
        * run_weight
        +
        df["projected_qs_score"]
        * qs_weight
    )

    df[rank_column] = (
        df[score_column]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    for _, row in df.iterrows():

        results.append(
            {
                "team": row["team"],
                "weights": label,
                "rank": row[rank_column],
                "score": row[score_column],
            }
        )


results_df = pd.DataFrame(results)


# =========================================================
# TOP 15 FOR EACH VERSION
# =========================================================

for run_weight, qs_weight in weight_tests:

    label = (
        f"{int(run_weight * 100)}/"
        f"{int(qs_weight * 100)}"
    )

    score_column = f"score_{label}"
    rank_column = f"rank_{label}"

    print("\n" + "=" * 85)
    print(
        f"RUN SUPPRESSION {int(run_weight * 100)}% "
        f"// QUALITY START {int(qs_weight * 100)}%"
    )
    print("=" * 85)

    display = (
        df[
            [
                "team",
                "projected_run_score",
                "projected_qs_score",
                score_column,
                rank_column,
            ]
        ]
        .sort_values(rank_column)
        .head(15)
        .rename(
            columns={
                score_column: "combined_score",
                rank_column: "rank",
            }
        )
    )

    print(
        display.to_string(
            index=False,
            formatters={
                "projected_run_score":
                    "{:.2f}".format,

                "projected_qs_score":
                    "{:.2f}".format,

                "combined_score":
                    "{:.2f}".format,
            },
        )
    )


# =========================================================
# SIDE-BY-SIDE RANK COMPARISON
# =========================================================

comparison = df[
    [
        "team",
        "rank_70/30",
        "rank_60/40",
        "rank_50/50",
    ]
].copy()

comparison["max_rank"] = comparison[
    [
        "rank_70/30",
        "rank_60/40",
        "rank_50/50",
    ]
].max(axis=1)

comparison["min_rank"] = comparison[
    [
        "rank_70/30",
        "rank_60/40",
        "rank_50/50",
    ]
].min(axis=1)

comparison["rank_swing"] = (
    comparison["max_rank"]
    -
    comparison["min_rank"]
)

comparison = comparison.sort_values(
    [
        "rank_swing",
        "rank_60/40",
    ],
    ascending=[
        False,
        True,
    ],
)


print("\n" + "=" * 85)
print("WEIGHT SENSITIVITY")
print("=" * 85)

print(
    comparison.to_string(
        index=False
    )
)


# =========================================================
# MOST STABLE TEAMS
# =========================================================

stable = comparison.sort_values(
    [
        "rank_swing",
        "rank_60/40",
    ]
).head(10)


print("\n" + "=" * 85)
print("MOST STABLE ROTATION RANKINGS")
print("=" * 85)

print(
    stable[
        [
            "team",
            "rank_70/30",
            "rank_60/40",
            "rank_50/50",
            "rank_swing",
        ]
    ].to_string(
        index=False
    )
)


# =========================================================
# BIGGEST MOVERS
# =========================================================

movers = comparison.head(10)


print("\n" + "=" * 85)
print("BIGGEST WEIGHT-DEPENDENT ROTATIONS")
print("=" * 85)

print(
    movers[
        [
            "team",
            "rank_70/30",
            "rank_60/40",
            "rank_50/50",
            "rank_swing",
        ]
    ].to_string(
        index=False
    )
)