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

BULLPEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "bullpen_appearances_2026.csv"
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
    / "reliever_outs_2026.csv"
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


def load_game(game_pk):

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

        return json.load(file)


# =========================================================
# COUNT OUTS FOR ONE PITCHER
# =========================================================

def count_pitcher_outs(
    game_feed,
    pitcher_id,
):

    pitcher_id = clean_id(
        pitcher_id
    )

    if (
        game_feed is None
        or pitcher_id is None
    ):
        return None

    plays = (
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

    total_outs = 0

    for play in plays:

        matchup = play.get(
            "matchup",
            {}
        )

        play_pitcher = (
            matchup.get(
                "pitcher",
                {}
            )
        )

        play_pitcher_id = clean_id(
            play_pitcher.get(
                "id"
            )
        )

        if (
            play_pitcher_id
            != pitcher_id
        ):
            continue

        # -----------------------------------------
        # MLB provides outs before and after
        # the plate appearance.
        #
        # Difference = outs recorded during
        # that plate appearance.
        #
        # This correctly handles:
        # strikeouts
        # groundouts
        # double plays
        # sacrifice plays
        # caught stealing during PA
        # etc.
        # -----------------------------------------

        about = play.get(
            "about",
            {}
        )

        start_outs = (
            about.get(
                "startTime"
            )
        )

        # We do NOT actually want startTime.
        # Outs are safer to calculate directly
        # from runner movements/result data below.

        play_outs = 0

        # Batter may be retired.

        result = play.get(
            "result",
            {}
        )

        event_type = str(
            result.get(
                "eventType",
                ""
            )
        ).lower()

        batter_out_events = {
            "strikeout",
            "strikeout_double_play",
            "groundout",
            "flyout",
            "lineout",
            "pop_out",
            "force_out",
            "field_out",
            "sac_fly",
            "sac_bunt",
            "double_play",
            "triple_play",
            "fielders_choice_out",
        }

        # Runner movement records are the
        # better source because they include
        # multiple outs on one play.

        runner_outs = 0

        for runner in play.get(
            "runners",
            []
        ):

            movement = runner.get(
                "movement",
                {}
            )

            if movement.get(
                "isOut",
                False,
            ):

                runner_outs += 1

        # In MLB play-by-play, the batter is
        # normally represented in runners when
        # retired. Use runner movements first.
        #
        # Only fall back to event type when
        # no out movement was recorded.

        if runner_outs > 0:

            play_outs = runner_outs

        elif (
            event_type
            in batter_out_events
        ):

            if (
                event_type
                == "double_play"
            ):

                play_outs = 2

            elif (
                event_type
                == "triple_play"
            ):

                play_outs = 3

            else:

                play_outs = 1

        total_outs += play_outs

    return total_outs


# =========================================================
# BUILD APPEARANCE OUTS
# =========================================================

def build_outs(
    bullpen,
):

    print(
        "\nCalculating actual relief outs..."
    )

    rows = []

    game_cache = {}

    total = len(
        bullpen
    )

    missing_games = 0

    for number, (
        _,
        row,
    ) in enumerate(
        bullpen.iterrows(),
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
            ] = load_game(
                game_pk
            )

        feed = game_cache[
            game_pk
        ]

        if feed is None:

            missing_games += 1

            outs = None

        else:

            outs = count_pitcher_outs(
                feed,
                row[
                    "pitcher_id"
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

                "team":
                    row[
                        "team"
                    ],

                "pitches":
                    row[
                        "pitches"
                    ],

                "runs_allowed":
                    row[
                        "runs_scored_while_pitching"
                    ],

                "outs_recorded":
                    outs,
            }
        )

        if (
            number % 1000
            == 0
        ):

            print(
                f"Processed "
                f"{number:,} / "
                f"{total:,} appearances"
            )

    result = pd.DataFrame(
        rows
    )

    print()
    print(
        f"Missing cached game rows: "
        f"{missing_games:,}"
    )

    return result


# =========================================================
# BUILD SEASON SUMMARY
# =========================================================

def build_summary(
    appearances,
):

    valid = appearances.dropna(
        subset=[
            "outs_recorded"
        ]
    ).copy()

    summary = (
        valid
        .groupby(
            [
                "pitcher_name",
                "team",
            ]
        )
        .agg(
            appearances=(
                "game_pk",
                "nunique",
            ),

            pitches=(
                "pitches",
                "sum",
            ),

            runs_allowed=(
                "runs_allowed",
                "sum",
            ),

            outs_recorded=(
                "outs_recorded",
                "sum",
            ),
        )
        .reset_index()
    )

    summary[
        "innings_pitched"
    ] = (
        summary[
            "outs_recorded"
        ]
        / 3
    )

    summary[
        "runs_per_9"
    ] = (
        summary[
            "runs_allowed"
        ]
        /
        summary[
            "innings_pitched"
        ]
        .replace(
            0,
            pd.NA,
        )
        * 9
    )

    return (
        summary
        .sort_values(
            "innings_pitched",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Loading bullpen appearances..."
    )

    bullpen = pd.read_csv(
        BULLPEN_FILE
    )

    print(
        f"Loaded "
        f"{len(bullpen):,} "
        f"reliever appearances."
    )

    appearances = build_outs(
        bullpen
    )

    summary = build_summary(
        appearances
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "=" * 90
    )

    print(
        "RELIEVER ACTUAL OUTS CHECK"
    )

    print(
        "=" * 90
    )

    print()

    print(
        summary[
            [
                "pitcher_name",
                "team",
                "appearances",
                "pitches",
                "runs_allowed",
                "outs_recorded",
                "innings_pitched",
                "runs_per_9",
            ]
        ]
        .head(30)
        .to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()