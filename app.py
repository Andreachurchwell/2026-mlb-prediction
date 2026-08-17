from pathlib import Path
import base64

import pandas as pd
import streamlit as st


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contender_scores_2026.csv"
)

HISTORY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ranking_history_2026.csv"
)

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
)

STARTERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pitcher_starts_2026.csv"
)

ASSETS_DIR = PROJECT_ROOT / "assets"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="October Shift // MLB 2026",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# TEAM METADATA
# =========================================================

TEAM_META = {
    # AL EAST
    "Baltimore Orioles": {
        "league": "AL",
        "division": "East",
    },
    "Boston Red Sox": {
        "league": "AL",
        "division": "East",
    },
    "New York Yankees": {
        "league": "AL",
        "division": "East",
    },
    "Tampa Bay Rays": {
        "league": "AL",
        "division": "East",
    },
    "Toronto Blue Jays": {
        "league": "AL",
        "division": "East",
    },

    # AL CENTRAL
    "Chicago White Sox": {
        "league": "AL",
        "division": "Central",
    },
    "Cleveland Guardians": {
        "league": "AL",
        "division": "Central",
    },
    "Detroit Tigers": {
        "league": "AL",
        "division": "Central",
    },
    "Kansas City Royals": {
        "league": "AL",
        "division": "Central",
    },
    "Minnesota Twins": {
        "league": "AL",
        "division": "Central",
    },

    # AL WEST
    "Athletics": {
        "league": "AL",
        "division": "West",
    },
    "Houston Astros": {
        "league": "AL",
        "division": "West",
    },
    "Los Angeles Angels": {
        "league": "AL",
        "division": "West",
    },
    "Seattle Mariners": {
        "league": "AL",
        "division": "West",
    },
    "Texas Rangers": {
        "league": "AL",
        "division": "West",
    },

    # NL EAST
    "Atlanta Braves": {
        "league": "NL",
        "division": "East",
    },
    "Miami Marlins": {
        "league": "NL",
        "division": "East",
    },
    "New York Mets": {
        "league": "NL",
        "division": "East",
    },
    "Philadelphia Phillies": {
        "league": "NL",
        "division": "East",
    },
    "Washington Nationals": {
        "league": "NL",
        "division": "East",
    },

    # NL CENTRAL
    "Chicago Cubs": {
        "league": "NL",
        "division": "Central",
    },
    "Cincinnati Reds": {
        "league": "NL",
        "division": "Central",
    },
    "Milwaukee Brewers": {
        "league": "NL",
        "division": "Central",
    },
    "Pittsburgh Pirates": {
        "league": "NL",
        "division": "Central",
    },
    "St. Louis Cardinals": {
        "league": "NL",
        "division": "Central",
    },

    # NL WEST
    "Arizona Diamondbacks": {
        "league": "NL",
        "division": "West",
    },
    "Colorado Rockies": {
        "league": "NL",
        "division": "West",
    },
    "Los Angeles Dodgers": {
        "league": "NL",
        "division": "West",
    },
    "San Diego Padres": {
        "league": "NL",
        "division": "West",
    },
    "San Francisco Giants": {
        "league": "NL",
        "division": "West",
    },
}


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    board = pd.read_csv(DATA_FILE)
    games = pd.read_csv(GAMES_FILE)
    starters = pd.read_csv(STARTERS_FILE)

    if HISTORY_FILE.exists():
        history = pd.read_csv(HISTORY_FILE)
    else:
        history = pd.DataFrame(
            columns=[
                "snapshot_date",
                "team",
                "rank",
                "october_shift_score",
            ]
        )

    games["date"] = pd.to_datetime(
        games["date"]
    )

    starters["date"] = pd.to_datetime(
        starters["date"]
    )

    if not history.empty:
        history["snapshot_date"] = pd.to_datetime(
            history["snapshot_date"]
        )

    board["league"] = board["team"].map(
        lambda team: TEAM_META.get(
            team,
            {}
        ).get(
            "league",
            "?"
        )
    )

    board["division"] = board["team"].map(
        lambda team: TEAM_META.get(
            team,
            {}
        ).get(
            "division",
            "?"
        )
    )

    return board, games, starters, history


board, games, starters, history = load_data()

latest_game_date = (
    games["date"]
    .max()
    .strftime("%b %d, %Y")
)


# =========================================================
# RANK MOVEMENT
# =========================================================

