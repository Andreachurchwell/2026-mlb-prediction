from pathlib import Path
import json

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ENTRIES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "inherited_runner_entries_2026.csv"
)

PLAY_BY_PLAY_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "play_by_play"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "inherited_runner_results_2026.csv"
)

RELIEVER_SUMMARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reliever_inherited_runner_summary_2026.csv"
)

TEAM_SUMMARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_inherited_runner_summary_2026.csv"
)


# =========================================================
# HELPERS
# =========================================================

def clean_id(value):

    if pd.isna(value):
        return None

    try:
        return int(float(value))

    except (TypeError, ValueError):
        return None


def load_game_feed(
    game_pk,
):

    path = (
        PLAY_BY_PLAY_DIR
        / f"{game_pk}.json"
    )

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


# =========================================================
# GET HALF-INNING PLAYS
# =========================================================

def get_half_inning_plays(
    game_feed,
    inning,
    pitching_side,
):

    if pitching_side == "home":
        half_inning = "top"

    else:
        half_inning = "bottom"

    all_plays = (
        game_feed
        .get(
            "liveData",
            {}
        )
        .get(
            "plays",
            {}
        )
        .get(
            "allPlays",
            []
        )
    )

    plays = []

    for play in all_plays:

        about = play.get(
            "about",
            {}
        )

        if (
            about.get("inning")
            == int(inning)
            and
            str(
                about.get(
                    "halfInning",
                    ""
                )
            ).lower()
            == half_inning
        ):

            plays.append(
                play
            )

    return plays


# =========================================================
# FIND WHERE RELIEVER ENTERED
# =========================================================

def find_reliever_entry_play(
    plays,
    pitcher_id,
):

    pitcher_id = clean_id(
        pitcher_id
    )

    if pitcher_id is None:
        return None

    for index, play in enumerate(
        plays
    ):

        matchup = play.get(
            "matchup",
            {}
        )

        pitcher = matchup.get(
            "pitcher",
            {}
        )

        play_pitcher_id = clean_id(
            pitcher.get(
                "id"
            )
        )

        if (
            play_pitcher_id
            == pitcher_id
        ):
            return index

    return None


# =========================================================
# GET RUNNER MOVEMENTS FROM A PLAY
# =========================================================

def get_runner_movements(
    play,
):

    movements = []

    for runner in play.get(
        "runners",
        []
    ):

        details = runner.get(
            "details",
            {}
        )

        runner_info = details.get(
            "runner",
            {}
        )

        movement = runner.get(
            "movement",
            {}
        )

        runner_id = clean_id(
            runner_info.get(
                "id"
            )
        )

        movements.append(
            {
                "runner_id":
                    runner_id,

                "runner_name":
                    runner_info.get(
                        "fullName",
                        ""
                    ),

                "start":
                    movement.get(
                        "start"
                    ),

                "end":
                    movement.get(
                        "end"
                    ),

                "is_out":
                    bool(
                        movement.get(
                            "isOut",
                            False,
                        )
                    ),
            }
        )

    return movements


# =========================================================
# SCORE ONE RELIEVER ENTRY
# =========================================================

