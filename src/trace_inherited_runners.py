from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

PITCHING_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

STARTERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "inherited_runner_results_2026.csv"
)


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print("Loading data...")

    pitching = pd.read_csv(
        PITCHING_FILE,
        low_memory=False,
    )

    starters = pd.read_csv(
        STARTERS_FILE
    )

    pitching["game_date"] = pd.to_datetime(
        pitching["game_date"]
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    print(
        f"Loaded {len(pitching):,} pitches."
    )

    print(
        f"Loaded starter assignments "
        f"for {len(starters):,} games."
    )

    return pitching, starters


# =========================================================
# BUILD TEAM LOOKUP
# =========================================================

def build_team_lookup(
    starters,
):

    home = starters[
        [
            "game_pk",
            "home_team",
            "home_starter_id",
        ]
    ].rename(
        columns={
            "home_team":
                "team",

            "home_starter_id":
                "starter_id",
        }
    )

    home["pitching_side"] = "home"

    away = starters[
        [
            "game_pk",
            "away_team",
            "away_starter_id",
        ]
    ].rename(
        columns={
            "away_team":
                "team",

            "away_starter_id":
                "starter_id",
        }
    )

    away["pitching_side"] = "away"

    return pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    )


# =========================================================
# DETERMINE IF RUNNER SCORED
# =========================================================

def runner_scored(
    runner_id,
    half_inning,
    entry_index,
):

    later = half_inning.loc[
        half_inning.index
        >= entry_index
    ].copy()

    last_seen_index = None

    for idx, row in later.iterrows():

        bases = {
            row["on_1b"],
            row["on_2b"],
            row["on_3b"],
        }

        if runner_id in bases:
            last_seen_index = idx
            continue

        if last_seen_index is None:
            continue

        previous = half_inning.loc[
            last_seen_index
        ]

        runs_on_play = (
            row["post_bat_score"]
            -
            row["bat_score"]
        )

        if (
            pd.notna(runs_on_play)
            and runs_on_play > 0
        ):
            return "scored"

        # Runner disappeared from the bases
        # without a run scoring on that play.
        # Most likely out / force / pickoff.
        return "stranded"

    # If the runner is still present when the
    # half-inning ends, treat as stranded.
    if last_seen_index is not None:
        return "stranded"

    return "ambiguous"


# =========================================================
# BUILD RELIEVER ENTRIES
# =========================================================

def trace_inherited_runners(
    pitching,
    starters,
):

    print(
        "\nTracing inherited runners..."
    )

    pitching = pitching.sort_values(
        [
            "game_pk",
            "inning",
            "inning_topbot",
            "at_bat_number",
            "pitch_number",
        ]
    ).copy()

    team_lookup = (
        build_team_lookup(
            starters
        )
    )

    results = []

    pitcher_groups = pitching.groupby(
        [
            "game_pk",
            "pitcher",
            "player_name",
        ],
        dropna=False,
    )

    for (
        game_pk,
        pitcher_id,
        pitcher_name,
    ), group in pitcher_groups:

        group = group.sort_values(
            [
                "inning",
                "at_bat_number",
                "pitch_number",
            ]
        )

        first_pitch = (
            group.iloc[0]
        )

        inning = (
            first_pitch["inning"]
        )

        inning_topbot = (
            first_pitch[
                "inning_topbot"
            ]
        )

        if inning_topbot == "Top":
            pitching_side = "home"

        else:
            pitching_side = "away"

        lookup_row = team_lookup[
            (
                team_lookup[
                    "game_pk"
                ]
                == game_pk
            )
            &
            (
                team_lookup[
                    "pitching_side"
                ]
                == pitching_side
            )
        ]

        if lookup_row.empty:
            continue

        team = (
            lookup_row.iloc[0][
                "team"
            ]
        )

        starter_id = (
            lookup_row.iloc[0][
                "starter_id"
            ]
        )

        if (
            pd.notna(starter_id)
            and
            pd.notna(pitcher_id)
            and
            int(pitcher_id)
            == int(starter_id)
        ):
            continue

        inherited = []

        for base_name in [
            "on_1b",
            "on_2b",
            "on_3b",
        ]:

            runner_id = (
                first_pitch[
                    base_name
                ]
            )

            if pd.notna(runner_id):

                inherited.append(
                    int(runner_id)
                )

        if not inherited:
            continue

        half_inning = pitching[
            (
                pitching[
                    "game_pk"
                ]
                == game_pk
            )
            &
            (
                pitching[
                    "inning"
                ]
                == inning
            )
            &
            (
                pitching[
                    "inning_topbot"
                ]
                == inning_topbot
            )
        ].copy()

        half_inning = half_inning.sort_values(
            [
                "at_bat_number",
                "pitch_number",
            ]
        )

        first_index = (
            group.index[0]
        )

        scored = 0
        stranded = 0
        ambiguous = 0

        runner_results = []

        for runner_id in inherited:

            result = runner_scored(
                runner_id,
                half_inning,
                first_index,
            )

            runner_results.append(
                f"{runner_id}:{result}"
            )

            if result == "scored":
                scored += 1

            elif result == "stranded":
                stranded += 1

            else:
                ambiguous += 1

        results.append(
            {
                "game_pk":
                    game_pk,

                "game_date":
                    first_pitch[
                        "game_date"
                    ],

                "team":
                    team,

                "pitcher_id":
                    pitcher_id,

                "pitcher_name":
                    pitcher_name,

                "entry_inning":
                    inning,

                "entry_outs":
                    first_pitch[
                        "outs_when_up"
                    ],

                "inherited_runners":
                    len(inherited),

                "inherited_scored":
                    scored,

                "inherited_stranded":
                    stranded,

                "inherited_ambiguous":
                    ambiguous,

                "runner_results":
                    " | ".join(
                        runner_results
                    ),
            }
        )

    return pd.DataFrame(
        results
    )


# =========================================================
# SUMMARY
# =========================================================

def print_summary(
    results,
):

    print()
    print(
        "INHERITED RUNNER RESULTS"
    )
    print()

    summary = (
        results
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

            inherited_ambiguous=(
                "inherited_ambiguous",
                "sum",
            ),
        )
        .reset_index()
    )

    clear_total = (
        summary[
            "inherited_scored"
        ]
        +
        summary[
            "inherited_stranded"
        ]
    )

    summary[
        "strand_rate"
    ] = (
        summary[
            "inherited_stranded"
        ]
        /
        clear_total.replace(
            0,
            pd.NA,
        )
    )

    summary = summary.sort_values(
        [
            "inherited_runners",
            "strand_rate",
        ],
        ascending=[
            False,
            False,
        ],
    )

    print(
        summary
        .head(30)
        .to_string(
            index=False
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    pitching, starters = (
        load_data()
    )

    results = (
        trace_inherited_runners(
            pitching,
            starters,
        )
    )

    print(
        f"\nCreated "
        f"{len(results):,} "
        f"reliever entries with "
        f"inherited runners."
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print_summary(
        results
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()