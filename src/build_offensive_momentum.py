from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "pitching_2026.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "offensive_momentum_2026.csv"
)


# =========================================================
# TEAM NAMES
# =========================================================

TEAM_NAMES = {
    "AZ": "Arizona Diamondbacks",
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CWS": "Chicago White Sox",
    "CHW": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KC": "Kansas City Royals",
    "KCR": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "OAK": "Athletics",
    "ATH": "Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "SDP": "San Diego Padres",
    "SEA": "Seattle Mariners",
    "SF": "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "STL": "St. Louis Cardinals",
    "TB": "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WSH": "Washington Nationals",
}


# =========================================================
# EVENT GROUPS
# =========================================================

HIT_EVENTS = {
    "single",
    "double",
    "triple",
    "home_run",
}

WALK_EVENTS = {
    "walk",
    "intent_walk",
}

STRIKEOUT_EVENTS = {
    "strikeout",
    "strikeout_double_play",
}

HBP_EVENTS = {
    "hit_by_pitch",
}

SAC_FLY_EVENTS = {
    "sac_fly",
    "sac_fly_double_play",
}

NON_AB_EVENTS = (
    WALK_EVENTS
    | HBP_EVENTS
    | SAC_FLY_EVENTS
    | {
        "sac_bunt",
        "catcher_interf",
    }
)


# =========================================================
# HELPERS
# =========================================================

def percentile_score(
    series,
    higher_is_better=True,
):

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    if higher_is_better:

        score = values.rank(
            pct=True,
            method="average",
        )

    else:

        score = (
            1
            - values.rank(
                pct=True,
                method="average",
            )
            + (1 / len(values))
        )

    return (
        score
        .fillna(0.5)
        .clip(0, 1)
        * 100
    )


def get_batting_team(row):

    if row["inning_topbot"] == "Top":
        return row["away_team"]

    return row["home_team"]


def total_bases(event):

    if event == "single":
        return 1

    if event == "double":
        return 2

    if event == "triple":
        return 3

    if event == "home_run":
        return 4

    return 0


# =========================================================
# BUILD PLATE APPEARANCES
# =========================================================

