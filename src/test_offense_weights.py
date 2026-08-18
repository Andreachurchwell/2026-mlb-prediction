from pathlib import Path

import pandas as pd


# =========================================================
# PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTENDER_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contender_scores_2026.csv"
)

OFFENSE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "offensive_momentum_2026.csv"
)


# =========================================================
# WEIGHT SCENARIOS
# =========================================================

SCENARIOS = {
    "CURRENT_LIVE": {
        "rotation": 0.20,
        "bullpen": 0.05,
        "offense": 0.00,
        "run_diff": 0.20,
        "post_asb": 0.20,
        "last_10": 0.15,
        "quality": 0.10,
        "record": 0.10,
    },

    "OFFENSE_10": {
        "rotation": 0.20,
        "bullpen": 0.05,
        "offense": 0.10,
        "run_diff": 0.20,
        "post_asb": 0.17,
        "last_10": 0.12,
        "quality": 0.06,
        "record": 0.10,
    },

    "OFFENSE_15": {
        "rotation": 0.20,
        "bullpen": 0.05,
        "offense": 0.15,
        "run_diff": 0.20,
        "post_asb": 0.15,
        "last_10": 0.10,
        "quality": 0.05,
        "record": 0.10,
    },

    "OFFENSE_20": {
        "rotation": 0.20,
        "bullpen": 0.05,
        "offense": 0.20,
        "run_diff": 0.20,
        "post_asb": 0.12,
        "last_10": 0.08,
        "quality": 0.05,
        "record": 0.10,
    },
}


# =========================================================
# TEAMS TO WATCH
# =========================================================

WATCH_TEAMS = [
    "Milwaukee Brewers",
    "Tampa Bay Rays",
    "Los Angeles Dodgers",
    "Chicago Cubs",
    "Atlanta Braves",
    "San Diego Padres",
    "Boston Red Sox",
    "New York Yankees",
]


# =========================================================
# HELPERS
# =========================================================

def normalize_0_100(series):

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    minimum = values.min()
    maximum = values.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            50.0,
            index=series.index,
        )

    if maximum == minimum:
        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (values - minimum)
        / (maximum - minimum)
        * 100
    )


def add_rank(df, score_column, rank_column):

    df[rank_column] = (
        df[score_column]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return df


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    contenders = pd.read_csv(
        CONTENDER_FILE
    )

    offense = pd.read_csv(
        OFFENSE_FILE
    )

    offense = offense[
        [
            "team",
            "offensive_momentum_rank",
            "offensive_momentum_score",
            "offense_level",
            "offense_direction",
        ]
    ].copy()

    merged = contenders.merge(
        offense,
        on="team",
        how="left",
        validate="one_to_one",
    )

    return merged


# =========================================================
# COMPONENTS
# =========================================================

def prepare_components(df):

    df = df.copy()

    # These already exist in the live contender file
    # as normalized 0-100 component scores.
    component_columns = [
        "rotation_component",
        "bullpen_component",
        "run_diff_component",
        "post_asb_component",
        "last_10_component",
        "quality_component",
        "overall_record_component",
    ]

    for column in component_columns:

        if column not in df.columns:
            raise KeyError(
                f"Missing required contender component: {column}"
            )

    # Offensive Momentum Score is already 0-100,
    # but normalize it again across MLB so every
    # scenario uses a comparable full 0-100 range.
    df["offense_component"] = (
        normalize_0_100(
            df["offensive_momentum_score"]
        )
    )

    return df


# =========================================================
# SCORE SCENARIOS
# =========================================================

def score_scenarios(df):

    df = df.copy()

    for name, weights in SCENARIOS.items():

        total = sum(
            weights.values()
        )

        if abs(total - 1.0) > 0.000001:
            raise ValueError(
                f"{name} weights total {total:.4f}, not 1.0"
            )

        score_column = (
            f"{name.lower()}_score"
        )

        rank_column = (
            f"{name.lower()}_rank"
        )

        df[score_column] = (
            weights["rotation"]
            * df["rotation_component"]

            + weights["bullpen"]
            * df["bullpen_component"]

            + weights["offense"]
            * df["offense_component"]

            + weights["run_diff"]
            * df["run_diff_component"]

            + weights["post_asb"]
            * df["post_asb_component"]

            + weights["last_10"]
            * df["last_10_component"]

            + weights["quality"]
            * df["quality_component"]

            + weights["record"]
            * df["overall_record_component"]
        )

        df = add_rank(
            df,
            score_column,
            rank_column,
        )

    return df


# =========================================================
# DISPLAY
# =========================================================

def print_scenario_board(
    df,
    scenario_name,
    top_n=15,
):

    score_column = (
        f"{scenario_name.lower()}_score"
    )

    rank_column = (
        f"{scenario_name.lower()}_rank"
    )

    board = (
        df.sort_values(
            [
                rank_column,
                "team",
            ]
        )
        [
            [
                rank_column,
                "team",
                score_column,
                "offensive_momentum_rank",
                "offensive_momentum_score",
                "offense_level",
                "offense_direction",
            ]
        ]
        .head(top_n)
    )

    print()
    print("=" * 110)
    print(
        f"{scenario_name} // TOP {top_n}"
    )
    print("=" * 110)
    print()

    print(
        board.to_string(
            index=False
        )
    )


def print_watch_teams(df):

    columns = [
        "team",
        "rank",
        "october_shift_score",
        "offensive_momentum_rank",
        "offensive_momentum_score",
        "offense_level",
        "offense_direction",
    ]

    for scenario_name in SCENARIOS:

        columns.extend(
            [
                f"{scenario_name.lower()}_rank",
                f"{scenario_name.lower()}_score",
            ]
        )

    watch = (
        df[
            df["team"].isin(
                WATCH_TEAMS
            )
        ]
        [columns]
        .copy()
    )

    watch = watch.sort_values(
        "rank"
    )

    print()
    print("=" * 150)
    print(
        "WATCH TEAMS // "
        "CURRENT VS OFFENSE WEIGHTS"
    )
    print("=" * 150)
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

    print(
        "Loading contender and offensive momentum data..."
    )

    df = load_data()

    print(
        f"Loaded {len(df)} teams."
    )

    missing_offense = (
        df[
            "offensive_momentum_score"
        ]
        .isna()
        .sum()
    )

    if missing_offense:

        raise ValueError(
            f"{missing_offense} teams are missing offense scores."
        )

    df = prepare_components(
        df
    )

    df = score_scenarios(
        df
    )

    for scenario_name in SCENARIOS:

        print_scenario_board(
            df,
            scenario_name,
            top_n=15,
        )

    print_watch_teams(
        df
    )


if __name__ == "__main__":
    main()