def add_rank_movement(
    board,
    history,
):

    result = board.copy()

    result["previous_rank"] = pd.NA
    result["rank_change"] = pd.NA
    result["movement_label"] = "NEW"
    result["movement_class"] = "movement-new"

    if history.empty:
        return result

    snapshot_dates = (
        history["snapshot_date"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if len(snapshot_dates) < 2:
        return result

    previous_date = snapshot_dates[-2]

    previous = (
        history[
            history["snapshot_date"]
            == previous_date
        ][
            [
                "team",
                "rank",
            ]
        ]
        .rename(
            columns={
                "rank":
                    "previous_rank"
            }
        )
    )

    result = result.drop(
        columns=[
            "previous_rank",
        ]
    ).merge(
        previous,
        on="team",
        how="left",
    )

    result["rank_change"] = (
        result["previous_rank"]
        - result["rank"]
    )

    def movement_label(row):

        if pd.isna(row["previous_rank"]):
            return "NEW"

        change = int(
            row["rank_change"]
        )

        if change > 0:
            return f"▲ {change}"

        if change < 0:
            return f"▼ {abs(change)}"

        return "—"

    def movement_class(row):

        if pd.isna(row["previous_rank"]):
            return "movement-new"

        change = int(
            row["rank_change"]
        )

        if change > 0:
            return "movement-up"

        if change < 0:
            return "movement-down"

        return "movement-flat"

    result["movement_label"] = result.apply(
        movement_label,
        axis=1,
    )

    result["movement_class"] = result.apply(
        movement_class,
        axis=1,
    )

    return result


board = add_rank_movement(
    board,
    history,
)


# =========================================================
# PITCHER ID / HEADSHOT HELPERS
# =========================================================

def build_pitcher_id_map(starters):

    home = starters[
        [
            "date",
            "home_starter_name",
            "home_starter_id",
        ]
    ].rename(
        columns={
            "home_starter_name": "pitcher_name",
            "home_starter_id": "pitcher_id",
        }
    )

    away = starters[
        [
            "date",
            "away_starter_name",
            "away_starter_id",
        ]
    ].rename(
        columns={
            "away_starter_name": "pitcher_name",
            "away_starter_id": "pitcher_id",
        }
    )

    ids = pd.concat(
        [home, away],
        ignore_index=True,
    )

    ids = ids.dropna(
        subset=[
            "pitcher_name",
            "pitcher_id",
        ]
    )

    ids = (
        ids
        .sort_values(
            [
                "pitcher_name",
                "date",
            ]
        )
        .groupby(
            "pitcher_name",
            as_index=False,
        )
        .tail(1)
    )

    return {
        row["pitcher_name"]: int(row["pitcher_id"])
        for _, row in ids.iterrows()
    }


PITCHER_ID_MAP = build_pitcher_id_map(
    starters
)


def pitcher_headshot_url(pitcher_name):

    pitcher_id = PITCHER_ID_MAP.get(
        pitcher_name
    )

    if pitcher_id is None:
        return ""

    # MLB's player image service uses the MLBAM player ID.
    # The default image in the URL provides a fallback if a
    # current headshot is unavailable.
    return (
        "https://img.mlbstatic.com/mlb-photos/image/upload/"
        "w_260,d_people:generic:headshot:silo:current.png,"
        "q_auto:best,f_auto/"
        f"v1/people/{pitcher_id}/headshot/67/current"
    )


# =========================================================
# LOGO HELPERS
# =========================================================

def find_logo(team):
    filename_map = {
        "Arizona Diamondbacks": "arizona-diamondbacks-logo.png",
        "Atlanta Braves": "atlanta-braves-logo.png",
        "Baltimore Orioles": "baltimore-orioles-logo.png",
        "Boston Red Sox": "boston-red-sox-logo.png",
        "Chicago Cubs": "chicago-cubs-logo.png",
        "Chicago White Sox": "chicago-white-sox-logo.png",
        "Cincinnati Reds": "cincinnati-reds-logo.png",
        "Cleveland Guardians": "cleveland-indians-logo.png",
        "Colorado Rockies": "colorado-rockies-logo.png",
        "Detroit Tigers": "detroit-tigers-logo.png",
        "Houston Astros": "houston-astros-logo.png",
        "Kansas City Royals": "kansas-city-royals-logo.png",
        "Los Angeles Angels": "los-angeles-angels-logo.png",
        "Los Angeles Dodgers": "los-angeles-dodgers-logo.png",
        "Miami Marlins": "miami-marlins-logo.png",
        "Milwaukee Brewers": "milwaukee-brewers-logo.png",
        "Minnesota Twins": "minnesota-twins-logo.png",
        "New York Mets": "new-york-mets-logo.png",
        "New York Yankees": "new-york-yankees-logo.png",
        "Athletics": "oakland-athletics-logo.png",
        "Philadelphia Phillies": "philadelphia-phillies-logo.png",
        "Pittsburgh Pirates": "pittsburgh-pirates-logo.png",
        "San Diego Padres": "san-diego-padres-logo.png",
        "San Francisco Giants": "san-francisco-giants-logo.png",
        "Seattle Mariners": "seattle-mariners-logo.png",
        "St. Louis Cardinals": "st-louis-cardinals-logo.png",
        "Tampa Bay Rays": "tampa-bay-rays-logo.png",
        "Texas Rangers": "texas-rangers-logo.png",
        "Toronto Blue Jays": "toronto-blue-jays-logo.png",
        "Washington Nationals": "washington-nationals-logo.png",
    }

    filename = filename_map.get(team)

    if not filename:
        return None

    logo_path = ASSETS_DIR / filename

    if logo_path.exists():
        return logo_path

    return None


def image_to_base64(path):

    if path is None:
        return ""

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")

    return (
        "data:image/png;base64,"
        + encoded
    )


def team_logo(team):

    path = find_logo(team)

    if path is None:
        return ""

    return image_to_base64(path)


# =========================================================
# CSS
# =========================================================

st.html(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap'
    );

    :root {
        --bg: #071014;
        --panel: #0D171C;
        --panel2: #111D22;
        --text: #F8FCFD;
        --text-soft: #D7E2E5;
        --muted: #A7B8BD;
        --cyan: #44F4FF;
        --green: #C7FF63;
        --line: rgba(68,244,255,0.35);
        --soft-line: rgba(255,255,255,0.13);
    }

    html, body { background: var(--bg); }

    .stApp {
        background:
            radial-gradient(circle at 10% 0%, rgba(68,244,255,0.10), transparent 28%),
            radial-gradient(circle at 90% 20%, rgba(199,255,99,0.05), transparent 24%),
            var(--bg);
        color: var(--text);
    }

    .block-container { max-width: 1500px; padding-top: 2rem; padding-bottom: 5rem; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }

    .hero {
        position: relative; padding: 42px; border: 1px solid var(--line);
        background: linear-gradient(135deg, rgba(68,244,255,0.08), rgba(199,255,99,0.03)), #0B151A;
        overflow: hidden; margin-bottom: 32px;
    }
    .hero::before { content: ""; position: absolute; top: 0; left: 0; width: 190px; height: 3px; background: var(--cyan); }
    .hero::after { content: "01"; position: absolute; right: 28px; top: 20px; font-family: 'Orbitron', sans-serif; font-size: 110px; font-weight: 900; color: rgba(255,255,255,0.025); }
    .hero-kicker { font-family: 'Orbitron', sans-serif; font-size: 12px; font-weight: 700; letter-spacing: 4px; color: var(--cyan); margin-bottom: 15px; }
    .hero-title { font-family: 'Orbitron', sans-serif; font-size: clamp(42px,6vw,82px); font-weight: 900; line-height: .95; letter-spacing: -2px; color: #fff; }
    .hero-title span { color: var(--green); text-shadow: 0 0 12px rgba(199,255,99,.22); }
    .hero-sub { max-width: 780px; margin-top: 24px; font-family: 'Space Grotesk', sans-serif; font-size: 16px; font-weight: 500; line-height: 1.75; color: var(--text-soft); }
    .hero-status { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 26px; }
    .status-chip { padding: 9px 12px; border: 1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.04); font-family: 'Orbitron', sans-serif; font-size: 9px; font-weight: 600; letter-spacing: 1.5px; color: #E2ECEE; }
    .status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 8px; background: var(--green); }

    .section-label { margin: 36px 0 16px; padding-left: 12px; border-left: 3px solid var(--cyan); font-family: 'Orbitron', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; color: var(--cyan); }

    .leader-card { position: relative; min-height: 330px; padding: 24px; border: 1px solid rgba(68,244,255,.32); background: linear-gradient(145deg,#101B20,#0A1216); overflow: hidden; }
    .leader-card::after { content:""; position:absolute; width:90px; height:90px; right:-48px; top:-48px; transform:rotate(45deg); border:1px solid rgba(68,244,255,.18); }
    .leader-rank { font-family:'Orbitron',sans-serif; font-size:10px; font-weight:700; letter-spacing:3px; color:var(--cyan); }
    .leader-logo { display:block; width:96px; height:96px; object-fit:contain; margin:18px 0 16px; padding:10px; background:#F7FAFB; border-radius:12px; box-shadow:0 0 0 1px rgba(255,255,255,.08); }
    .leader-team { min-height:46px; font-family:'Orbitron',sans-serif; font-size:18px; font-weight:800; line-height:1.25; color:#fff; }
    .leader-record { margin-top:7px; font-family:'Space Grotesk',sans-serif; font-size:12px; font-weight:500; color:var(--muted); }
    .leader-score { margin-top:20px; font-family:'Orbitron',sans-serif; font-size:40px; font-weight:900; color:var(--green); }
    .leader-score-label { margin-top:6px; font-family:'Orbitron',sans-serif; font-size:9px; font-weight:600; letter-spacing:2px; color:var(--text-soft); }

    .rank-row { display:grid; grid-template-columns:55px 60px minmax(220px,1.7fr) 70px 90px 100px 100px 100px 110px; gap:12px; align-items:center; padding:15px 14px; border-bottom:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.025); transition:.2s ease; }
    .rank-row:hover { background:rgba(68,244,255,.07); border-left:2px solid var(--cyan); }
    .rank-num { font-family:'Orbitron',sans-serif; font-size:18px; font-weight:700; color:#B9C9CD; }
    .rank-logo { display:block; width:46px; height:46px; object-fit:contain; padding:5px; background:#F7FAFB; border-radius:8px; }
    .rank-team { font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:700; color:#fff; }
    .rank-team-meta { margin-top:3px; font-family:'Orbitron',sans-serif; font-size:9px; font-weight:600; letter-spacing:1.2px; color:#A8B8BC; }
    .rank-stat { font-family:'Orbitron',sans-serif; font-size:11px; font-weight:600; color:#D0DCDF; }
    .rank-score { text-align:right; font-family:'Orbitron',sans-serif; font-size:20px; font-weight:800; color:var(--green); }
    .rank-move { font-family:'Orbitron',sans-serif; font-size:10px; font-weight:800; letter-spacing:.7px; text-align:center; white-space:nowrap; }
    .movement-up { color:var(--green); }
    .movement-down { color:#FF7A8A; }
    .movement-flat { color:#8FA1A6; }
    .movement-new { color:var(--cyan); }
    .leader-move { margin-top:8px; display:inline-block; padding:5px 8px; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.025); font-family:'Orbitron',sans-serif; font-size:9px; font-weight:800; letter-spacing:1px; }


    .intel { margin-top:16px; padding:32px; border:1px solid rgba(68,244,255,.30); background:#0D171C; }
    .intel-head { display:flex; align-items:center; gap:24px; margin-bottom:28px; }
    .intel-logo { width:105px; height:105px; object-fit:contain; padding:10px; background:#F7FAFB; border-radius:14px; }
    .intel-team { font-family:'Orbitron',sans-serif; font-size:30px; font-weight:900; color:#fff; }
    .intel-meta { margin-top:7px; font-family:'Orbitron',sans-serif; font-size:10px; font-weight:600; letter-spacing:1.8px; color:#B1C0C4; }

    .score-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; }
    .score-module { padding:18px 14px; border:1px solid rgba(255,255,255,.12); background:#111D22; }
    .module-value { font-family:'Orbitron',sans-serif; font-size:20px; font-weight:700; color:var(--cyan); }
    .module-label { margin-top:7px; font-family:'Orbitron',sans-serif; font-size:8px; font-weight:600; line-height:1.5; letter-spacing:1.2px; text-transform:uppercase; color:#B3C2C6; }

    div[data-baseweb="select"] > div { background:#111D22 !important; border:1px solid rgba(68,244,255,.30) !important; border-radius:0 !important; color:#fff !important; }
    button[data-baseweb="tab"] { font-family:'Orbitron',sans-serif !important; font-size:10px !important; font-weight:700 !important; letter-spacing:1.5px !important; color:#EAF2F4 !important; }

    .logic-card { height:100%; padding:26px; border:1px solid rgba(255,255,255,.11); background:#0D171C; }
    .logic-title { margin-bottom:17px; font-family:'Orbitron',sans-serif; font-size:11px; font-weight:700; letter-spacing:2px; color:var(--cyan); }
    .logic-row { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,.07); font-family:'Space Grotesk',sans-serif; font-size:14px; font-weight:500; color:#D0DCDF; }
    .logic-weight { font-family:'Orbitron',sans-serif; font-weight:700; color:var(--green); }
    .logic-text { font-family:'Space Grotesk',sans-serif; font-size:15px; font-weight:500; line-height:1.8; color:#D0DCDF; }


    .rotation-panel { margin-top:14px; padding:26px; border:1px solid rgba(199,255,99,.28); background:linear-gradient(135deg,rgba(199,255,99,.045),#0D171C); }
    .rotation-topline { margin-bottom:18px; }
    .rotation-title { font-family:'Orbitron',sans-serif; font-size:12px; font-weight:800; letter-spacing:2px; color:var(--green); }
    .rotation-stat-strip { display:grid; grid-template-columns:110px 110px minmax(190px,1.5fr) 110px 110px; gap:10px; margin:16px 0 20px; }
    .rotation-stat-box { min-width:0; padding:12px 13px; border:1px solid rgba(255,255,255,.11); background:rgba(255,255,255,.025); }
    .rotation-stat-label { font-family:'Orbitron',sans-serif; font-size:7px; font-weight:700; letter-spacing:1.4px; color:#8FA1A6; margin-bottom:7px; }
    .rotation-stat-value { font-family:'Orbitron',sans-serif; font-size:17px; font-weight:800; line-height:1.2; color:#fff; overflow-wrap:anywhere; }
    .rotation-stat-value.green { color:var(--green); }
    .rotation-stat-value.cyan { color:var(--cyan); }
    .rotation-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
    .rotation-arm { min-width:0; padding:0 13px 16px; border:1px solid rgba(255,255,255,.12); background:#111D22; overflow:hidden; }
    .rotation-photo-wrap { height:190px; margin:0 -13px 14px; overflow:hidden; background:linear-gradient(180deg,rgba(68,244,255,.08),rgba(255,255,255,.025)); border-bottom:1px solid rgba(255,255,255,.10); }
    .rotation-photo { width:100%; height:100%; object-fit:contain; object-position:center bottom; display:block; }
    .rotation-photo-fallback { height:100%; display:flex; align-items:center; justify-content:center; padding:12px; text-align:center; font-family:'Orbitron',sans-serif; font-size:9px; letter-spacing:1.3px; color:#809398; }
    .rotation-slot { font-family:'Orbitron',sans-serif; font-size:8px; letter-spacing:1.5px; color:var(--cyan); margin-bottom:7px; }
    .rotation-name { font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:700; color:#fff; line-height:1.25; overflow-wrap:anywhere; }
    .rotation-note { margin-top:15px; padding-top:13px; border-top:1px solid rgba(255,255,255,.07); font-family:'Space Grotesk',sans-serif; font-size:12px; line-height:1.65; color:#A7B8BD; }

    .tech-footer { margin-top:60px; padding-top:18px; border-top:1px solid rgba(255,255,255,.08); font-family:'Orbitron',sans-serif; font-size:8px; font-weight:600; letter-spacing:2px; color:#90A2A6; }

    @media (max-width:1100px) {
        .rotation-stat-strip {
            grid-template-columns:repeat(2,minmax(0,1fr));
        }
        .rotation-stat-box:nth-child(3) {
            grid-column:span 2;
        }
        .rotation-grid {
            grid-template-columns:repeat(2,minmax(0,1fr));
        }
    }

    @media (max-width:900px) {
        .block-container { padding-left:1rem; padding-right:1rem; }
        .hero { padding:28px 22px; }
        .rank-row { grid-template-columns:35px 46px minmax(0,1fr) 52px 68px; }
        .rank-hide-mobile { display:none; }
        .score-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .intel { padding:22px; }
        .intel-head { gap:16px; }
        .intel-logo { width:82px; height:82px; }
        .intel-team { font-size:22px; }
        .rotation-panel { padding:20px; }
        .rotation-photo-wrap { height:175px; }
    }

    @media (max-width:620px) {
        .block-container { padding-left:.75rem; padding-right:.75rem; }
        .hero { padding:24px 18px; }
        .hero-title { font-size:38px; letter-spacing:-1px; }
        .hero-sub { font-size:14px; }
        .intel { padding:18px; }
        .intel-head { align-items:flex-start; }
        .intel-logo { width:70px; height:70px; }
        .intel-team { font-size:18px; }
        .intel-meta { line-height:1.8; }
        .score-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
        .score-module { padding:14px 10px; }
        .module-value { font-size:17px; }
        .rotation-panel { padding:16px; }
        .rotation-title { font-size:10px; line-height:1.6; }
        .rotation-stat-strip {
            grid-template-columns:repeat(2,minmax(0,1fr));
            gap:8px;
        }
        .rotation-stat-box { padding:11px 10px; }
        .rotation-stat-box:nth-child(3) { grid-column:1 / -1; }
        .rotation-stat-value { font-size:15px; }
        .rotation-grid { grid-template-columns:1fr; gap:10px; }
        .rotation-photo-wrap { height:220px; }
        .rotation-name { font-size:17px; }
        .rotation-note { font-size:11px; }
        .rank-move { font-size:8px; }
        .rank-score { font-size:16px; }

    }

    @media (max-width:400px) {
        .score-grid { grid-template-columns:1fr 1fr; }
        .rotation-stat-strip { grid-template-columns:1fr 1fr; }
        .rotation-photo-wrap { height:205px; }
    }

    </style>
    """
)


# =========================================================
# HERO
# =========================================================

st.html(
    f"""
    <div class="hero">

        <div class="hero-kicker">
            MLB // 2026 ANALYTICS SYSTEM
        </div>

        <div class="hero-title">
            OCTOBER<br>
            <span>SHIFT</span>
        </div>

        <div class="hero-sub">

            A live 2026 MLB postseason contender system built around
            current form, run differential, opponent-adjusted performance,
            season strength and projected postseason rotation ceiling.

            The October Shift Score is a relative contender rating,
            not a World Series probability.

        </div>

        <div class="hero-status">

            <div class="status-chip">
                <span class="status-dot"></span>
                DATA ONLINE
            </div>

            <div class="status-chip">
                LAST GAME //
                {latest_game_date.upper()}
            </div>

            <div class="status-chip">
                {len(games):,}
                GAMES INGESTED
            </div>

            <div class="status-chip">
                30 TEAMS TRACKED
            </div>

        </div>

    </div>
    """
)


# =========================================================
# TOP FOUR
# =========================================================

st.html(
    """
    <div class="section-label">
        OCTOBER LEADERS // TOP 04
    </div>
    """
)


top_four = board.head(4)

columns = st.columns(4)


for column, (_, team) in zip(
    columns,
    top_four.iterrows(),
):

    logo = team_logo(
        team["team"]
    )

    if logo:

        logo_html = f"""
        <img
            class="leader-logo"
            src="{logo}"
        >
        """

    else:

        logo_html = """
        <div
            style="
                height:88px;
                margin:18px 0 14px 0;
            "
        ></div>
        """

    with column:

        st.html(
            f"""
            <div class="leader-card">

                <div class="leader-rank">
                    RANK //
                    {int(team["rank"]):02d}
                </div>

                {logo_html}

                <div class="leader-team">
                    {team["team"]}
                </div>

                <div class="leader-record">

                    {int(team["wins"])}
                    -
                    {int(team["losses"])}

                    //

                    {team["league"]}
                    {team["division"].upper()}

                </div>

                <div class="leader-score">
                    {team["october_shift_score"]:.1f}
                </div>

                <div class="leader-score-label">
                    OCTOBER SHIFT SCORE
                </div>

                <div class="leader-move {team["movement_class"]}">
                    SHIFT // {team["movement_label"]}
                </div>

            </div>
            """
        )


# =========================================================
# RANKING TABLE
# =========================================================

def render_ranking_table(data):

    for _, team in data.iterrows():

        logo = team_logo(
            team["team"]
        )

        if logo:

            logo_html = f"""
            <img
                class="rank-logo"
                src="{logo}"
            >
            """

        else:

            logo_html = """
            <div class="rank-logo">
            </div>
            """

        if (
            team[
                "run_diff_per_game"
            ]
            >= 0
        ):

            run_diff = (
                f"+"
                f"{team['run_diff_per_game']:.2f}"
            )

        else:

            run_diff = (
                f"{team['run_diff_per_game']:.2f}"
            )

        st.html(
            f"""
            <div class="rank-row">

                <div class="rank-num">
                    {int(team["rank"]):02d}
                </div>

                <div>
                    {logo_html}
                </div>

                <div>

                    <div class="rank-team">
                        {team["team"]}
                    </div>

                    <div class="rank-team-meta">

                        {team["league"]}
                        //

                        {team["division"].upper()}
                        //

                        {int(team["wins"])}
                        -
                        {int(team["losses"])}

                    </div>

                </div>

                <div class="rank-move {team["movement_class"]}">
                    {team["movement_label"]}
                </div>

                <div
                    class="
                        rank-stat
                        rank-hide-mobile
                    "
                >
                    ROT
                    #{int(team["projected_rotation_rank"])}
                </div>

                <div
                    class="
                        rank-stat
                        rank-hide-mobile
                    "
                >
                    POST
                    {team["post_asb_win_pct"]:.3f}
                </div>

                <div
                    class="
                        rank-stat
                        rank-hide-mobile
                    "
                >
                    L10
                    {team["last_10_win_pct"]:.3f}
                </div>

                <div
                    class="
                        rank-stat
                        rank-hide-mobile
                    "
                >
                    RD/G
                    {run_diff}
                </div>

                <div class="rank-score">
                    {team["october_shift_score"]:.1f}
                </div>

            </div>
            """
        )


# =========================================================
# CONTENDER MATRIX
# =========================================================

st.html(
    """
    <div class="section-label">
        OCTOBER SHIFT MATRIX // LEAGUE VIEW
    </div>
    """
)


overall_tab, nl_tab, al_tab = st.tabs(
    [
        "ALL // 30",
        "NATIONAL // NL",
        "AMERICAN // AL",
    ]
)


with overall_tab:

    render_ranking_table(
        board
    )


with nl_tab:

    nl = (
        board[
            board["league"]
            == "NL"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    render_ranking_table(
        nl
    )


with al_tab:

    al = (
        board[
            board["league"]
            == "AL"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    render_ranking_table(
        al
    )


# =========================================================
# TEAM INTELLIGENCE
# =========================================================

st.html(
    """
    <div class="section-label">
        TEAM INTELLIGENCE // DEEP SCAN
    </div>
    """
)


selected_team = st.selectbox(
    "Select team",
    board["team"].tolist(),
    label_visibility="collapsed",
)


team = (
    board[
        board["team"]
        == selected_team
    ]
    .iloc[0]
)


logo = team_logo(
    selected_team
)


if logo:

    logo_html = f"""
    <img
        class="intel-logo"
        src="{logo}"
    >
    """

else:

    logo_html = ""


if (
    team[
        "run_diff_per_game"
    ]
    >= 0
):

    run_diff = (
        f"+"
        f"{team['run_diff_per_game']:.2f}"
    )

else:

    run_diff = (
        f"{team['run_diff_per_game']:.2f}"
    )


st.html(
    f"""
    <div class="intel">

        <div class="intel-head">

            {logo_html}

            <div>

                <div class="intel-team">
                    {selected_team}
                </div>

                <div class="intel-meta">

                    CONTENDER RANK //
                    {int(team["rank"]):02d}

                    &nbsp;&nbsp;

                    {team["league"]}
                    //
                    {team["division"].upper()}

                    &nbsp;&nbsp;

                    RECORD //
                    {int(team["wins"])}
                    -
                    {int(team["losses"])}

                    &nbsp;&nbsp;

                    SHIFT //
                    <span class="{team["movement_class"]}">
                        {team["movement_label"]}
                    </span>

                </div>

            </div>

        </div>


        <div class="score-grid">

            <div class="score-module">

                <div class="module-value">
                    {team["october_shift_score"]:.1f}
                </div>

                <div class="module-label">
                    October Shift
                    <br>
                    Score
                </div>

            </div>


            <div class="score-module">

                <div class="module-value">
                    {team["post_asb_win_pct"]:.3f}
                </div>

                <div class="module-label">
                    Post All-Star
                    <br>
                    Win Rate
                </div>

            </div>


            <div class="score-module">

                <div class="module-value">
                    {team["last_10_win_pct"]:.3f}
                </div>

                <div class="module-label">
                    Last 10
                    <br>
                    Win Rate
                </div>

            </div>


            <div class="score-module">

                <div class="module-value">
                    {run_diff}
                </div>

                <div class="module-label">
                    Run Differential
                    <br>
                    Per Game
                </div>

            </div>


            <div class="score-module">

                <div class="module-value">
                    {team["quality_weighted_win_pct"]:.3f}
                </div>

                <div class="module-label">
                    Quality Adjusted
                    <br>
                    Win Rate
                </div>

            </div>


            <div class="score-module">

                <div class="module-value">
                    #{int(team["projected_rotation_rank"])}
                </div>

                <div class="module-label">
                    Postseason Rotation
                    <br>
                    Rank
                </div>

            </div>

        </div>

    </div>
    """
)


# =========================================================
# POSTSEASON ROTATION DEEP SCAN
# =========================================================

rotation_names = [
    name.strip()
    for name in str(
        team.get(
            "projected_top_4",
            ""
        )
    ).split("|")
    if name.strip()
]

rotation_cards = []

for index in range(4):

    name = (
        rotation_names[index]
        if index < len(rotation_names)
        else "Depth TBD"
    )

    slot = (
        "ACE"
        if index == 0
        else f"SP{index + 1}"
    )

    headshot = pitcher_headshot_url(
        name
    )

    if headshot:

        photo_html = f"""
        <div class="rotation-photo-wrap">
            <img
                class="rotation-photo"
                src="{headshot}"
                alt="{name}"
                onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=&quot;rotation-photo-fallback&quot;>IMAGE UNAVAILABLE</div>';"
            >
        </div>
        """

    else:

        photo_html = """
        <div class="rotation-photo-wrap">
            <div class="rotation-photo-fallback">
                IMAGE UNAVAILABLE
            </div>
        </div>
        """

    rotation_cards.append(
        f"""
        <div class="rotation-arm">

            {photo_html}

            <div class="rotation-slot">
                {slot}
            </div>

            <div class="rotation-name">
                {name}
            </div>

        </div>
        """
    )


st.html(
    f"""
    <div class="rotation-panel">

        <div class="rotation-topline">

            <div class="rotation-title">
                POSTSEASON ROTATION // PROJECTED TOP 04
            </div>

        </div>

        <div class="rotation-stat-strip">

            <div class="rotation-stat-box">
                <div class="rotation-stat-label">MLB RANK</div>
                <div class="rotation-stat-value cyan">
                    #{int(team["projected_rotation_rank"]):02d}
                </div>
            </div>

            <div class="rotation-stat-box">
                <div class="rotation-stat-label">ROTATION SCORE</div>
                <div class="rotation-stat-value green">
                    {team["projected_rotation_score"]:.1f}
                </div>
            </div>

            <div class="rotation-stat-box">
                <div class="rotation-stat-label">ACE</div>
                <div class="rotation-stat-value">
                    {team["projected_ace"]}
                </div>
            </div>

            <div class="rotation-stat-box">
                <div class="rotation-stat-label">TOP 3</div>
                <div class="rotation-stat-value">
                    {team["projected_top_3_score"]:.1f}
                </div>
            </div>

            <div class="rotation-stat-box">
                <div class="rotation-stat-label">TOP 4</div>
                <div class="rotation-stat-value">
                    {team["projected_top_4_score"]:.1f}
                </div>
            </div>

        </div>

        <div class="rotation-grid">
            {''.join(rotation_cards)}
        </div>

        <div class="rotation-note">
            <strong>ROTATION MODEL:</strong>
            2026 run suppression + quality/deep-start performance,
            then ace strength, top-three quality and four-man depth.
            Minimum 5 starts plus starter-level workload.
            Ceiling only; October health and availability are separate.
        </div>

    </div>
    """
)


# =========================================================
# RANK MOVEMENT STATUS
# =========================================================

if history.empty:

    movement_status = (
        "Ranking history has not started yet."
    )

else:

    history_dates = (
        history["snapshot_date"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    if len(history_dates) < 2:

        movement_status = (
            "FIRST SNAPSHOT SAVED // "
            "Movement begins automatically after the next new game-date snapshot."
        )

    else:

        previous_label = (
            history_dates.iloc[-2]
            .strftime("%b %d")
            .upper()
        )

        latest_label = (
            history_dates.iloc[-1]
            .strftime("%b %d")
            .upper()
        )

        movement_status = (
            f"SHIFT WINDOW // "
            f"{previous_label} → {latest_label}"
        )


st.html(
    f"""
    <div class="section-label">
        RANK MOVEMENT // DAILY SHIFT
    </div>

    <div class="logic-card">
        <div class="logic-title">
            {movement_status}
        </div>

        <div class="logic-text">
            ▲ means a team moved up, ▼ means it moved down,
            and — means its rank held. With only one saved
            snapshot, teams display NEW until the next dated
            snapshot is created by the update pipeline.
        </div>
    </div>
    """
)


# =========================================================
# SYSTEM LOGIC
# =========================================================

st.html(
    """
    <div class="section-label">
        SYSTEM LOGIC // V2.0
    </div>
    """
)


left, right = st.columns(2)


with left:

    st.html(
        """
        <div class="logic-card">

            <div class="logic-title">
                OCTOBER SHIFT SCORE WEIGHTS
            </div>

            <div class="logic-row">
                <span>Postseason rotation ceiling</span>
                <span class="logic-weight">25%</span>
            </div>

            <div class="logic-row">
                <span>Run differential</span>
                <span class="logic-weight">20%</span>
            </div>

            <div class="logic-row">
                <span>Post All-Star performance</span>
                <span class="logic-weight">20%</span>
            </div>

            <div class="logic-row">
                <span>Last 10 games</span>
                <span class="logic-weight">15%</span>
            </div>

            <div class="logic-row">
                <span>Quality-adjusted performance</span>
                <span class="logic-weight">10%</span>
            </div>

            <div class="logic-row">
                <span>Overall 2026 record</span>
                <span class="logic-weight">10%</span>
            </div>

        </div>
        """
    )


with right:

    st.html(
        """
        <div class="logic-card">

            <div class="logic-title">
                HOW TO READ THE MODEL
            </div>

            <div class="logic-text">

                The October Shift Score is not a percentage
                chance of winning the World Series.

                <br><br>

                The system compares all 30 MLB teams using
                postseason rotation ceiling, scoring margin,
                post-All-Star form, recent results, opponent
                quality and overall season strength.

                <br><br>

                Earlier games still matter, but the system
                intentionally gives more importance to how
                a team is performing later in the season.

            </div>

        </div>
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.html(
    """
    <div class="tech-footer">

        OCTOBER SHIFT //
        MLB 2026 //

        LIVE SEASON DATA //

        XGBOOST EXPERIMENTATION +
        CUSTOM POSTSEASON CONTENDER MODEL

    </div>
    """
)