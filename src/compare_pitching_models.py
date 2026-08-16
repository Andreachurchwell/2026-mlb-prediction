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

PITCHING_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_features_2026.csv"
)

TEST_START_DATE = pd.Timestamp("2026-08-01")


def load_data():

    games = pd.read_csv(TRAINING_FILE)
    pitching = pd.read_csv(PITCHING_FILE)

    games["date"] = pd.to_datetime(
        games["date"]
    )

    print(
        f"Loaded {len(games):,} "
        "training games."
    )

    print(
        f"Loaded pitching features "
        f"for {len(pitching):,} games."
    )

    return games, pitching


def merge_data(games, pitching):

    pitching = pitching.rename(
        columns={
            "game_pk": "game_id"
        }
    )

    df = games.merge(
        pitching,
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

    # ============================
    # TEAM FEATURES
    # ============================

    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
    )

    # ============================
    # SEASON PITCHING
    # ============================

    features["season_k_rate_diff"] = (
        df["home_starter_season_k_rate"]
        - df["away_starter_season_k_rate"]
    )

    features["season_walk_rate_diff"] = (
        df["home_starter_season_walk_rate"]
        - df["away_starter_season_walk_rate"]
    )

    features[
        "season_baserunner_rate_diff"
    ] = (
        df[
            "home_starter_season_baserunner_rate"
        ]
        - df[
            "away_starter_season_baserunner_rate"
        ]
    )

    features["season_hr_rate_diff"] = (
        df["home_starter_season_hr_rate"]
        - df["away_starter_season_hr_rate"]
    )

    # ============================
    # RECENT PITCHING
    # ============================

    features["recent_k_rate_diff"] = (
        df["home_starter_recent_k_rate"]
        - df["away_starter_recent_k_rate"]
    )

    features["recent_walk_rate_diff"] = (
        df["home_starter_recent_walk_rate"]
        - df["away_starter_recent_walk_rate"]
    )

    features[
        "recent_baserunner_rate_diff"
    ] = (
        df[
            "home_starter_recent_baserunner_rate"
        ]
        - df[
            "away_starter_recent_baserunner_rate"
        ]
    )

    features["recent_hr_rate_diff"] = (
        df["home_starter_recent_hr_rate"]
        - df["away_starter_recent_hr_rate"]
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

    games, pitching = load_data()

    df = merge_data(
        games,
        pitching,
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

    y_train = df.loc[
        train_mask,
        "home_win",
    ]

    y_test = df.loc[
        test_mask,
        "home_win",
    ]

    X_train = all_features[
        train_mask
    ]

    X_test = all_features[
        test_mask
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

    season_pitching = [
        "season_k_rate_diff",
        "season_walk_rate_diff",
        "season_baserunner_rate_diff",
        "season_hr_rate_diff",
    ]

    recent_pitching = [
        "recent_k_rate_diff",
        "recent_walk_rate_diff",
        "recent_baserunner_rate_diff",
        "recent_hr_rate_diff",
    ]

    experiments = {

        "Team Only":
            team_features,

        "Team + Season Pitching":
            team_features
            + season_pitching,

        "Team + Recent Pitching":
            team_features
            + recent_pitching,

        "Team + Season + Recent":
            team_features
            + season_pitching
            + recent_pitching,

        "Recent Pitching Only":
            recent_pitching,
    }

    results = []

    print(
        "\nRunning experiments...\n"
    )

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
    print("=" * 70)

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\nBEST BY ACCURACY")
    print("=" * 70)

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
    print("=" * 70)

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
    print("=" * 70)

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