def build_plate_appearances(data):

    print(
        "Building completed plate appearances..."
    )

    data = data.copy()

    data["game_date"] = pd.to_datetime(
        data["game_date"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "game_date",
            "game_pk",
            "at_bat_number",
            "inning_topbot",
            "home_team",
            "away_team",
        ]
    )

    plate_appearances = (
        data.sort_values(
            [
                "game_date",
                "game_pk",
                "at_bat_number",
                "pitch_number",
            ]
        )
        .groupby(
            [
                "game_pk",
                "at_bat_number",
            ],
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    plate_appearances = (
        plate_appearances[
            plate_appearances[
                "events"
            ].notna()
        ]
        .copy()
    )

    plate_appearances[
        "team_code"
    ] = plate_appearances.apply(
        get_batting_team,
        axis=1,
    )

    plate_appearances[
        "team"
    ] = (
        plate_appearances[
            "team_code"
        ]
        .map(TEAM_NAMES)
    )

    plate_appearances = (
        plate_appearances.dropna(
            subset=["team"]
        )
    )

    plate_appearances[
        "is_hit"
    ] = (
        plate_appearances[
            "events"
        ]
        .isin(HIT_EVENTS)
        .astype(int)
    )

    plate_appearances[
        "is_walk"
    ] = (
        plate_appearances[
            "events"
        ]
        .isin(WALK_EVENTS)
        .astype(int)
    )

    plate_appearances[
        "is_hbp"
    ] = (
        plate_appearances[
            "events"
        ]
        .isin(HBP_EVENTS)
        .astype(int)
    )

    plate_appearances[
        "is_strikeout"
    ] = (
        plate_appearances[
            "events"
        ]
        .isin(STRIKEOUT_EVENTS)
        .astype(int)
    )

    plate_appearances[
        "is_sac_fly"
    ] = (
        plate_appearances[
            "events"
        ]
        .isin(SAC_FLY_EVENTS)
        .astype(int)
    )

    plate_appearances[
        "is_ab"
    ] = (
        ~plate_appearances[
            "events"
        ]
        .isin(NON_AB_EVENTS)
    ).astype(int)

    plate_appearances[
        "total_bases"
    ] = (
        plate_appearances[
            "events"
        ]
        .map(total_bases)
    )

    return plate_appearances


# =========================================================
# BUILD TEAM-GAME OFFENSE
# =========================================================

def build_team_games(pa):

    print(
        "Building team-game offense..."
    )

    grouped = (
        pa.groupby(
            [
                "team",
                "game_pk",
                "game_date",
            ],
            as_index=False,
        )
        .agg(
            plate_appearances=(
                "events",
                "size",
            ),
            at_bats=(
                "is_ab",
                "sum",
            ),
            hits=(
                "is_hit",
                "sum",
            ),
            walks=(
                "is_walk",
                "sum",
            ),
            hbp=(
                "is_hbp",
                "sum",
            ),
            strikeouts=(
                "is_strikeout",
                "sum",
            ),
            sac_flies=(
                "is_sac_fly",
                "sum",
            ),
            total_bases=(
                "total_bases",
                "sum",
            ),
            runs=(
                "post_bat_score",
                "max",
            ),
        )
    )

    grouped["runs"] = pd.to_numeric(
        grouped["runs"],
        errors="coerce",
    ).fillna(0)

    return grouped


# =========================================================
# WINDOW SUMMARY
# =========================================================

def summarize_window(team_games):

    games = len(team_games)

    pa = team_games[
        "plate_appearances"
    ].sum()

    ab = team_games[
        "at_bats"
    ].sum()

    hits = team_games[
        "hits"
    ].sum()

    walks = team_games[
        "walks"
    ].sum()

    hbp = team_games[
        "hbp"
    ].sum()

    strikeouts = team_games[
        "strikeouts"
    ].sum()

    sac_flies = team_games[
        "sac_flies"
    ].sum()

    total_bases = team_games[
        "total_bases"
    ].sum()

    runs = team_games[
        "runs"
    ].sum()

    batting_average = (
        hits / ab
        if ab
        else np.nan
    )

    obp_denominator = (
        ab
        + walks
        + hbp
        + sac_flies
    )

    obp = (
        (
            hits
            + walks
            + hbp
        )
        / obp_denominator
        if obp_denominator
        else np.nan
    )

    slg = (
        total_bases / ab
        if ab
        else np.nan
    )

    ops = (
        obp + slg
        if pd.notna(obp)
        and pd.notna(slg)
        else np.nan
    )

    iso = (
        slg - batting_average
        if pd.notna(slg)
        and pd.notna(
            batting_average
        )
        else np.nan
    )

    walk_rate = (
        walks / pa
        if pa
        else np.nan
    )

    strikeout_rate = (
        strikeouts / pa
        if pa
        else np.nan
    )

    runs_per_game = (
        runs / games
        if games
        else np.nan
    )

    return {
        "games": games,
        "runs_per_game": runs_per_game,
        "batting_average": batting_average,
        "obp": obp,
        "slg": slg,
        "ops": ops,
        "iso": iso,
        "walk_rate": walk_rate,
        "strikeout_rate": strikeout_rate,
    }


# =========================================================
# BUILD TEAM WINDOWS
# =========================================================

def build_windows(team_games):

    print(
        "Building season / Last 15 / Last 7 windows..."
    )

    rows = []

    for team, games in team_games.groupby(
        "team"
    ):

        games = games.sort_values(
            [
                "game_date",
                "game_pk",
            ]
        ).copy()

        season = summarize_window(
            games
        )

        last_15 = summarize_window(
            games.tail(15)
        )

        last_7 = summarize_window(
            games.tail(7)
        )

        row = {
            "team": team,
        }

        for prefix, summary in [
            ("season", season),
            ("last_15", last_15),
            ("last_7", last_7),
        ]:

            for metric, value in (
                summary.items()
            ):

                row[
                    f"{prefix}_{metric}"
                ] = value

        rows.append(row)

    return pd.DataFrame(rows)


# =========================================================
# OFFENSIVE STRENGTH
# =========================================================

def add_strength_score(
    df,
    prefix,
):

    ops_score = percentile_score(
        df[f"{prefix}_ops"]
    )

    runs_score = percentile_score(
        df[
            f"{prefix}_runs_per_game"
        ]
    )

    iso_score = percentile_score(
        df[f"{prefix}_iso"]
    )

    walk_score = percentile_score(
        df[
            f"{prefix}_walk_rate"
        ]
    )

    strikeout_score = percentile_score(
        df[
            f"{prefix}_strikeout_rate"
        ],
        higher_is_better=False,
    )

    df[
        f"{prefix}_offense_score"
    ] = (
        0.35 * ops_score
        + 0.30 * runs_score
        + 0.15 * iso_score
        + 0.10 * walk_score
        + 0.10 * strikeout_score
    )

    return df


# =========================================================
# MOMENTUM
# =========================================================

def build_momentum(df):

    print(
        "Scoring offensive momentum..."
    )

    df = add_strength_score(
        df,
        "season",
    )

    df = add_strength_score(
        df,
        "last_15",
    )

    df = add_strength_score(
        df,
        "last_7",
    )

    # How much better/worse the last 15
    # are than the team's season level.
    df["trend_raw"] = (
        df[
            "last_15_offense_score"
        ]
        - df[
            "season_offense_score"
        ]
    )

    # Whether the last 7 are improving
    # or declining relative to the last 15.
    df["acceleration_raw"] = (
        df[
            "last_7_offense_score"
        ]
        - df[
            "last_15_offense_score"
        ]
    )

    df["trend_score"] = (
        percentile_score(
            df["trend_raw"]
        )
    )

    df["acceleration_score"] = (
        percentile_score(
            df["acceleration_raw"]
        )
    )

    # =====================================================
    # FINAL OFFENSIVE MOMENTUM SCORE
    # =====================================================
    #
    # Current production matters most.
    #
    # 65% Last 15 offense
    # 20% Last 7 offense
    # 15% Trend vs season
    #
    # =====================================================

    df[
        "offensive_momentum_score"
    ] = (
        0.65
        * df[
            "last_15_offense_score"
        ]
        + 0.20
        * df[
            "last_7_offense_score"
        ]
        + 0.15
        * df[
            "trend_score"
        ]
    )

    df[
        "offensive_momentum_rank"
    ] = (
        df[
            "offensive_momentum_score"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    # =====================================================
    # CURRENT OFFENSIVE LEVEL
    # =====================================================

    def offense_level(score):

        if score >= 80:
            return "HOT"

        if score >= 65:
            return "STRONG"

        if score >= 40:
            return "AVERAGE"

        if score >= 25:
            return "COLD"

        return "VERY COLD"

    df["offense_level"] = (
        df[
            "last_15_offense_score"
        ]
        .apply(
            offense_level
        )
    )

    # =====================================================
    # DIRECTION
    # =====================================================

    def offense_direction(row):

        trend = row[
            "trend_raw"
        ]

        acceleration = row[
            "acceleration_raw"
        ]

        if (
            trend < -8
            and acceleration >= 8
        ):
            return "REBOUNDING"

        if (
            trend >= 8
            and acceleration >= 5
        ):
            return "HEATING UP"

        if (
            trend >= 8
            and acceleration <= -5
        ):
            return "COOLING FROM PEAK"

        if (
            trend <= -8
            and acceleration <= -5
        ):
            return "COOLING"

        if acceleration >= 5:
            return "RISING"

        if acceleration <= -5:
            return "FADING"

        return "STEADY"

    df[
        "offense_direction"
    ] = (
        df.apply(
            offense_direction,
            axis=1,
        )
    )

    return df


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "Loading Statcast data..."
    )

    data = pd.read_csv(
        INPUT_FILE,
        low_memory=False,
    )

    print(
        f"Loaded {len(data):,} pitches."
    )

    plate_appearances = (
        build_plate_appearances(
            data
        )
    )

    print(
        f"Completed plate appearances: "
        f"{len(plate_appearances):,}"
    )

    team_games = (
        build_team_games(
            plate_appearances
        )
    )

    print(
        f"Team-game rows: "
        f"{len(team_games):,}"
    )

    momentum = (
        build_windows(
            team_games
        )
    )

    momentum = (
        build_momentum(
            momentum
        )
    )

    momentum = (
        momentum.sort_values(
            [
                "offensive_momentum_rank",
                "team",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    momentum.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 110)
    print(
        "OCTOBER SHIFT // "
        "OFFENSIVE MOMENTUM"
    )
    print("=" * 110)
    print()

    display_columns = [
        "offensive_momentum_rank",
        "team",
        "offensive_momentum_score",
        "offense_level",
        "offense_direction",
        "last_15_runs_per_game",
        "last_15_ops",
        "last_15_iso",
        "last_15_walk_rate",
        "last_15_strikeout_rate",
        "season_offense_score",
        "last_15_offense_score",
        "last_7_offense_score",
        "trend_raw",
        "acceleration_raw",
    ]

    print(
        momentum[
            display_columns
        ]
        .head(30)
        .to_string(
            index=False
        )
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()