from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAINING_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "training_data_2026.csv"
)

STARTER_RECORD_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "starter_records_2026.csv"
)

TEST_START_DATE = pd.Timestamp("2026-08-01")


def load_data():
    games = pd.read_csv(TRAINING_FILE)
    starters = pd.read_csv(STARTER_RECORD_FILE)

    games["date"] = pd.to_datetime(games["date"])
    starters["date"] = pd.to_datetime(starters["date"])

    print(f"Loaded {len(games):,} training games.")
    print(f"Loaded starter records for {len(starters):,} games.")

    return games, starters


def merge_data(games, starters):
    starter_columns = [
        "game_id",
        "home_starter_prior_starts",
        "home_starter_team_win_pct",
        "home_starter_weighted_team_win_pct",
        "home_starter_recent_team_win_pct",
        "away_starter_prior_starts",
        "away_starter_team_win_pct",
        "away_starter_weighted_team_win_pct",
        "away_starter_recent_team_win_pct",
    ]

    df = games.merge(
        starters[starter_columns],
        on="game_id",
        how="left",
    )

    print(f"\nMerged dataset: {len(df):,} games.")

    return df


def build_features(df):
    features = pd.DataFrame(index=df.index)

    # Current best team features
    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
    )

    # Starter record features
    features["starter_team_win_pct_diff"] = (
        df["home_starter_team_win_pct"]
        - df["away_starter_team_win_pct"]
    )

    features["starter_weighted_win_pct_diff"] = (
        df["home_starter_weighted_team_win_pct"]
        - df["away_starter_weighted_team_win_pct"]
    )

    features["starter_recent_win_pct_diff"] = (
        df["home_starter_recent_team_win_pct"]
        - df["away_starter_recent_team_win_pct"]
    )

    features["starter_prior_starts_diff"] = (
        df["home_starter_prior_starts"]
        - df["away_starter_prior_starts"]
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

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

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
    games, starters = load_data()

    df = merge_data(
        games,
        starters,
    )

    all_features = build_features(df)

    train_mask = (
        df["date"]
        < TEST_START_DATE
    )

    test_mask = (
        df["date"]
        >= TEST_START_DATE
    )

    X_train = all_features[train_mask]
    X_test = all_features[test_mask]

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

        "Team + Starter Record":
            team_features
            + [
                "starter_team_win_pct_diff",
            ],

        "Team + Recent Starter":
            team_features
            + [
                "starter_recent_win_pct_diff",
            ],

        "Team + Weighted Starter":
            team_features
            + [
                "starter_weighted_win_pct_diff",
            ],

        "Team + Weighted + Recent Starter":
            team_features
            + [
                "starter_weighted_win_pct_diff",
                "starter_recent_win_pct_diff",
            ],

        "Team + All Starter Records":
            team_features
            + [
                "starter_team_win_pct_diff",
                "starter_weighted_win_pct_diff",
                "starter_recent_win_pct_diff",
                "starter_prior_starts_diff",
            ],
    }

    results = []

    print("\nRunning experiments...\n")

    for name, columns in experiments.items():

        result = evaluate(
            name,
            X_train[columns],
            X_test[columns],
            y_train,
            y_test,
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        "roc_auc",
        ascending=False,
    ).reset_index(drop=True)

    print("RESULTS")
    print("=" * 75)

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\nBEST BY ACCURACY")
    print("=" * 75)

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
    print("=" * 75)

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
    print("=" * 75)

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