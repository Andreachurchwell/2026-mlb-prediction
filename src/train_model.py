from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    roc_auc_score,
)
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "training_data_2026.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"
MODEL_FILE = MODEL_DIR / "xgb_2026.json"

PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "test_predictions_2026.csv"
)

TEST_START_DATE = pd.Timestamp("2026-08-01")


def load_data():
    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(df["date"])

    return df


def create_difference_features(df):
    """
    Instead of giving XGBoost separate home and away stats,
    calculate the difference between the teams.
    """

    features = pd.DataFrame(index=df.index)

    features["win_pct_diff"] = (
        df["home_win_pct"]
        - df["away_win_pct"]
    )

    features["weighted_win_pct_diff"] = (
        df["home_weighted_win_pct"]
        - df["away_weighted_win_pct"]
    )

    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
    )

    features["runs_scored_per_game_diff"] = (
        df["home_runs_scored_per_game"]
        - df["away_runs_scored_per_game"]
    )

    features["runs_allowed_per_game_diff"] = (
        df["home_runs_allowed_per_game"]
        - df["away_runs_allowed_per_game"]
    )

    return features


def main():

    print("Loading training data...")

    df = load_data()

    print(f"Loaded {len(df):,} games.")

    # ---------------------------------
    # TIME-BASED TRAIN / TEST SPLIT
    # ---------------------------------

    train_df = df[
        df["date"] < TEST_START_DATE
    ].copy()

    test_df = df[
        df["date"] >= TEST_START_DATE
    ].copy()

    print(
        f"\nTraining games: {len(train_df):,}"
    )

    print(
        f"Testing games:  {len(test_df):,}"
    )

    print(
        "Train through:",
        train_df["date"].max().date(),
    )

    print(
        "Test begins:",
        test_df["date"].min().date(),
    )

    # ---------------------------------
    # FEATURES
    # ---------------------------------

    X_train = create_difference_features(
        train_df
    )

    X_test = create_difference_features(
        test_df
    )

    y_train = train_df["home_win"]
    y_test = test_df["home_win"]

    # ---------------------------------
    # BASELINE
    # ---------------------------------

    # Dumb prediction:
    # always predict the home team wins.
    baseline_predictions = [1] * len(y_test)

    baseline_accuracy = accuracy_score(
        y_test,
        baseline_predictions,
    )

    print(
        f"\nHome-team baseline accuracy: "
        f"{baseline_accuracy:.3f}"
    )

    # ---------------------------------
    # XGBOOST
    # ---------------------------------

    print("\nTraining XGBoost...")

    model = XGBClassifier(
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

    model.fit(
        X_train,
        y_train,
    )

    # ---------------------------------
    # PREDICTIONS
    # ---------------------------------

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # ---------------------------------
    # METRICS
    # ---------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    auc = roc_auc_score(
        y_test,
        probabilities,
    )

    loss = log_loss(
        y_test,
        probabilities,
    )

    print("\nMODEL RESULTS")
    print("------------------------")

    print(
        f"Accuracy: {accuracy:.3f}"
    )

    print(
        f"ROC AUC:  {auc:.3f}"
    )

    print(
        f"Log Loss: {loss:.3f}"
    )

    print(
        f"Baseline: {baseline_accuracy:.3f}"
    )

    # ---------------------------------
    # FEATURE IMPORTANCE
    # ---------------------------------

    importance = pd.DataFrame(
        {
            "feature": X_train.columns,
            "importance":
                model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False,
    )

    print("\nFEATURE IMPORTANCE")
    print("------------------------")

    print(
        importance.to_string(
            index=False
        )
    )

    # ---------------------------------
    # SAVE TEST PREDICTIONS
    # ---------------------------------

    results = test_df[
        [
            "game_id",
            "date",
            "home_team",
            "away_team",
            "home_win",
        ]
    ].copy()

    results["predicted_home_win"] = (
        predictions
    )

    results["home_win_probability"] = (
        probabilities
    )

    results["predicted_winner"] = (
        results.apply(
            lambda row:
            row["home_team"]
            if row["predicted_home_win"] == 1
            else row["away_team"],
            axis=1,
        )
    )

    results.to_csv(
        PREDICTIONS_FILE,
        index=False,
    )

    # ---------------------------------
    # SAVE MODEL
    # ---------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save_model(
        MODEL_FILE
    )

    print(
        f"\nModel saved to: {MODEL_FILE}"
    )

    print(
        f"Predictions saved to: "
        f"{PREDICTIONS_FILE}"
    )

    # ---------------------------------
    # SAMPLE PREDICTIONS
    # ---------------------------------

    print("\nSAMPLE PREDICTIONS")
    print("------------------------")

    display_columns = [
        "date",
        "away_team",
        "home_team",
        "home_win_probability",
        "predicted_winner",
        "home_win",
    ]

    print(
        results[
            display_columns
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()