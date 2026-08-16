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


def load_data():
    games = pd.read_csv(TRAINING_FILE)
    starter_runs = pd.read_csv(STARTER_RUN_FILE)

    games["date"] = pd.to_datetime(games["date"])

    starter_runs = starter_runs.rename(
        columns={
            "game_pk": "game_id"
        }
    )

    starter_columns = [
        "game_id",
        "home_starter_recent_run_score",
        "away_starter_recent_run_score",
    ]

    df = games.merge(
        starter_runs[starter_columns],
        on="game_id",
        how="left",
    )

    print(f"Loaded {len(df):,} games.")

    return df


def build_features(df):
    features = pd.DataFrame(index=df.index)

    features["recent_win_pct_diff"] = (
        df["home_recent_win_pct"]
        - df["away_recent_win_pct"]
    )

    features["run_diff_per_game_diff"] = (
        df["home_run_diff_per_game"]
        - df["away_run_diff_per_game"]
    )

    features["starter_recent_run_score_diff"] = (
        df["home_starter_recent_run_score"]
        - df["away_starter_recent_run_score"]
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


def evaluate_window(
    df,
    features,
    train_end,
    test_start,
    test_end,
):
    train_mask = (
        df["date"] <= train_end
    )

    test_mask = (
        (df["date"] >= test_start)
        & (df["date"] <= test_end)
    )

    y_train = df.loc[
        train_mask,
        "home_win",
    ]

    y_test = df.loc[
        test_mask,
        "home_win",
    ]

    if len(y_test) == 0:
        return []

    team_columns = [
        "recent_win_pct_diff",
        "run_diff_per_game_diff",
    ]

    pitching_columns = [
        "recent_win_pct_diff",
        "run_diff_per_game_diff",
        "starter_recent_run_score_diff",
    ]

    experiments = {
        "Team Only": team_columns,
        "Team + Recent Run Score": pitching_columns,
    }

    rows = []

    for name, columns in experiments.items():
        model = make_model()

        X_train = features.loc[
            train_mask,
            columns,
        ]

        X_test = features.loc[
            test_mask,
            columns,
        ]

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

        rows.append(
            {
                "model": name,
                "train_end":
                    train_end.date(),
                "test_start":
                    test_start.date(),
                "test_end":
                    test_end.date(),
                "test_games":
                    len(y_test),
                "accuracy":
                    accuracy_score(
                        y_test,
                        predictions,
                    ),
                "roc_auc":
                    roc_auc_score(
                        y_test,
                        probabilities,
                    ),
                "log_loss":
                    log_loss(
                        y_test,
                        probabilities,
                    ),
            }
        )

    return rows


def main():
    df = load_data()

    features = build_features(df)

    windows = [
        {
            "train_end":
                pd.Timestamp("2026-06-15"),

            "test_start":
                pd.Timestamp("2026-06-16"),

            "test_end":
                pd.Timestamp("2026-06-30"),
        },

        {
            "train_end":
                pd.Timestamp("2026-06-30"),

            "test_start":
                pd.Timestamp("2026-07-01"),

            "test_end":
                pd.Timestamp("2026-07-15"),
        },

        {
            "train_end":
                pd.Timestamp("2026-07-15"),

            "test_start":
                pd.Timestamp("2026-07-16"),

            "test_end":
                pd.Timestamp("2026-07-31"),
        },

        {
            "train_end":
                pd.Timestamp("2026-07-31"),

            "test_start":
                pd.Timestamp("2026-08-01"),

            "test_end":
                pd.Timestamp("2026-08-16"),
        },
    ]

    all_results = []

    print("\nRunning time-window validation...\n")

    for window in windows:
        rows = evaluate_window(
            df=df,
            features=features,
            train_end=window[
                "train_end"
            ],
            test_start=window[
                "test_start"
            ],
            test_end=window[
                "test_end"
            ],
        )

        all_results.extend(rows)

    results = pd.DataFrame(
        all_results
    )

    print("WINDOW RESULTS")
    print("=" * 95)

    print(
        results.to_string(
            index=False
        )
    )

    print("\nAVERAGE RESULTS")
    print("=" * 95)

    averages = (
        results
        .groupby("model")
        .agg(
            avg_accuracy=(
                "accuracy",
                "mean",
            ),
            avg_roc_auc=(
                "roc_auc",
                "mean",
            ),
            avg_log_loss=(
                "log_loss",
                "mean",
            ),
        )
        .reset_index()
    )

    print(
        averages.to_string(
            index=False
        )
    )

    print("\nWINS BY ROC AUC")
    print("=" * 95)

    for (
        test_start,
        group
    ) in results.groupby(
        "test_start"
    ):

        best = group.sort_values(
            "roc_auc",
            ascending=False,
        ).iloc[0]

        print(
            f"{test_start}: "
            f"{best['model']} "
            f"({best['roc_auc']:.3f})"
        )


if __name__ == "__main__":
    main()