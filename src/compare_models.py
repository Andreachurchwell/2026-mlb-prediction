from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "training_data_2026.csv"
)

TEST_START_DATE = pd.Timestamp("2026-08-01")


def load_data():
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_all_features(df):
    features = pd.DataFrame(index=df.index)

    features["win_pct_diff"] = (
        df["home_win_pct"]
        - df["away_win_pct"]
    )

    features["weighted_win_pct_diff"] = (
        df["home_weighted_win_pct"]
        - df["away_weighted_win_pct"]
    )

    features["quality_weighted_win_pct_diff"] = (
        df["home_quality_weighted_win_pct"]
        - df["away_quality_weighted_win_pct"]
    )

    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
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


def evaluate_model(
    name,
    train_features,
    test_features,
    y_train,
    y_test,
):
    model = make_model()

    model.fit(
        train_features,
        y_train,
    )

    predictions = model.predict(
        test_features
    )

    probabilities = model.predict_proba(
        test_features
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

    print("Loading data...")

    df = load_data()

    train_df = df[
        df["date"] < TEST_START_DATE
    ].copy()

    test_df = df[
        df["date"] >= TEST_START_DATE
    ].copy()

    print(
        f"Training games: {len(train_df):,}"
    )

    print(
        f"Testing games: {len(test_df):,}"
    )

    y_train = train_df["home_win"]
    y_test = test_df["home_win"]

    train_features = build_all_features(
        train_df
    )

    test_features = build_all_features(
        test_df
    )

    baseline_predictions = [1] * len(y_test)

    baseline_accuracy = accuracy_score(
        y_test,
        baseline_predictions,
    )

    print(
        f"\nHome-team baseline: "
        f"{baseline_accuracy:.3f}"
    )

    experiments = {

        "Normal Record": [
            "win_pct_diff",
            "recent_win_pct_diff",
            "run_diff_per_game_diff",
        ],

        "Recency Weighted": [
            "weighted_win_pct_diff",
            "recent_win_pct_diff",
            "run_diff_per_game_diff",
        ],

        "Quality Weighted": [
            "quality_weighted_win_pct_diff",
            "recent_win_pct_diff",
            "run_diff_per_game_diff",
        ],

        "Quality Weight Only": [
            "quality_weighted_win_pct_diff",
            "run_diff_per_game_diff",
        ],

        "Recent + Run Diff": [
            "recent_win_pct_diff",
            "run_diff_per_game_diff",
        ],

        "Quality + Recency": [
            "quality_weighted_win_pct_diff",
            "weighted_win_pct_diff",
            "recent_win_pct_diff",
            "run_diff_per_game_diff",
        ],
    }

    results = []

    print("\nRunning experiments...\n")

    for name, columns in experiments.items():

        result = evaluate_model(
            name,
            train_features[columns],
            test_features[columns],
            y_train,
            y_test,
        )

        results.append(result)

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        "roc_auc",
        ascending=False,
    ).reset_index(drop=True)

    print("RESULTS")
    print("=" * 65)

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\nBEST BY ACCURACY")
    print("=" * 65)

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
    print("=" * 65)

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
    print("=" * 65)

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
        f"\nBaseline accuracy: "
        f"{baseline_accuracy:.3f}"
    )


if __name__ == "__main__":
    main()