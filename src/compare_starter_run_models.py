from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    roc_auc_score,
)
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAINING_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "training_data_2026.csv"
)

STARTER_RUN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "starter_run_scores_2026.csv"
)

TEST_START_DATE = pd.Timestamp("2026-08-01")


def load_data():

    games = pd.read_csv(
        TRAINING_FILE
    )

    starter_runs = pd.read_csv(
        STARTER_RUN_FILE
    )

    games["date"] = pd.to_datetime(
        games["date"]
    )

    print(
        f"Loaded {len(games):,} training games."
    )

    print(
        f"Loaded starter run scores "
        f"for {len(starter_runs):,} games."
    )

    return games, starter_runs


def merge_data(games, starter_runs):

    starter_runs = starter_runs.rename(
        columns={
            "game_pk": "game_id"
        }
    )

    columns = [
        "game_id",

        "home_starter_prior_starts",
        "home_starter_season_run_score",
        "home_starter_recent_run_score",
        "home_starter_season_continuous_score",
        "home_starter_recent_continuous_score",
        "home_starter_season_runs_allowed",
        "home_starter_recent_runs_allowed",

        "away_starter_prior_starts",
        "away_starter_season_run_score",
        "away_starter_recent_run_score",
        "away_starter_season_continuous_score",
        "away_starter_recent_continuous_score",
        "away_starter_season_runs_allowed",
        "away_starter_recent_runs_allowed",
    ]

    df = games.merge(
        starter_runs[columns],
        on="game_id",
        how="left",
    )

    print(
        f"\nMerged dataset: "
        f"{len(df):,} games."
    )

    return df


def build_features(df):

    features = pd.DataFrame(
        index=df.index
    )

    # ----------------------------
    # CURRENT CHAMPION
    # ----------------------------

    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
    )

    # ----------------------------
    # STARTER RUN SCORES
    # ----------------------------

    features["starter_season_score_diff"] = (
        df["home_starter_season_run_score"]
        - df["away_starter_season_run_score"]
    )

    features["starter_recent_score_diff"] = (
        df["home_starter_recent_run_score"]
        - df["away_starter_recent_run_score"]
    )

    features[
        "starter_season_continuous_diff"
    ] = (
        df[
            "home_starter_season_continuous_score"
        ]
        - df[
            "away_starter_season_continuous_score"
        ]
    )

    features[
        "starter_recent_continuous_diff"
    ] = (
        df[
            "home_starter_recent_continuous_score"
        ]
        - df[
            "away_starter_recent_continuous_score"
        ]
    )

    # Lower runs allowed is better.
    features["starter_recent_runs_diff"] = (
        df["home_starter_recent_runs_allowed"]
        - df["away_starter_recent_runs_allowed"]
    )

    features["starter_season_runs_diff"] = (
        df["home_starter_season_runs_allowed"]
        - df["away_starter_season_runs_allowed"]
    )

    return features


def make_model():

    return XGBClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )


def evaluate(
    name,
    X_train,
    X_test,
    y_train,
    y_test,
):

    model = make_model()

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    return {
        "model": name,

        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),

        "roc_auc": roc_auc_score(
            y_test,
            probabilities,
        ),

        "log_loss": log_loss(
            y_test,
            probabilities,
        ),
    }


def main():

    games, starter_runs = load_data()

    df = merge_data(
        games,
        starter_runs,
    )

    all_features = build_features(
        df
    )

    train_mask = (
        df["date"]
        < TEST_START_DATE
    )

    test_mask = (
        df["date"]
        >= TEST_START_DATE
    )

    X_train = all_features[
        train_mask
    ]

    X_test = all_features[
        test_mask
    ]

    y_train = df.loc[
        train_mask,
        "home_win",
    ]

    y_test = df.loc[
        test_mask,
        "home_win",
    ]

    print(
        f"\nTraining games: "
        f"{len(y_train):,}"
    )

    print(
        f"Testing games: "
        f"{len(y_test):,}"
    )

    baseline = [1] * len(y_test)

    baseline_accuracy = accuracy_score(
        y_test,
        baseline,
    )

    print(
        f"\nHome-team baseline: "
        f"{baseline_accuracy:.3f}"
    )

    team_features = [
        "recent_win_pct_diff",
        "run_diff_per_game_diff",
    ]

    experiments = {

        "Team Only":
            team_features,

        # Your original bucket idea
        "Team + Season Run Score":
            team_features
            + [
                "starter_season_score_diff",
            ],

        "Team + Recent Run Score":
            team_features
            + [
                "starter_recent_score_diff",
            ],

        # Smooth version instead of buckets
        "Team + Recent Continuous":
            team_features
            + [
                "starter_recent_continuous_diff",
            ],

        # Just actual recent runs allowed
        "Team + Recent Runs Allowed":
            team_features
            + [
                "starter_recent_runs_diff",
            ],

        # Season + recent version
        "Team + Season + Recent Run Score":
            team_features
            + [
                "starter_season_score_diff",
                "starter_recent_score_diff",
            ],

        # Pitcher score by itself
        "Recent Starter Score Only": [
            "starter_recent_score_diff",
        ],
    }

    print(
        "\nRunning starter run experiments...\n"
    )

    results = []

    for name, columns in experiments.items():

        result = evaluate(
            name,
            X_train[columns],
            X_test[columns],
            y_train,
            y_test,
        )

        results.append(
            result
        )

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        "roc_auc",
        ascending=False,
    ).reset_index(drop=True)

    print("RESULTS")
    print("=" * 80)

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\nBEST BY ACCURACY")
    print("=" * 80)

    best_accuracy = (
        results_df
        .sort_values(
            "accuracy",
            ascending=False,
        )
        .iloc[0]
    )

    print(
        f"{best_accuracy['model']}: "
        f"{best_accuracy['accuracy']:.3f}"
    )

    print("\nBEST BY ROC AUC")
    print("=" * 80)

    best_auc = (
        results_df
        .sort_values(
            "roc_auc",
            ascending=False,
        )
        .iloc[0]
    )

    print(
        f"{best_auc['model']}: "
        f"{best_auc['roc_auc']:.3f}"
    )

    print("\nLOWEST LOG LOSS")
    print("=" * 80)

    best_loss = (
        results_df
        .sort_values(
            "log_loss",
            ascending=True,
        )
        .iloc[0]
    )

    print(
        f"{best_loss['model']}: "
        f"{best_loss['log_loss']:.3f}"
    )

    print(
        f"\nHome baseline: "
        f"{baseline_accuracy:.3f}"
    )


if __name__ == "__main__":
    main()