def score_entry(
    row,
    game_feed,
):

    inherited_ids = []

    for column in [
        "on_1b",
        "on_2b",
        "on_3b",
    ]:

        runner_id = clean_id(
            row[column]
        )

        if runner_id is not None:
            inherited_ids.append(
                runner_id
            )

    # Remove accidental duplicates while
    # keeping the original order.

    inherited_ids = list(
        dict.fromkeys(
            inherited_ids
        )
    )

    expected_count = len(
        inherited_ids
    )

    if game_feed is None:

        return {
            "status":
                "missing_feed",

            "inherited_runners":
                expected_count,

            "inherited_scored":
                0,

            "inherited_stranded":
                0,

            "inherited_ambiguous":
                expected_count,

            "runner_results":
                "",
        }

    plays = get_half_inning_plays(
        game_feed,
        row["entry_inning"],
        row["pitching_side"],
    )

    if not plays:

        return {
            "status":
                "half_inning_not_found",

            "inherited_runners":
                expected_count,

            "inherited_scored":
                0,

            "inherited_stranded":
                0,

            "inherited_ambiguous":
                expected_count,

            "runner_results":
                "",
        }

    entry_play_index = (
        find_reliever_entry_play(
            plays,
            row["pitcher_id"],
        )
    )

    if entry_play_index is None:

        return {
            "status":
                "pitcher_entry_not_found",

            "inherited_runners":
                expected_count,

            "inherited_scored":
                0,

            "inherited_stranded":
                0,

            "inherited_ambiguous":
                expected_count,

            "runner_results":
                "",
        }

    # Only look at plays from the moment
    # this reliever entered through the end
    # of the half inning.

    later_plays = plays[
        entry_play_index:
    ]

    runner_status = {
        runner_id:
            "stranded"
        for runner_id in inherited_ids
    }

    runner_names = {
        runner_id:
            ""
        for runner_id in inherited_ids
    }

    # -----------------------------------------
    # TRACK EACH SPECIFIC INHERITED RUNNER
    # -----------------------------------------
    #
    # If MLB records that runner's destination
    # as "score", he scored.
    #
    # Otherwise, once the half inning ends,
    # the inherited runner was prevented from
    # scoring and counts as stranded for our
    # project metric.
    # -----------------------------------------

    for play in later_plays:

        movements = (
            get_runner_movements(
                play
            )
        )

        for movement in movements:

            runner_id = (
                movement[
                    "runner_id"
                ]
            )

            if (
                runner_id
                not in runner_status
            ):
                continue

            if movement[
                "runner_name"
            ]:

                runner_names[
                    runner_id
                ] = movement[
                    "runner_name"
                ]

            end_base = str(
                movement[
                    "end"
                ]
                or ""
            ).lower()

            if end_base == "score":

                runner_status[
                    runner_id
                ] = "scored"

    scored = sum(
        status == "scored"
        for status in runner_status.values()
    )

    stranded = sum(
        status == "stranded"
        for status in runner_status.values()
    )

    runner_results = []

    for runner_id in inherited_ids:

        name = (
            runner_names.get(
                runner_id
            )
            or str(
                runner_id
            )
        )

        runner_results.append(
            f"{name}:{runner_status[runner_id]}"
        )

    return {
        "status":
            "ok",

        "inherited_runners":
            expected_count,

        "inherited_scored":
            scored,

        "inherited_stranded":
            stranded,

        "inherited_ambiguous":
            0,

        "runner_results":
            " | ".join(
                runner_results
            ),
    }


# =========================================================
# BUILD ENTRY RESULTS
# =========================================================

def build_results(
    entries,
):

    print(
        "\nScoring inherited runners "
        "from MLB play-by-play..."
    )

    entries = entries[
        entries[
            "inherited_runners"
        ]
        > 0
    ].copy()

    rows = []

    game_cache = {}

    total = len(
        entries
    )

    for number, (
        _,
        row,
    ) in enumerate(
        entries.iterrows(),
        start=1,
    ):

        game_pk = int(
            row["game_pk"]
        )

        if (
            game_pk
            not in game_cache
        ):

            game_cache[
                game_pk
            ] = load_game_feed(
                game_pk
            )

        result = score_entry(
            row,
            game_cache[
                game_pk
            ],
        )

        rows.append(
            {
                "game_pk":
                    game_pk,

                "game_date":
                    row[
                        "game_date"
                    ],

                "team":
                    row[
                        "team"
                    ],

                "pitcher_id":
                    clean_id(
                        row[
                            "pitcher_id"
                        ]
                    ),

                "pitcher_name":
                    row[
                        "pitcher_name"
                    ],

                "entry_inning":
                    row[
                        "entry_inning"
                    ],

                "entry_outs":
                    row[
                        "entry_outs"
                    ],

                "on_1b":
                    clean_id(
                        row[
                            "on_1b"
                        ]
                    ),

                "on_2b":
                    clean_id(
                        row[
                            "on_2b"
                        ]
                    ),

                "on_3b":
                    clean_id(
                        row[
                            "on_3b"
                        ]
                    ),

                "inherited_runners":
                    result[
                        "inherited_runners"
                    ],

                "inherited_scored":
                    result[
                        "inherited_scored"
                    ],

                "inherited_stranded":
                    result[
                        "inherited_stranded"
                    ],

                "inherited_ambiguous":
                    result[
                        "inherited_ambiguous"
                    ],

                "status":
                    result[
                        "status"
                    ],

                "runner_results":
                    result[
                        "runner_results"
                    ],
            }
        )

        if (
            number % 500
            == 0
        ):

            print(
                f"Processed "
                f"{number:,} / "
                f"{total:,} entries"
            )

    return pd.DataFrame(
        rows
    )


# =========================================================
# RELIEVER SUMMARY
# =========================================================

def build_reliever_summary(
    results,
):

    clear = results[
        results["status"]
        == "ok"
    ].copy()

    summary = (
        clear
        .groupby(
            [
                "pitcher_name",
                "team",
            ]
        )
        .agg(
            entries_with_runners=(
                "game_pk",
                "count",
            ),

            inherited_runners=(
                "inherited_runners",
                "sum",
            ),

            inherited_scored=(
                "inherited_scored",
                "sum",
            ),

            inherited_stranded=(
                "inherited_stranded",
                "sum",
            ),
        )
        .reset_index()
    )

    summary[
        "strand_rate"
    ] = (
        summary[
            "inherited_stranded"
        ]
        /
        summary[
            "inherited_runners"
        ]
        .replace(
            0,
            pd.NA,
        )
    )

    return (
        summary
        .sort_values(
            [
                "inherited_runners",
                "strand_rate",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )


# =========================================================
# TEAM SUMMARY
# =========================================================

def build_team_summary(
    results,
):

    clear = results[
        results["status"]
        == "ok"
    ].copy()

    summary = (
        clear
        .groupby(
            "team"
        )
        .agg(
            entries_with_runners=(
                "game_pk",
                "count",
            ),

            inherited_runners=(
                "inherited_runners",
                "sum",
            ),

            inherited_scored=(
                "inherited_scored",
                "sum",
            ),

            inherited_stranded=(
                "inherited_stranded",
                "sum",
            ),
        )
        .reset_index()
    )

    summary[
        "strand_rate"
    ] = (
        summary[
            "inherited_stranded"
        ]
        /
        summary[
            "inherited_runners"
        ]
        .replace(
            0,
            pd.NA,
        )
    )

    summary = (
        summary
        .sort_values(
            "strand_rate",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    summary.insert(
        0,
        "strand_rank",
        range(
            1,
            len(summary) + 1,
        ),
    )

    return summary


# =========================================================
# PRINT RESULTS
# =========================================================

def print_summary(
    results,
    relievers,
    teams,
):

    print()
    print(
        "=" * 90
    )

    print(
        "INHERITED RUNNER CHECK"
    )

    print(
        "=" * 90
    )

    status_counts = (
        results[
            "status"
        ]
        .value_counts(
            dropna=False
        )
    )

    print()
    print(
        status_counts.to_string()
    )

    print()
    print(
        "TOP RELIEVERS BY "
        "INHERITED RUNNER VOLUME"
    )

    print()

    print(
        relievers
        .head(30)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "TEAM INHERITED-RUNNER "
        "STRAND RANKINGS"
    )

    print()

    print(
        teams
        .to_string(
            index=False
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Loading inherited-runner entries..."
    )

    entries = pd.read_csv(
        ENTRIES_FILE
    )

    print(
        f"Loaded "
        f"{len(entries):,} "
        f"reliever entries."
    )

    results = build_results(
        entries
    )

    relievers = (
        build_reliever_summary(
            results
        )
    )

    teams = (
        build_team_summary(
            results
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    relievers.to_csv(
        RELIEVER_SUMMARY_FILE,
        index=False,
    )

    teams.to_csv(
        TEAM_SUMMARY_FILE,
        index=False,
    )

    print_summary(
        results,
        relievers,
        teams,
    )

    print()
    print(
        "Saved:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        RELIEVER_SUMMARY_FILE
    )

    print(
        TEAM_SUMMARY_FILE
    )


if __name__ == "__main__":
    main()