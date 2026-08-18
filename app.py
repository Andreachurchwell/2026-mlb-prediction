from pathlib import Path
import base64

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="October Shift | MLB 2026",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed")

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "contender_scores_2026.csv"
HISTORY_FILE = PROJECT_ROOT / "data" / "processed" / "ranking_history_2026.csv"
# GAMES_FILE = PROJECT_ROOT / "data" / "raw" / "games_2026.csv"
STARTERS_FILE = PROJECT_ROOT / "data" / "processed" / "pitcher_starts_2026.csv"
BULLPEN_APPEARANCES_FILE = PROJECT_ROOT / "data" / "processed" / "bullpen_appearances_2026.csv"
RELIEVER_RUN_FILE = PROJECT_ROOT / "data" / "processed" / "reliever_run_scores_2026.csv"
BULLPEN_FILE = PROJECT_ROOT / "data" / "processed" / "bullpen_scores_2026.csv"
ROTATION_FILE = PROJECT_ROOT / "data" / "processed" / "projected_rotations_2026.csv"
ASSETS_DIR = PROJECT_ROOT / "assets"
MLB_LOGO_FILE = ASSETS_DIR / "mlb-logo.png"

TEAM_META = {
    "Baltimore Orioles": {"league": "AL", "division": "East"},
    "Boston Red Sox": {"league": "AL", "division": "East"},
    "New York Yankees": {"league": "AL", "division": "East"},
    "Tampa Bay Rays": {"league": "AL", "division": "East"},
    "Toronto Blue Jays": {"league": "AL", "division": "East"},
    "Chicago White Sox": {"league": "AL", "division": "Central"},
    "Cleveland Guardians": {"league": "AL", "division": "Central"},
    "Detroit Tigers": {"league": "AL", "division": "Central"},
    "Kansas City Royals": {"league": "AL", "division": "Central"},
    "Minnesota Twins": {"league": "AL", "division": "Central"},
    "Athletics": {"league": "AL", "division": "West"},
    "Houston Astros": {"league": "AL", "division": "West"},
    "Los Angeles Angels": {"league": "AL", "division": "West"},
    "Seattle Mariners": {"league": "AL", "division": "West"},
    "Texas Rangers": {"league": "AL", "division": "West"},
    "Atlanta Braves": {"league": "NL", "division": "East"},
    "Miami Marlins": {"league": "NL", "division": "East"},
    "New York Mets": {"league": "NL", "division": "East"},
    "Philadelphia Phillies": {"league": "NL", "division": "East"},
    "Washington Nationals": {"league": "NL", "division": "East"},
    "Chicago Cubs": {"league": "NL", "division": "Central"},
    "Cincinnati Reds": {"league": "NL", "division": "Central"},
    "Milwaukee Brewers": {"league": "NL", "division": "Central"},
    "Pittsburgh Pirates": {"league": "NL", "division": "Central"},
    "St. Louis Cardinals": {"league": "NL", "division": "Central"},
    "Arizona Diamondbacks": {"league": "NL", "division": "West"},
    "Colorado Rockies": {"league": "NL", "division": "West"},
    "Los Angeles Dodgers": {"league": "NL", "division": "West"},
    "San Diego Padres": {"league": "NL", "division": "West"},
    "San Francisco Giants": {"league": "NL", "division": "West"},
}

TEAM_LOGO_FILES = {
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

MODEL_WEIGHTS = {
    "Starting Rotation": 0.20,
    "Bullpen": 0.05,
    "Offensive Momentum": 0.15,
    "Run Differential": 0.20,
    "Post All-Star Performance": 0.15,
    "Last 10 Games": 0.10,
    "Quality-Adjusted Performance": 0.05,
    "Overall Record": 0.10,
}

@st.cache_data
def load_data():
    board = pd.read_csv(DATA_FILE)
    # games = pd.read_csv(GAMES_FILE)
    starters = pd.read_csv(STARTERS_FILE)
    bullpen_appearances = pd.read_csv(BULLPEN_APPEARANCES_FILE)
    relievers = pd.read_csv(RELIEVER_RUN_FILE)
    bullpen = pd.read_csv(BULLPEN_FILE)
    rotations = pd.read_csv(ROTATION_FILE)

    if HISTORY_FILE.exists():
        history = pd.read_csv(HISTORY_FILE)
    else:
        history = pd.DataFrame(columns=["snapshot_date", "team", "rank", "october_shift_score"])

    # games["date"] = pd.to_datetime(games["date"], errors="coerce")
    starters["date"] = pd.to_datetime(starters["date"], errors="coerce")
    bullpen_appearances["game_date"] = pd.to_datetime(bullpen_appearances["game_date"], errors="coerce")
    if not history.empty:
        history["snapshot_date"] = pd.to_datetime(history["snapshot_date"], errors="coerce")

    board["league"] = board["team"].map(lambda t: TEAM_META.get(t, {}).get("league", "?"))
    board["division"] = board["team"].map(lambda t: TEAM_META.get(t, {}).get("division", "?"))
    return board, starters, bullpen_appearances, relievers, bullpen, rotations, history

board, starters, bullpen_appearances, relievers, bullpen, rotations, history = load_data()
latest_game_date = history["snapshot_date"].max()
latest_game_label = (
    latest_game_date.strftime("%B %d, %Y")
    if pd.notna(latest_game_date)
    else "Unknown"
)

completed_games = int(board["games"].sum() / 2)


def image_to_base64(path):
    if path is None or not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


MLB_LOGO = image_to_base64(MLB_LOGO_FILE)


def team_logo(team):
    filename = TEAM_LOGO_FILES.get(team)
    if not filename:
        return ""
    return image_to_base64(ASSETS_DIR / filename)


def build_pitcher_id_map(starters_df, bullpen_df):
    parts = []
    for prefix in ["home", "away"]:
        n = f"{prefix}_starter_name"
        i = f"{prefix}_starter_id"
        if n in starters_df.columns and i in starters_df.columns:
            parts.append(
                starters_df[["date", n, i]].rename(columns={n: "pitcher_name", i: "pitcher_id"})
            )
    if {"game_date", "pitcher_name", "pitcher_id"}.issubset(bullpen_df.columns):
        parts.append(
            bullpen_df[["game_date", "pitcher_name", "pitcher_id"]]
            .rename(columns={"game_date": "date"})
        )
    if not parts:
        return {}
    ids = pd.concat(parts, ignore_index=True)
    ids["pitcher_id"] = pd.to_numeric(ids["pitcher_id"], errors="coerce")
    ids = ids.dropna(subset=["pitcher_name", "pitcher_id"])
    ids = ids.sort_values(["pitcher_name", "date"]).groupby("pitcher_name", as_index=False).tail(1)
    return {row["pitcher_name"]: int(row["pitcher_id"]) for _, row in ids.iterrows()}


PITCHER_ID_MAP = build_pitcher_id_map(starters, bullpen_appearances)


def pitcher_headshot_url(name):
    pitcher_id = PITCHER_ID_MAP.get(name)
    if pitcher_id is None:
        return ""
    return (
        "https://img.mlbstatic.com/mlb-photos/image/upload/"
        "w_400,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/"
        f"v1/people/{pitcher_id}/headshot/67/current"
    )


def safe_int(value, default=0):
    return default if pd.isna(value) else int(value)


def rank_text(value):
    return "—" if pd.isna(value) else f"#{int(value)}"


def run_diff_text(value):
    if pd.isna(value):
        return "—"
    return f"+{value:.2f}" if value >= 0 else f"{value:.2f}"


def movement_for_team(team_name):
    if history.empty:
        return "NEW", "neutral"
    dates = history["snapshot_date"].dropna().drop_duplicates().sort_values().tolist()
    if len(dates) < 2:
        return "NEW", "neutral"
    previous = history[history["snapshot_date"] == dates[-2]]
    row = previous[previous["team"] == team_name]
    if row.empty:
        return "NEW", "neutral"
    previous_rank = safe_int(row.iloc[0]["rank"])
    current_rank = safe_int(board.loc[board["team"] == team_name, "rank"].iloc[0])
    change = previous_rank - current_rank
    if change > 0:
        return f"▲ {change}", "up"
    if change < 0:
        return f"▼ {abs(change)}", "down"
    return "—", "neutral"


def logo_html(team, css_class):
    logo = team_logo(team)
    if not logo:
        return f'<div class="{css_class} logo-fallback"></div>'
    return f'<img class="{css_class}" src="{logo}" alt="{team}">'


def player_card(name, role="", stat_label="", stat_value=""):
    headshot = pitcher_headshot_url(name)
    photo = (
        f'<img class="player-photo" src="{headshot}" alt="{name}">'
        if headshot
        else '<div class="player-photo player-fallback">No image</div>'
    )
    stat = ""
    if stat_label and stat_value:
        stat = f'<div class="player-stat"><span>{stat_label}</span><strong>{stat_value}</strong></div>'
    return f'''<div class="player-card"><div class="player-photo-wrap">{photo}</div>
    <div class="player-role">{role}</div><div class="player-name">{name}</div>{stat}</div>'''


def get_component_explanation(team_row):
    components = {
        "Starting rotation": float(team_row.get("rotation_component", 50)),
        "Bullpen": float(team_row.get("bullpen_component", 50)),
        "Offensive momentum": float(team_row.get("offense_component", 50)),
        "Run differential": float(team_row.get("run_diff_component", 50)),
        "Post All-Star form": float(team_row.get("post_asb_component", 50)),
        "Last 10 games": float(team_row.get("last_10_component", 50)),
        "Quality-adjusted results": float(team_row.get("quality_component", 50)),
        "Overall record": float(team_row.get("overall_record_component", 50)),
    }
    ordered = sorted(components.items(), key=lambda x: x[1], reverse=True)
    return ordered[:2], ordered[-2:]


def component_detail(label, t):
    if label == "Starting rotation":
        return f"{rank_text(t['projected_rotation_rank'])} MLB · score {t['projected_rotation_score']:.1f}"
    if label == "Bullpen":
        return f"{rank_text(t['bullpen_rank'])} MLB · score {t['neutral_bullpen_score']:.1f}"
    if label == "Offensive momentum":
        return (
            f"{rank_text(t['offensive_momentum_rank'])} MLB · "
            f"{t['offense_level']} · {t['offense_direction']}"
        )
    if label == "Run differential":
        return f"{run_diff_text(t['run_diff_per_game'])} runs/game"
    if label == "Post All-Star form":
        return f"{t['post_asb_win_pct']:.3f} win rate"
    if label == "Last 10 games":
        wins = round(t["last_10_win_pct"] * 10)
        return f"{wins}-{10-wins} in last 10"
    if label == "Quality-adjusted results":
        return f"{t['quality_weighted_win_pct']:.3f}"
    if label == "Overall record":
        return f"{safe_int(t['wins'])}-{safe_int(t['losses'])}"
    return ""




def icon_img(kind, size=22):
    icons = {
        "rotation": '<circle cx="12" cy="12" r="8.5" fill="none" stroke="#FFFFFF" stroke-width="1.8"/><path d="M8.2 5.6c2.4 1.3 3.5 3.1 3.5 5.5s-1.1 4.2-3.5 5.5M15.8 7.3c-2.1 1.1-3.1 2.6-3.1 4.7s1 3.6 3.1 4.7" fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>',
        "bullpen": '<path d="M6 18V8.5M18 18V8.5M4.5 18h15M7.5 8.5h9M9 8.5V6.2h6v2.3M9.2 18v-4.7h5.6V18" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
        "offense": '<path d="M5 17l4-5 3 2 6-8M16 6h3v3" fill="none" stroke="#FFFFFF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><circle cx="7" cy="17" r="1.5" fill="#FFFFFF"/>',
        "run_diff": '<path d="M5 6h14v12H5zM8 9h3M13 9h3M8 13h3M13 13h3" fill="none" stroke="#FFFFFF" stroke-width="1.7" stroke-linejoin="round"/>',
        "post_asb": '<rect x="5" y="6.5" width="14" height="12" rx="1.5" fill="none" stroke="#FFFFFF" stroke-width="1.7"/><path d="M8 4.5v4M16 4.5v4M5 10h14M9 13.5l2 2 4-4" fill="none" stroke="#FFFFFF" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
        "last10": '<path d="M5 17V8M10 17V11M15 17V6M20 17V9" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/><path d="M4 19h17" fill="none" stroke="#FFFFFF" stroke-width="1.5"/>',
        "quality": '<path d="M12 4.5l2.1 4.2 4.7.7-3.4 3.3.8 4.7-4.2-2.2-4.2 2.2.8-4.7-3.4-3.3 4.7-.7L12 4.5z" fill="none" stroke="#FFFFFF" stroke-width="1.7" stroke-linejoin="round"/>',
        "record": '<rect x="6" y="4.5" width="12" height="15" rx="1.5" fill="none" stroke="#FFFFFF" stroke-width="1.7"/><path d="M9 8h6M9 12h6M9 16h4" fill="none" stroke="#FFFFFF" stroke-width="1.7" stroke-linecap="round"/>',
        "up": '<path d="M6 16l5-5 3 3 4-5M14 9h4v4" fill="none" stroke="#FFFFFF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
        "down": '<path d="M6 8l5 5 3-3 4 5M14 15h4v-4" fill="none" stroke="#FFFFFF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
        "steady": '<path d="M5 12h14" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>',
        "score": '<path d="M5 17l4-5 3 2 6-8M16 6h2.5v2.5" fill="none" stroke="#FFFFFF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
    }

    body = icons.get(kind, icons["score"])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 24 24">'
        f'{body}</svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")

    return (
        f'<img class="ui-svg-icon" width="{size}" height="{size}" '
        f'src="data:image/svg+xml;base64,{encoded}" alt="">'
    )


MODEL_ICON_MAP = {
    "Starting Rotation": "rotation",
    "Bullpen": "bullpen",
    "Offensive Momentum": "offense",
    "Run Differential": "run_diff",
    "Post All-Star Performance": "post_asb",
    "Last 10 Games": "last10",
    "Quality-Adjusted Performance": "quality",
    "Overall Record": "record",
}

st.html(
    """
    <style>
    :root{--navy:#0a2944;--navy2:#123f63;--red:#c8102e;--page:#d9e9f5;--card:#edf6fc;--card2:#e5f1f9;--line:#8eb6d1;--line2:#6f9fbe;--text:#10263a;--muted:#49687f;--green:#176b46;--bad:#aa2734;}
    html,body,[class*="css"]{font-family:Arial,Helvetica,sans-serif}.stApp{background:var(--page);color:var(--text)}
    .block-container{max-width:1280px;padding:14px 24px 56px} header[data-testid="stHeader"]{background:transparent} #MainMenu,footer{visibility:hidden}
    .brand{background:var(--navy);color:#fff;border-bottom:5px solid var(--red);padding:20px 24px;margin-bottom:12px}.brand-row{display:flex;justify-content:space-between;gap:24px;align-items:end}.brand-title{font-size:46px;font-weight:900;letter-spacing:-1px;text-transform:uppercase}.brand-sub{font-size:15px;font-weight:700;color:#dce7f2}.brand-meta{text-align:right;font-size:12px;line-height:1.5;color:#dce7f2}
    div[role="radiogroup"]{background:var(--navy);border:1px solid #08223a;border-radius:0;padding:0;gap:0!important;box-shadow:0 2px 8px rgba(10,41,68,.16);overflow:hidden} div[role="radiogroup"] label{padding:10px 15px!important;margin:0!important;border-right:1px solid rgba(255,255,255,.16);min-height:42px;display:flex!important;align-items:center!important} div[role="radiogroup"] label p{font-size:13px!important;font-weight:800!important;color:#ffffff!important}
    .hero{background:var(--card);border:1px solid var(--line);border-top:6px solid var(--navy);padding:28px;box-shadow:0 4px 16px rgba(7,26,43,.07)}.eyebrow{color:var(--red);font-size:12px;font-weight:900;text-transform:uppercase}.hero h1{font-size:52px;line-height:1.04;margin:7px 0 0;color:var(--text)}.hero p{max-width:850px;font-size:17px;line-height:1.6;color:#2c506a}.note{display:inline-block;background:#e9f5fc;border-left:4px solid var(--red);padding:9px 12px;font-size:13px;font-weight:700;color:#18384f}
    .page-title{margin:34px 0 8px;font-size:30px;line-height:1.1;font-weight:900;color:var(--navy);letter-spacing:-.45px}.deck{max-width:920px;margin:0 0 24px;font-size:15px;line-height:1.62;color:#36566f}.section{margin:34px 0 12px;padding-bottom:9px;border-bottom:2px solid var(--navy);font-size:18px;font-weight:900;color:var(--navy)}
    .leader{background:var(--card);border:1px solid var(--line);border-top:5px solid var(--navy);padding:18px;height:100%}.leader-rank{color:var(--red);font-size:12px;font-weight:900}.leader-logo{width:78px;height:78px;object-fit:contain;margin:12px 0}.leader-team{font-size:20px;font-weight:900;line-height:1.15;color:var(--text);min-height:46px}.leader-record{font-size:13px;color:#47677f;font-weight:700}.leader-score{font-size:34px;font-weight:900;color:var(--text);margin-top:12px}.leader-label{font-size:11px;font-weight:800;color:#47677f;text-transform:uppercase}.leader-pitch{display:flex;justify-content:space-between;gap:8px;border-top:1px solid var(--line);padding-top:10px;margin-top:12px;font-size:12px;font-weight:800;color:#2c506a}
    .feature{background:var(--card);border:1px solid var(--line);padding:18px;height:100%}.feature h3{margin:0 0 6px;color:var(--text);font-size:18px}.feature p{margin:0;color:#466980;font-size:14px;line-height:1.5}
    .rank-head,.rank-row{display:grid;grid-template-columns:46px minmax(245px,1.7fr) 90px 82px 82px 82px 92px 92px;gap:10px;align-items:center}.rank-head{background:var(--navy);color:#fff;padding:11px 12px;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.2px;border:1px solid var(--navy);white-space:nowrap}.rank-row{background:var(--card);border-left:1px solid var(--line2);border-right:1px solid var(--line2);border-bottom:1px solid var(--line2);padding:11px 12px;min-height:70px}.rank-row:nth-of-type(even){background:#e8f3fa}.rank-row:hover{background:#dcecf7}.rank-head>div,.rank-row>div{min-width:0}.rank-num{font-size:19px;font-weight:900;color:var(--text)}.team-cell{display:flex;align-items:center;gap:12px;min-width:0}.rank-row .team-cell{min-width:0}.rank-logo{width:42px;height:42px;object-fit:contain}.team-name{font-size:15px;font-weight:900;color:var(--text)}.team-meta{font-size:11px;font-weight:700;color:#47677f}.rank-stat{font-size:13px;font-weight:800;color:#173c58}.rank-score{font-size:22px;font-weight:900;color:var(--text)}.movement-up{color:var(--green);font-weight:900}.movement-down{color:var(--bad);font-weight:900}.movement-neutral{color:#47677f;font-weight:900}
    .team-hero{display:grid;grid-template-columns:105px minmax(0,1fr) 170px;gap:22px;align-items:center;background:var(--card);border:1px solid var(--line2);border-top:6px solid var(--navy);padding:20px 22px;box-shadow:0 3px 10px rgba(10,41,68,.08)}.team-logo{width:105px;height:105px;object-fit:contain}.team-title{font-size:34px;font-weight:900;color:var(--text)}.team-sub{font-size:14px;font-weight:700;color:#47677f;margin-top:7px}.score-big{text-align:right;min-width:155px}.score-big .num{font-size:48px;font-weight:900;color:var(--text);line-height:.95}.score-big .lab{font-size:11px;font-weight:900;color:#47677f;text-transform:uppercase;margin-top:5px}
    .stat-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-top:14px}.stat-card{background:var(--card2);border:1px solid var(--line2);padding:12px;min-height:72px}.stat-value{font-size:22px;font-weight:900;color:var(--text)}.stat-label{font-size:11px;font-weight:800;color:#47677f;margin-top:4px}
    .why-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.why-card{background:var(--card);border:1px solid var(--line2);padding:18px}.why-card.good{border-top:5px solid var(--green)}.why-card.bad{border-top:5px solid var(--bad)}.why-title{font-size:16px;font-weight:900;color:var(--text);margin-bottom:9px}.why-item{padding:9px 0;border-top:1px solid var(--line)}.why-item:first-of-type{border-top:0}.why-label{font-size:14px;font-weight:900;color:var(--text)}.why-detail{font-size:12px;font-weight:700;color:#47677f;margin-top:2px}.bottom-line{background:var(--navy);color:#fff;padding:16px 18px;margin-top:14px;font-size:14px;line-height:1.55}
    .pitch-panel{background:var(--card);border:1px solid var(--line2);padding:0 16px 16px;margin:0 0 28px;box-shadow:0 2px 8px rgba(10,41,68,.06)}.pitch-head{display:flex;justify-content:space-between;align-items:center;gap:14px;margin:0 -16px 14px;padding:11px 14px;background:var(--navy);border-bottom:3px solid var(--red)}.pitch-title{color:#fff;font-size:18px;font-weight:900}.pitch-rank{color:#fff;font-size:13px;font-weight:900;background:var(--red);padding:6px 9px;white-space:nowrap}.player-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;align-items:stretch}.rotation-player-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.rotation-board{border-top:4px solid var(--red);margin-bottom:18px}.player-card{background:var(--card2);border:1px solid var(--line2);overflow:hidden;min-width:0;height:100%;display:flex;flex-direction:column}.player-photo-wrap{height:170px;background:#cfe4f2;overflow:hidden;border-bottom:1px solid var(--line2)}.player-photo{width:100%;height:100%;object-fit:contain;object-position:center bottom;display:block}.player-fallback{display:flex;align-items:center;justify-content:center;color:#76889a;font-size:12px;font-weight:700}.player-role{padding:8px 10px 0;color:var(--red);font-size:8px;font-weight:900;text-transform:uppercase;letter-spacing:.35px}.player-name{padding:3px 10px 10px;color:var(--navy);font-size:13px;line-height:1.2;font-weight:900;overflow-wrap:anywhere}.player-stat{border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:6px;padding:8px 11px 10px;font-size:11px;color:#47677f}.player-stat strong{color:var(--text)}.pitch-note{margin-top:12px;background:#e3f0f8;border-left:3px solid var(--navy);padding:9px 11px;color:#36566f;font-size:11px;line-height:1.5}
    .board-row{display:grid;grid-template-columns:42px minmax(220px,1.4fr) minmax(180px,1fr) 90px 90px;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);border-top:0;padding:10px 12px}.board-row:first-of-type{border-top:1px solid var(--line)}.player-inline{display:flex;align-items:center;gap:10px}.player-inline img{width:48px;height:48px;object-fit:contain;background:#d4eafa}
    .method{background:var(--card);border:1px solid var(--line);padding:18px;height:100%}.method h3{margin:0 0 10px;color:var(--text)}.method p{color:#385970;line-height:1.6;font-size:14px}.weight{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid var(--line);color:#1f4159;font-size:14px;font-weight:700}.weight strong{color:var(--red)}
    .stButton>button{width:100%;border-radius:0!important;border:0!important;background:var(--navy)!important;color:#fff!important;font-weight:900!important;padding:.65rem 1rem!important}.stButton>button:hover{background:var(--red)!important}.stSelectbox div[data-baseweb="select"]>div{background:#f8fcff!important;border:1px solid #6fa6c8!important;color:#10283d!important;border-radius:0!important;min-height:46px!important}
    @media(max-width:1100px){.stat-grid{grid-template-columns:repeat(3,1fr)}.player-grid{grid-template-columns:repeat(3,1fr)}.rotation-player-grid{grid-template-columns:repeat(2,1fr)}.rank-head,.rank-row{grid-template-columns:42px minmax(230px,1.6fr) 80px 72px 72px 88px 88px}.hide-mid{display:none}}
    @media(max-width:800px){.brand-row{display:block}.brand-meta{text-align:left;margin-top:10px}div[role="radiogroup"]{overflow-x:auto;flex-wrap:nowrap!important}.team-hero{grid-template-columns:85px 1fr}.team-logo{width:75px;height:75px}.score-big{grid-column:1/-1;text-align:left;border-top:1px solid var(--line);padding-top:12px}.stat-grid{grid-template-columns:repeat(2,1fr)}.why-grid{grid-template-columns:1fr}.player-grid{grid-template-columns:repeat(2,1fr)}.rotation-player-grid{grid-template-columns:repeat(2,1fr)}.rank-head,.rank-row{grid-template-columns:36px minmax(180px,1fr) 70px 70px 80px}.hide-mobile{display:none}}
    @media(max-width:520px){.block-container{padding-left:.55rem;padding-right:.55rem}.brand{padding:16px}.brand-title{font-size:30px}.hero{padding:20px}.hero h1{font-size:31px}.page-title{font-size:27px}.player-photo-wrap{height:150px}.rank-head,.rank-row{grid-template-columns:32px minmax(150px,1fr) 64px 72px}.hide-small{display:none}}
    
    @media (max-width:1100px){
        .rotation-player-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
        .player-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
        .player-photo-wrap{height:180px}
    }

    @media (max-width:760px){
        .pitching-panel-head,.pitch-head{align-items:flex-start;flex-direction:column}
        .pitching-panel-rank,.pitch-rank{align-self:flex-start}
        .pitch-summary,
        .rotation-player-grid,.player-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
        .player-photo-wrap{height:170px}
    }

    @media (max-width:480px){
        .rotation-player-grid,.player-grid{grid-template-columns:1fr}
        .player-photo-wrap{height:230px}
    }


.pitch-summary,
.pitching-summary{
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:10px;
    margin:0 0 14px;
}


.method-card{
    background:var(--card);
    border:1px solid var(--line2);
    padding:18px 20px;
    height:100%;
    box-shadow:0 2px 8px rgba(10,41,68,.05);
}
.method-card h3{
    margin:0 0 12px;
    font-size:18px;
    color:var(--navy);
}
.method-card p{
    margin:0 0 14px;
    color:#36566f;
    font-size:14px;
    line-height:1.62;
}
.method-card p:last-child{margin-bottom:0}
.compact-method{min-height:150px}
.weight-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    padding:9px 0;
    border-bottom:1px solid #b9d3e5;
    color:#274b65;
    font-size:13px;
    font-weight:700;
}
.weight-row strong{color:var(--navy);font-size:14px}
.weight-total{
    display:flex;
    justify-content:space-between;
    margin:10px -20px -18px;
    padding:11px 20px;
    background:#dcecf7;
    border-top:1px solid var(--line2);
    color:var(--navy);
    font-weight:900;
}


@media (max-width:1000px){
    .pitch-summary,.pitching-summary{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .rotation-player-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .player-grid{
        grid-template-columns:repeat(3,minmax(0,1fr));
    }
}

@media (max-width:700px){
    .block-container{padding-left:12px;padding-right:12px}
    .pitch-head{align-items:flex-start;flex-direction:column}
    .pitch-summary,.pitching-summary{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .rotation-player-grid,.player-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .player-photo-wrap{height:155px}
}

@media (max-width:430px){
    .pitch-summary,.pitching-summary{
        grid-template-columns:1fr 1fr;
    }
    .rotation-player-grid,.player-grid{
        grid-template-columns:1fr;
    }
    .player-photo-wrap{height:220px}
}


/* =========================================================
   RESPONSIVE TOP NAVIGATION
   ========================================================= */

div[role="radiogroup"]{
    display:flex !important;
    width:100%;
    background:var(--navy);
    border:1px solid #08223a;
    border-radius:0;
    padding:0;
    gap:0 !important;
    box-shadow:0 2px 8px rgba(10,41,68,.16);
    overflow:hidden;
}

div[role="radiogroup"] > label{
    flex:1 1 0;
    min-width:0;
    margin:0 !important;
    padding:10px 8px !important;
    border-right:1px solid rgba(255,255,255,.14);
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    gap:6px;
    white-space:nowrap;
}

div[role="radiogroup"] > label:last-child{
    border-right:0;
}

div[role="radiogroup"] > label p{
    margin:0 !important;
    font-size:12px !important;
    line-height:1 !important;
    font-weight:800 !important;
    color:#fff !important;
    white-space:nowrap !important;
    overflow:visible !important;
    word-break:normal !important;
}

div[role="radiogroup"] > label [data-testid="stMarkdownContainer"]{
    overflow:visible !important;
}

@media (max-width: 760px){
    div[role="radiogroup"]{
        display:grid !important;
        grid-template-columns:repeat(4,minmax(0,1fr));
        overflow:visible !important;
    }

    div[role="radiogroup"] > label{
        min-height:42px;
        padding:8px 6px !important;
        border-right:1px solid rgba(255,255,255,.14);
        border-bottom:1px solid rgba(255,255,255,.14);
    }

    div[role="radiogroup"] > label p{
        font-size:11px !important;
    }
}

@media (max-width: 520px){
    div[role="radiogroup"]{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }

    div[role="radiogroup"] > label{
        justify-content:flex-start !important;
        padding:9px 12px !important;
    }

    div[role="radiogroup"] > label p{
        font-size:12px !important;
    }
}


/* =========================================================
   DESKTOP NAVIGATION POLISH
   ========================================================= */

[data-testid="stRadio"]{
    width:100% !important;
}

[data-testid="stRadio"] > div{
    width:100% !important;
}

div[role="radiogroup"]{
    display:grid !important;
    grid-template-columns:repeat(8,minmax(0,1fr)) !important;
    width:100% !important;
    max-width:none !important;
    overflow:hidden !important;
}

div[role="radiogroup"] > label{
    width:100% !important;
    min-width:0 !important;
    min-height:46px;
    padding:10px 12px !important;
    justify-content:center !important;
    text-align:center;
}

div[role="radiogroup"] > label p{
    font-size:12px !important;
    white-space:nowrap !important;
    overflow:visible !important;
    text-overflow:clip !important;
}

/* Give the desktop layout a little more room */
@media (min-width: 1200px){
    .block-container{
        max-width:1400px;
        padding-left:28px;
        padding-right:28px;
    }

    .brand{
        padding:20px 24px 18px;
    }

    .hero{
        padding:28px 24px;
    }
}

/* Tablet */
@media (max-width: 760px){
    div[role="radiogroup"]{
        grid-template-columns:repeat(4,minmax(0,1fr)) !important;
    }

    div[role="radiogroup"] > label{
        min-height:44px;
        padding:9px 8px !important;
    }
}

/* Phone */
@media (max-width: 520px){
    div[role="radiogroup"]{
        grid-template-columns:repeat(2,minmax(0,1fr)) !important;
    }

    div[role="radiogroup"] > label{
        justify-content:flex-start !important;
        text-align:left;
        padding:10px 12px !important;
    }
}


/* FINAL NAV */
.os-nav{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));width:100%;margin:12px 0 0;background:var(--navy);border:1px solid #08223a;box-shadow:0 2px 7px rgba(10,41,68,.13)}
.os-nav a{min-height:48px;padding:0 10px;display:flex;align-items:center;justify-content:center;gap:7px;color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:800;border-right:1px solid rgba(255,255,255,.14);box-sizing:border-box}
.os-nav a:last-child{border-right:0}.os-nav a:hover{background:#173f61}.os-nav a.active{background:#244f72;box-shadow:inset 0 -4px 0 var(--red)}
.os-nav-dot{width:10px;height:10px;flex:0 0 10px;border-radius:50%;background:#fff}.os-nav a.active .os-nav-dot{background:#ff4d62}
@media(max-width:850px){.os-nav{grid-template-columns:repeat(4,minmax(0,1fr))}.os-nav a{border-bottom:1px solid rgba(255,255,255,.14)}}
@media(max-width:520px){.os-nav{grid-template-columns:repeat(2,minmax(0,1fr))}.os-nav a{justify-content:flex-start;padding:0 13px}}

/* LOGO CONTRAST */
.rank-logo,.leader-logo,.team-logo,.move-team-logo{background:#fff;border:1px solid #b3cadb;border-radius:7px;padding:5px;box-sizing:border-box}

/* MODEL */
.model-intro{max-width:940px;margin:0 0 24px;color:#36566f;font-size:15px;line-height:1.65}
.model-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:18px;align-items:stretch}
.model-panel{background:var(--card);border:1px solid var(--line2);box-shadow:0 2px 7px rgba(10,41,68,.05)}
.model-panel-head{min-height:48px;display:flex;align-items:center;gap:10px;padding:0 16px;background:var(--navy);color:#fff;border-bottom:3px solid var(--red);font-size:17px;font-weight:900}
.weight-list{padding:8px 16px 4px}.weight-item{display:grid;grid-template-columns:34px minmax(165px,1fr) minmax(120px,1.5fr) 48px;gap:10px;align-items:center;min-height:47px;border-bottom:1px solid #bfd4e3}
.weight-item:last-child{border-bottom:0}.weight-icon{width:28px;height:28px;display:flex;align-items:center;justify-content:center;color:#12538a;background:#d7e9f5;border-radius:50%}
.weight-name{color:#203f58;font-size:13px;font-weight:800}.weight-track{height:9px;border-radius:99px;background:#d6e5ef;overflow:hidden}.weight-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#0f4d80,#2477b5)}
.weight-pct{text-align:right;color:var(--navy);font-size:14px;font-weight:900}.model-total{display:flex;justify-content:space-between;padding:12px 16px;background:#d7e8f4;border-top:1px solid var(--line2);color:var(--navy);font-weight:900}
.meaning-list{padding:4px 18px 8px}.meaning-item{display:grid;grid-template-columns:42px 1fr;gap:12px;align-items:flex-start;padding:18px 0;border-bottom:1px solid #bfd4e3}.meaning-item:last-child{border-bottom:0}
.meaning-icon{width:38px;height:38px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#12538a;color:#fff}.meaning-copy{color:#294b64;font-size:14px;line-height:1.58}
.model-detail-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:16px}.model-detail{background:var(--card);border:1px solid var(--line2);padding:17px;min-height:170px}
.model-detail-title{display:flex;align-items:center;gap:10px;color:var(--navy);font-size:16px;font-weight:900;margin-bottom:10px}.model-detail-icon{width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:#fff;background:var(--navy)}
.model-detail p{margin:0;color:#36566f;font-size:13px;line-height:1.62}


/* OFFENSE */
.offense-board{background:var(--card);border:1px solid var(--line2);padding:16px}
.offense-row{display:grid;grid-template-columns:42px minmax(190px,1.5fr) 96px 72px 95px 95px;gap:10px;align-items:center;min-height:58px;border-top:1px solid #c6d9e7}
.offense-row:first-of-type{border-top:0}
.offense-badge{display:inline-flex;align-items:center;justify-content:center;padding:5px 8px;border-radius:999px;font-size:10px;font-weight:900}
.offense-hot{background:#dfeee6;color:#1d694a}
.offense-strong{background:#e4eef8;color:#245b86}
.offense-average{background:#edf1f4;color:#596b79}
.offense-cold{background:#f3e6e8;color:#a43b48}
@media(max-width:850px){.offense-row{grid-template-columns:36px minmax(145px,1fr) 82px 64px}.offense-hide{display:none}}
@media(max-width:520px){.offense-row{grid-template-columns:34px minmax(120px,1fr) 70px}.offense-hide-small{display:none}.offense-row>div:nth-child(4){display:none}}

/* MOVEMENT */
.movement-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:14px 0 18px}.move-card{background:var(--card);border:1px solid var(--line2);padding:14px;min-height:108px}
.move-card-icon{width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:#fff;background:var(--navy)}.move-card-label{margin-top:12px;color:#5b7386;font-size:10px;font-weight:900;text-transform:uppercase}
.move-card-value{margin-top:3px;color:var(--navy);font-size:18px;line-height:1.2;font-weight:900}.move-card-sub{margin-top:4px;color:#5a7285;font-size:11px}
.move-chart{background:var(--card);border:1px solid var(--line2);padding:16px}.move-chart-title{color:var(--navy);font-size:17px;font-weight:900}.move-chart-note{color:#60788b;font-size:11px;margin-bottom:10px}
.move-row{display:grid;grid-template-columns:42px minmax(180px,1.3fr) 72px minmax(120px,1fr) 72px;gap:10px;align-items:center;min-height:50px;border-top:1px solid #c6d9e7}.move-row:first-of-type{border-top:0}
.move-team{display:flex;align-items:center;gap:9px;min-width:0}.move-team-logo{width:34px;height:34px;object-fit:contain}.move-team-name{color:#29485f;font-size:12px;font-weight:800}.move-rank{color:var(--navy);font-size:13px;font-weight:900}
.delta-pill{display:inline-flex;align-items:center;justify-content:center;min-width:42px;padding:5px 7px;border-radius:999px;font-size:11px;font-weight:900}.delta-up{background:#d8efe4;color:#14663e}.delta-down{background:#f6dfe3;color:#a02436}.delta-flat{background:#e3edf4;color:#526d80}
.score-bar{height:8px;background:#d7e4ed;border-radius:99px;overflow:hidden}.score-bar-fill{height:100%;border-radius:99px;background:#1c669b}.no-movement{padding:13px 15px;margin:0 0 16px;background:#e6f1f8;border-left:4px solid var(--navy);color:#36566f;font-size:13px;line-height:1.55}
@media(max-width:850px){.model-grid{grid-template-columns:1fr}.model-detail-grid{grid-template-columns:1fr}.movement-summary{grid-template-columns:repeat(2,minmax(0,1fr))}.move-row{grid-template-columns:36px minmax(145px,1fr) 60px 70px}.move-score-col{display:none}}
@media(max-width:520px){.weight-item{grid-template-columns:32px minmax(130px,1fr) 48px}.weight-track{display:none}.movement-summary{grid-template-columns:1fr}.move-row{grid-template-columns:34px minmax(120px,1fr) 54px 64px}}


/* =========================================================
   OCTOBER SHIFT — BROADCAST / MLB RESEARCH VISUAL SYSTEM
   ========================================================= */

/* Web fonts */
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

:root{
    --navy:#102F4F;
    --navy2:#1B456A;
    --blue:#245B86;
    --blue2:#3978A7;
    --red:#C8102E;
    --page:#F3F7FA;
    --card:#FBFDFE;
    --card2:#F7FAFC;
    --line:#B8CBD9;
    --line2:#9DB8CA;
    --text:#172B3A;
    --muted:#536B7C;
    --green:#237A57;
    --bad:#B63A46;
}

/* Base */
html,body,[class*="css"]{
    font-family:'Inter',Arial,sans-serif !important;
}

.stApp{
    background:
        linear-gradient(180deg,#EDF4F8 0%,#F5F8FA 240px,#F3F7FA 100%) !important;
    color:var(--text) !important;
}

/* Content width / rhythm */
.block-container{
    max-width:1360px !important;
    padding-top:16px !important;
    padding-bottom:56px !important;
}

/* Brand */
.brand{
    background:linear-gradient(100deg,#0D2944 0%,#153E61 100%) !important;
    border-bottom:4px solid var(--red) !important;
    box-shadow:0 8px 24px rgba(16,47,79,.10);
}

.brand-title{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    font-size:54px !important;
    line-height:.92 !important;
    letter-spacing:.4px !important;
    font-weight:800 !important;
    color:#fff !important;
}

.brand-sub{
    font-family:'Inter',Arial,sans-serif !important;
    font-size:13px !important;
    letter-spacing:.2px;
    color:#DCE7EF !important;
}

.brand-meta{
    color:#D6E2EB !important;
}

/* Navigation */
.os-nav{
    background:#102F4F !important;
    border-color:#0B2742 !important;
    box-shadow:0 5px 14px rgba(16,47,79,.12) !important;
}

.os-nav a{
    font-family:'Inter',Arial,sans-serif !important;
    font-size:12px !important;
    font-weight:700 !important;
    color:#F7FAFC !important;
    letter-spacing:.05px;
}

.os-nav a:hover{
    background:#1C496F !important;
}

.os-nav a.active{
    background:#245B86 !important;
    box-shadow:inset 0 -4px 0 var(--red) !important;
}

/* Display typography */
.hero h1,
.page-title,
.section,
.section-title,
.pitch-title,
.model-panel-head,
.move-chart-title{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    letter-spacing:.1px !important;
}

.hero h1{
    font-size:58px !important;
    font-weight:800 !important;
    line-height:.98 !important;
    color:var(--navy) !important;
    max-width:980px;
}

.page-title{
    font-size:38px !important;
    font-weight:800 !important;
    color:var(--navy) !important;
    margin-top:34px !important;
}

.section,
.section-title{
    font-size:24px !important;
    font-weight:800 !important;
    color:var(--navy) !important;
    border-bottom:2px solid #8FAFC4 !important;
}

.eyebrow{
    color:var(--red) !important;
    font-size:11px !important;
    letter-spacing:.75px !important;
}

/* Cards */
.hero,
.leader,
.feature,
.rank-row,
.team-hero,
.stat-card,
.why-card,
.pitch-panel,
.player-card,
.method-card,
.model-panel,
.model-detail,
.move-card,
.move-chart{
    background:var(--card) !important;
    border-color:var(--line) !important;
}

.hero,
.team-hero,
.pitch-panel,
.model-panel,
.move-chart{
    box-shadow:0 6px 18px rgba(16,47,79,.055) !important;
}

.hero{
    border-top:5px solid var(--navy) !important;
}

/* Card typography */
.leader-team,
.team-title,
.rank-score,
.stat-value,
.move-card-value{
    color:var(--navy) !important;
}

.team-title{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    font-size:40px !important;
    font-weight:800 !important;
}

.leader-team{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    font-size:24px !important;
    font-weight:700 !important;
}

.leader-score{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    font-size:40px !important;
    color:var(--navy) !important;
}

/* Rankings */
.rank-head{
    background:linear-gradient(90deg,#102F4F,#173D5F) !important;
    color:#fff !important;
    font-family:'Inter',Arial,sans-serif !important;
    letter-spacing:.35px !important;
}

.rank-row:nth-of-type(even){
    background:#F5F9FC !important;
}

.rank-row:hover{
    background:#ECF4F9 !important;
}

.team-name{
    color:var(--navy) !important;
}

.team-meta,
.rank-stat,
.player-stat,
.deck,
.hero p,
.model-intro,
.meaning-copy,
.model-detail p,
.pitch-note,
.move-card-sub{
    color:var(--muted) !important;
}

/* Pitching panels */
.pitch-head{
    background:linear-gradient(90deg,#102F4F,#173D5F) !important;
    border-bottom:3px solid var(--red) !important;
}

.pitch-title{
    font-size:23px !important;
    font-weight:800 !important;
}

.pitch-rank{
    background:var(--red) !important;
    color:#fff !important;
}

.stat-card{
    background:#F7FAFC !important;
}

.player-card{
    background:#F8FBFD !important;
}

.player-photo-wrap{
    background:#E4EEF4 !important;
}

.player-role{
    color:var(--red) !important;
}

.player-name{
    color:var(--navy) !important;
}

/* Why-this-rank */
.why-card.good{
    border-top-color:var(--green) !important;
}

.why-card.bad{
    border-top-color:var(--bad) !important;
}

.bottom-line{
    background:#163C5C !important;
}

/* Model page */
.model-panel-head{
    background:linear-gradient(90deg,#102F4F,#173D5F) !important;
    border-bottom:3px solid var(--red) !important;
    font-size:22px !important;
    font-weight:800 !important;
}

.weight-icon{
    background:#E1EDF5 !important;
    color:#245B86 !important;
}

.weight-track{
    background:#DDE8EF !important;
}

.weight-fill{
    background:linear-gradient(90deg,#245B86,#5C91B5) !important;
}

.weight-name,
.weight-pct{
    color:var(--navy) !important;
}

.model-total{
    background:#E8F1F6 !important;
}

.meaning-icon,
.model-detail-icon,
.move-card-icon{
    background:#245B86 !important;
}

/* Movement */
.delta-up{
    background:#DDEFE7 !important;
    color:#1D694A !important;
}

.delta-down{
    background:#F3E1E4 !important;
    color:#A43B48 !important;
}

.delta-flat{
    background:#E8EFF4 !important;
    color:#567083 !important;
}

.score-bar{
    background:#DCE7EE !important;
}

.score-bar-fill{
    background:linear-gradient(90deg,#245B86,#5B8EAF) !important;
}

/* Logo badges */
.rank-logo,
.leader-logo,
.team-logo,
.move-team-logo{
    background:#fff !important;
    border-color:#B8CBD9 !important;
}

/* Buttons */
.stButton>button{
    background:#102F4F !important;
    border:1px solid #102F4F !important;
    border-radius:4px !important;
    font-family:'Inter',Arial,sans-serif !important;
}

.stButton>button:hover{
    background:#245B86 !important;
    border-color:#245B86 !important;
}

/* Mobile type scaling */
@media(max-width:700px){
    .brand-title{font-size:40px !important}
    .hero h1{font-size:40px !important}
    .page-title{font-size:32px !important}
    .section,.section-title{font-size:21px !important}
}

@media(max-width:430px){
    .brand-title{font-size:34px !important}
    .hero h1{font-size:34px !important}
}


/* =========================================================
   OCTOBER SHIFT — WARM BASEBALL EDITORIAL THEME
   ========================================================= */

@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

:root{
    --ink:#1E252B;
    --charcoal:#252B31;
    --charcoal2:#313941;
    --red:#D71920;
    --blue:#2E628F;
    --blue2:#4C7FA8;
    --page:#F5F3EE;
    --card:#FFFFFF;
    --card2:#FAF9F6;
    --line:#D5D0C6;
    --line2:#C8C1B6;
    --text:#1F2A32;
    --muted:#68727A;
    --green:#23845D;
    --bad:#C43D4B;
}

html,body,[class*="css"]{
    font-family:'Inter',Arial,sans-serif !important;
}

.stApp{
    background:
        linear-gradient(180deg,#F1EEE8 0%,#F7F5F0 280px,#F5F3EE 100%) !important;
    color:var(--text) !important;
}

.block-container{
    max-width:1360px !important;
    padding-top:16px !important;
    padding-bottom:56px !important;
}

/* Brand */
.brand{
    background:linear-gradient(100deg,#20252B 0%,#2B3137 100%) !important;
    border-bottom:4px solid var(--red) !important;
    box-shadow:0 8px 22px rgba(31,37,43,.10) !important;
}

.brand-title{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
    font-size:56px !important;
    line-height:.92 !important;
    letter-spacing:.4px !important;
    font-weight:800 !important;
    color:#FFFFFF !important;
}

/* split title color via CSS trick */
.brand-title::first-line{
    color:#FFFFFF;
}

.brand-sub,
.brand-meta{
    color:#E7E2DA !important;
}

/* Nav */
.os-nav{
    background:#252B31 !important;
    border-color:#1C2126 !important;
    box-shadow:0 5px 14px rgba(31,37,43,.12) !important;
}

.os-nav a{
    color:#FFFFFF !important;
}

.os-nav a:hover{
    background:#353D45 !important;
}

.os-nav a.active{
    background:#3A424B !important;
    box-shadow:inset 0 -4px 0 var(--red) !important;
}

/* Typography */
.hero h1,
.page-title,
.section,
.section-title,
.pitch-title,
.model-panel-head,
.move-chart-title,
.team-title,
.leader-team,
.leader-score{
    font-family:'Barlow Condensed',Arial Narrow,sans-serif !important;
}

.hero h1{
    color:var(--ink) !important;
    font-size:58px !important;
    line-height:.98 !important;
    font-weight:800 !important;
}

.page-title{
    color:var(--ink) !important;
    font-size:40px !important;
    font-weight:800 !important;
}

.section,
.section-title{
    color:var(--ink) !important;
    border-bottom:2px solid #BDB6AA !important;
    font-size:25px !important;
    font-weight:800 !important;
}

.eyebrow{
    color:var(--red) !important;
}

/* Cards */
.hero,
.leader,
.feature,
.rank-row,
.team-hero,
.stat-card,
.why-card,
.pitch-panel,
.player-card,
.method-card,
.model-panel,
.model-detail,
.move-card,
.move-chart{
    background:var(--card) !important;
    border-color:var(--line) !important;
}

.hero,
.team-hero,
.pitch-panel,
.model-panel,
.move-chart{
    box-shadow:0 5px 15px rgba(31,37,43,.055) !important;
}

.hero{
    border-top:5px solid var(--charcoal) !important;
}

.note{
    background:#F6EFE9 !important;
    border-left-color:var(--red) !important;
    color:#4E5358 !important;
}

/* Rankings */
.rank-head{
    background:#252B31 !important;
    color:#FFFFFF !important;
}

.rank-row:nth-of-type(even){
    background:#FAF9F6 !important;
}

.rank-row:hover{
    background:#F1EEE8 !important;
}

.team-name,
.rank-score,
.stat-value,
.team-title,
.leader-team,
.leader-score{
    color:var(--ink) !important;
}

.team-meta,
.rank-stat,
.deck,
.hero p,
.model-intro,
.meaning-copy,
.model-detail p,
.pitch-note,
.move-card-sub,
.player-stat{
    color:var(--muted) !important;
}

/* Pitching */
.pitch-head{
    background:#252B31 !important;
    border-bottom:3px solid var(--red) !important;
}

.pitch-title{
    color:#FFFFFF !important;
}

.pitch-rank{
    background:var(--red) !important;
    color:#FFFFFF !important;
}

.stat-card{
    background:#FBFAF7 !important;
}

.player-card{
    background:#FCFBF8 !important;
}

.player-photo-wrap{
    background:#EEEAE3 !important;
}

.player-role{
    color:var(--red) !important;
}

.player-name{
    color:var(--ink) !important;
}

/* Logos */
.rank-logo,
.leader-logo,
.team-logo,
.move-team-logo{
    background:#FFFFFF !important;
    border-color:#D7D1C7 !important;
}

/* Model */
.model-panel-head{
    background:#252B31 !important;
    border-bottom:3px solid var(--red) !important;
    color:#FFFFFF !important;
}

.weight-icon,
.meaning-icon,
.model-detail-icon,
.move-card-icon{
    background:#2E628F !important;
    color:#FFFFFF !important;
}

.weight-track{
    background:#E5E0D7 !important;
}

.weight-fill{
    background:linear-gradient(90deg,#2E628F,#5C8AAE) !important;
}

.weight-name,
.weight-pct{
    color:var(--ink) !important;
}

.model-total{
    background:#F0ECE5 !important;
    color:var(--ink) !important;
}

/* Make the data-URI SVG icons visible */
.ui-svg-icon{
    display:block !important;
    width:20px !important;
    height:20px !important;
    object-fit:contain !important;
}

/* Movement */
.move-card-icon.riser,
.move-card-icon.positive{
    background:var(--green) !important;
}

.move-card-icon.faller,
.move-card-icon.negative{
    background:var(--bad) !important;
}

.delta-up{
    background:#E0EFE8 !important;
    color:#1E6F4D !important;
}

.delta-down{
    background:#F4E1E4 !important;
    color:#A93B48 !important;
}

.delta-flat{
    background:#ECE9E3 !important;
    color:#666F76 !important;
}

.score-bar{
    background:#E6E1D8 !important;
}

.score-bar-fill{
    background:linear-gradient(90deg,#2E628F,#6B97B8) !important;
}

/* cleaner card edges */
.feature,
.model-detail,
.move-card{
    border-radius:4px !important;
}

@media(max-width:700px){
    .brand-title{font-size:40px !important}
    .hero h1{font-size:40px !important}
    .page-title{font-size:33px !important}
}


.brand-october{color:#FFFFFF}
.brand-shift{color:#E53935}


/* =========================================================
   OCTOBER SHIFT — MLB LIGHT BLUE / RED / WHITE
   Final visual override
   ========================================================= */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Roboto+Condensed:wght@500;600;700;800&display=swap');

:root{
    --page:#EAF3F9;
    --page-deep:#DDECF6;
    --card:#FFFFFF;
    --card-soft:#F6FAFD;
    --navy:#102A43;
    --navy-2:#163A5C;
    --blue:#2F6B9A;
    --blue-soft:#DCECF7;
    --red:#D71920;
    --red-dark:#B9141A;
    --text:#152536;
    --muted:#60758A;
    --line:#BDD3E3;
    --line-soft:#D9E7F0;
    --green:#21865F;
    --negative:#C83E4D;
}

/* BODY + FONT SYSTEM */
html,
body,
[class*="css"],
.stApp{
    font-family:'Inter',Arial,sans-serif !important;
}

.stApp{
    background:
        linear-gradient(180deg,#E3F0F8 0px,#EAF3F9 260px,#EDF5FA 100%) !important;
    color:var(--text) !important;
}

.block-container{
    max-width:1360px !important;
    padding-top:16px !important;
    padding-bottom:60px !important;
}

/* DISPLAY TYPE */
.brand-title,
.hero h1,
.page-title,
.section,
.section-title,
.pitch-title,
.model-panel-head,
.move-chart-title,
.team-title,
.leader-team,
.leader-score,
.stat-value,
.rank-score,
.player-name,
.weight-pct,
.model-total{
    font-family:'Roboto Condensed','Arial Narrow',Arial,sans-serif !important;
}

/* BRAND */
.brand{
    background:linear-gradient(105deg,#102A43 0%,#163A5C 100%) !important;
    border:1px solid #163A5C !important;
    border-bottom:4px solid var(--red) !important;
    box-shadow:0 7px 20px rgba(16,42,67,.13) !important;
}

.brand-title{
    font-size:55px !important;
    line-height:.94 !important;
    font-weight:800 !important;
    letter-spacing:.2px !important;
}

.brand-october{
    color:#FFFFFF !important;
}

.brand-shift{
    color:#FF4450 !important;
}

.brand-sub,
.brand-meta{
    color:#EEF7FC !important;
}

/* NAV */
.os-nav{
    background:#102A43 !important;
    border:1px solid #0C2237 !important;
    box-shadow:0 4px 12px rgba(16,42,67,.13) !important;
}

.os-nav a{
    color:#FFFFFF !important;
    font-family:'Inter',Arial,sans-serif !important;
    font-weight:700 !important;
}

.os-nav a:hover{
    background:#1D4B70 !important;
}

.os-nav a.active{
    background:#2F6B9A !important;
    box-shadow:inset 0 -4px 0 var(--red) !important;
}

/* PAGE HEADINGS */
.hero h1{
    color:var(--navy) !important;
    font-size:57px !important;
    line-height:1 !important;
    font-weight:800 !important;
}

.page-title{
    color:var(--navy) !important;
    font-size:40px !important;
    font-weight:800 !important;
}

.section,
.section-title{
    color:var(--navy) !important;
    border-bottom:2px solid var(--navy) !important;
    font-size:25px !important;
    font-weight:800 !important;
}

.eyebrow{
    color:var(--red) !important;
    font-weight:800 !important;
}

/* GENERAL CARDS */
.hero,
.leader,
.feature,
.rank-row,
.team-hero,
.stat-card,
.why-card,
.pitch-panel,
.player-card,
.method-card,
.model-panel,
.model-detail,
.move-card,
.move-chart{
    background:#FFFFFF !important;
    border-color:var(--line) !important;
}

.hero,
.team-hero,
.pitch-panel,
.model-panel,
.move-chart{
    box-shadow:0 5px 15px rgba(16,42,67,.06) !important;
}

.hero{
    border-top:5px solid var(--navy) !important;
}

.note{
    background:#F7FBFE !important;
    border-left:4px solid var(--red) !important;
    color:#304B63 !important;
}

/* RANKINGS */
.rank-head{
    background:#102A43 !important;
    color:#FFFFFF !important;
}

.rank-row:nth-of-type(even){
    background:#F7FBFE !important;
}

.rank-row:hover{
    background:#E8F3FA !important;
}

.team-name,
.rank-score,
.stat-value,
.team-title,
.leader-team,
.leader-score{
    color:var(--navy) !important;
}

.team-meta,
.rank-stat,
.deck,
.hero p,
.model-intro,
.meaning-copy,
.model-detail p,
.pitch-note,
.move-card-sub,
.player-stat{
    color:var(--muted) !important;
}

/* PITCHING PANELS */
.pitch-head{
    background:#102A43 !important;
    border-bottom:3px solid var(--red) !important;
}

.pitch-title{
    color:#FFFFFF !important;
    font-weight:800 !important;
}

.pitch-rank{
    background:var(--red) !important;
    color:#FFFFFF !important;
}

.stat-card{
    background:#F8FCFF !important;
}

.player-card{
    background:#FFFFFF !important;
}

.player-photo-wrap{
    background:#DCECF7 !important;
}

.player-role{
    color:var(--red) !important;
    font-weight:800 !important;
}

.player-name{
    color:var(--navy) !important;
    font-weight:700 !important;
}

/* LOGOS */
.rank-logo,
.leader-logo,
.team-logo,
.move-team-logo{
    background:#FFFFFF !important;
    border-color:#C7DBE8 !important;
}

/* MODEL */
.model-panel-head{
    background:#102A43 !important;
    border-bottom:3px solid var(--red) !important;
    color:#FFFFFF !important;
    font-weight:800 !important;
}

.weight-icon,
.meaning-icon,
.model-detail-icon,
.move-card-icon{
    background:#2F6B9A !important;
    color:#FFFFFF !important;
    border:1px solid #275C86 !important;
}

.weight-track{
    background:#DCE8F0 !important;
}

.weight-fill{
    background:linear-gradient(90deg,#2F6B9A,#6D9ABD) !important;
}

.weight-name,
.weight-pct{
    color:var(--navy) !important;
}

.model-total{
    background:#E4F0F8 !important;
    color:var(--navy) !important;
}

/* MOVEMENT */
.move-card-icon.riser,
.move-card-icon.positive{
    background:var(--green) !important;
    border-color:#19734F !important;
}

.move-card-icon.faller,
.move-card-icon.negative{
    background:var(--negative) !important;
    border-color:#AE3340 !important;
}

.delta-up{
    background:#DDF2E8 !important;
    color:#176B4A !important;
}

.delta-down{
    background:#F7E0E4 !important;
    color:#A72F3D !important;
}

.delta-flat{
    background:#E7EFF5 !important;
    color:#5C7182 !important;
}

.score-bar{
    background:#DCE8F0 !important;
}

.score-bar-fill{
    background:linear-gradient(90deg,#2F6B9A,#78A4C3) !important;
}

/* SVG ICONS */
.ui-svg-icon{
    display:block !important;
    width:20px !important;
    height:20px !important;
    object-fit:contain !important;
}

/* BUTTONS / SELECTS */
div[data-baseweb="select"] > div{
    background:#FFFFFF !important;
    border-color:#B8D0E0 !important;
    color:var(--navy) !important;
}

.stButton > button{
    background:#FFFFFF !important;
    color:var(--navy) !important;
    border:1px solid #B8D0E0 !important;
    font-weight:700 !important;
}

.stButton > button:hover{
    border-color:var(--blue) !important;
    color:var(--blue) !important;
}

/* RESPONSIVE */
@media(max-width:700px){
    .brand-title{
        font-size:40px !important;
    }

    .hero h1{
        font-size:40px !important;
    }

    .page-title{
        font-size:33px !important;
    }
}


/* =========================================================
   FINAL FONT CLEANUP
   Keep the light blue / red / white design.
   ========================================================= */

html,
body,
[class*="css"],
.stApp,
p,
span,
div,
label,
button,
input,
select{
    font-family:"Segoe UI",Arial,sans-serif !important;
}

.brand-title,
.hero h1,
.page-title,
.section,
.section-title,
.pitch-title,
.team-title,
.leader-team,
.leader-score,
.rank-score,
.stat-value,
.model-panel-head,
.model-detail-title,
.move-chart-title,
.move-card-value,
.weight-pct{
    font-family:"Segoe UI",Arial,sans-serif !important;
}

.brand-title{
    font-size:46px !important;
    line-height:1 !important;
    letter-spacing:-1px !important;
    font-weight:800 !important;
}

.hero h1{
    font-size:48px !important;
    line-height:1.05 !important;
    letter-spacing:-1.1px !important;
    font-weight:750 !important;
}

.page-title{
    font-size:34px !important;
    line-height:1.08 !important;
    letter-spacing:-.6px !important;
    font-weight:750 !important;
}

.section,
.section-title{
    font-size:20px !important;
    letter-spacing:-.2px !important;
    font-weight:750 !important;
}

.model-panel-head{
    font-size:17px !important;
    letter-spacing:-.1px !important;
    font-weight:750 !important;
}

.team-title,
.leader-team,
.move-card-value{
    font-weight:750 !important;
}

.os-nav a{
    font-family:"Segoe UI",Arial,sans-serif !important;
    font-size:13px !important;
    font-weight:650 !important;
}

@media(max-width:700px){
    .brand-title{font-size:36px !important}
    .hero h1{font-size:36px !important}
    .page-title{font-size:29px !important}
}


/* MLB LOGO IN TOP BRAND */
.brand-left{display:flex;align-items:center;gap:18px;min-width:0}
.brand-mlb-logo{width:86px;height:52px;object-fit:contain;flex:0 0 auto;display:block}
@media(max-width:700px){.brand-left{gap:12px}.brand-mlb-logo{width:70px;height:44px}}
@media(max-width:430px){.brand-mlb-logo{width:60px;height:38px}}

</style>
    """)

st.html(
    f'''<div class="brand">
    <div class="brand-row">
        <div class="brand-left">
            <img class="brand-mlb-logo" src="{MLB_LOGO}" alt="MLB logo">
            <div>
                <div class="brand-title"><span class="brand-october">October</span> <span class="brand-shift">Shift</span></div>
                <div class="brand-sub">2026 MLB Postseason Contender Rankings</div>
            </div>
        </div>
        <div class="brand-meta">Through {latest_game_label}<br>{completed_games:,} completed games · 30 teams</div>
    </div>
    </div>''')

nav = ["Home", "Rankings", "Teams", "Rotations", "Bullpens", "Offense", "Movement", "Model"]

requested_page = st.query_params.get("page", "Home")
if isinstance(requested_page, list):
    requested_page = requested_page[0] if requested_page else "Home"

page = requested_page if requested_page in nav else "Home"

nav_html = "".join(
    f'<a class="{"active" if item == page else ""}" href="?page={item}">'
    f'<span class="os-nav-dot"></span><span>{item}</span></a>'
    for item in nav
)

st.html(f'<nav class="os-nav">{nav_html}</nav>')


def render_rankings(data):
    st.html(
        '''<div class="rank-head"><div>RK</div><div>TEAM</div><div>RECORD</div><div class="hide-mid">LAST 10</div>
        <div class="hide-mobile">ROT</div><div class="hide-mobile">BP</div><div class="hide-small">SHIFT</div><div>SCORE</div></div>''')
    for _, row in data.iterrows():
        move, move_class = movement_for_team(row["team"])
        l10w = round(row["last_10_win_pct"] * 10)
        st.html(
            f'''<div class="rank-row"><div class="rank-num">{safe_int(row['rank'])}</div>
            <div class="team-cell">{logo_html(row['team'],'rank-logo')}<div><div class="team-name">{row['team']}</div>
            <div class="team-meta">{row['league']} {row['division']}</div></div></div>
            <div class="rank-stat">{safe_int(row['wins'])}-{safe_int(row['losses'])}</div>
            <div class="rank-stat hide-mid">{l10w}-{10-l10w}</div>
            <div class="rank-stat hide-mobile">{rank_text(row['projected_rotation_rank'])}</div>
            <div class="rank-stat hide-mobile">{rank_text(row['bullpen_rank'])}</div>
            <div class="rank-stat hide-small movement-{move_class}">{move}</div>
            <div class="rank-score">{row['october_shift_score']:.1f}</div></div>''')


if page == "Home":
    st.html(
        '''<div class="hero"><div class="eyebrow">LIVE 2026 MODEL</div>
        <h1>Which MLB teams are built best for October?</h1>
        <p>October Shift ranks all 30 clubs using recent form, offensive momentum, run differential, opponent-adjusted results, starting rotation strength and bullpen performance.</p>
        <div class="note">The October Shift Score is a relative contender rating, not a World Series probability.</div></div>''')
    st.html('<div class="section">Top Contenders</div>')
    cols = st.columns(4)
    for col, (_, row) in zip(cols, board.head(4).iterrows()):
        with col:
            logo = team_logo(row["team"])
            pic = f'<img class="leader-logo" src="{logo}">' if logo else ""
            st.html(
                f'''<div class="leader"><div class="leader-rank">#{safe_int(row['rank'])} Overall</div>{pic}
                <div class="leader-team">{row['team']}</div><div class="leader-record">{safe_int(row['wins'])}-{safe_int(row['losses'])}</div>
                <div class="leader-score">{row['october_shift_score']:.1f}</div><div class="leader-label">October Shift Score</div>
                <div class="leader-pitch"><span>Rotation {rank_text(row['projected_rotation_rank'])}</span><span>Bullpen {rank_text(row['bullpen_rank'])}</span></div></div>''')
    st.html('<div class="section">Explore</div>')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.html('<div class="feature"><h3>Full Rankings</h3><p>Compare all 30 teams by score, record, recent form, offense, rotation and bullpen rank.</p></div>')
        if st.button("View Rankings", key="go_rank"):
            st.session_state.page = "Rankings"; st.rerun()
    with c2:
        st.html('<div class="feature"><h3>Team Breakdowns</h3><p>See why each team ranks where it does and which factors are helping or hurting.</p></div>')
        if st.button("Explore Teams", key="go_team"):
            st.session_state.page = "Teams"; st.rerun()
    with c3:
        st.html('<div class="feature"><h3>Pitching Rankings</h3><p>Compare projected postseason rotations and bullpens across MLB.</p></div>')
        if st.button("View Rotations", key="go_pitch"):
            st.session_state.page = "Rotations"; st.rerun()
    st.html('<div class="section">Top 10 Snapshot</div>')
    render_rankings(board.head(10))

elif page == "Rankings":
    st.html('<div class="page-title">MLB Contender Rankings</div>')
    st.html('<div class="deck">The full 30-team board. Rotation, bullpen and offensive momentum are tracked separately so you can see where each team is strong or vulnerable.</div>')
    league = st.radio("League", ["All MLB", "National League", "American League"], horizontal=True)
    view = board
    if league == "National League": view = board[board["league"] == "NL"]
    if league == "American League": view = board[board["league"] == "AL"]
    render_rankings(view)

elif page == "Teams":
    st.html('<div class="page-title">Team Breakdown</div>')
    st.html('<div class="deck">Choose any team to see exactly what is helping its October profile, what is holding it back, and how its pitching and offense compare with MLB.</div>')
    selected = st.selectbox("Choose a team", board["team"].tolist())
    t = board[board["team"] == selected].iloc[0]
    move, move_class = movement_for_team(selected)
    st.html(
        f'''<div class="team-hero"><div>{logo_html(selected,'team-logo')}</div><div><div class="team-title">{selected}</div>
        <div class="team-sub">#{safe_int(t['rank'])} overall · {safe_int(t['wins'])}-{safe_int(t['losses'])} · {t['league']} {t['division']} · <span class="movement-{move_class}">Movement {move}</span></div></div>
        <div class="score-big"><div class="num">{t['october_shift_score']:.1f}</div><div class="lab">October Shift Score</div></div></div>''')
    l10w = round(t["last_10_win_pct"] * 10)
    st.html(
        f'''<div class="stat-grid"><div class="stat-card"><div class="stat-value">{t['post_asb_win_pct']:.3f}</div><div class="stat-label">Post All-Star Win Rate</div></div>
        <div class="stat-card"><div class="stat-value">{l10w}-{10-l10w}</div><div class="stat-label">Last 10 Games</div></div>
        <div class="stat-card"><div class="stat-value">{run_diff_text(t['run_diff_per_game'])}</div><div class="stat-label">Run Differential / Game</div></div>
        <div class="stat-card"><div class="stat-value">{t['quality_weighted_win_pct']:.3f}</div><div class="stat-label">Quality-Adjusted Win Rate</div></div>
        <div class="stat-card"><div class="stat-value">{rank_text(t['projected_rotation_rank'])}</div><div class="stat-label">Starting Rotation Rank</div></div>
        <div class="stat-card"><div class="stat-value">{rank_text(t['bullpen_rank'])}</div><div class="stat-label">Bullpen Rank</div></div>
        <div class="stat-card"><div class="stat-value">{rank_text(t['offensive_momentum_rank'])}</div><div class="stat-label">Offensive Momentum Rank</div></div>
        <div class="stat-card"><div class="stat-value">{t['offensive_momentum_score']:.1f}</div><div class="stat-label">Offensive Momentum Score</div></div></div>''')
    strengths, drags = get_component_explanation(t)
    strengths_html = "".join([f'<div class="why-item"><div class="why-label">{x[0]}</div><div class="why-detail">{component_detail(x[0],t)}</div></div>' for x in strengths])
    drags_html = "".join([f'<div class="why-item"><div class="why-label">{x[0]}</div><div class="why-detail">{component_detail(x[0],t)}</div></div>' for x in drags])
    st.html('<div class="section">Why This Rank?</div>')
    st.html(
        f'''<div class="why-grid"><div class="why-card good"><div class="why-title">Biggest Strengths</div>{strengths_html}</div>
        <div class="why-card bad"><div class="why-title">Biggest Drags</div>{drags_html}</div></div>
        <div class="bottom-line"><strong>Bottom line:</strong> {selected} ranks #{safe_int(t['rank'])} because its strongest model signals are {strengths[0][0].lower()} and {strengths[1][0].lower()}, while {drags[0][0].lower()} and {drags[1][0].lower()} are currently pulling the score down.</div>''')
    st.html('<div class="section">Offensive Momentum</div>')
    st.html(
        f'''<div class="pitch-panel">
        <div class="pitch-head">
            <div class="pitch-title">Current Offensive Form</div>
            <div class="pitch-rank">{rank_text(t['offensive_momentum_rank'])} MLB</div>
        </div>
        <div class="pitch-summary">
            <div class="stat-card"><div class="stat-value">{t['offensive_momentum_score']:.1f}</div><div class="stat-label">Momentum Score</div></div>
            <div class="stat-card"><div class="stat-value">{t['offense_level']}</div><div class="stat-label">Current Level</div></div>
            <div class="stat-card"><div class="stat-value">{t['offense_direction']}</div><div class="stat-label">Direction</div></div>
            <div class="stat-card"><div class="stat-value">{t['last_15_offense_score']:.1f}</div><div class="stat-label">Last 15 Offense</div></div>
        </div>
        <div class="pitch-note">Offensive Momentum emphasizes how dangerous a lineup looks right now. It blends the last 15 games, the last 7 games and the change from the club's season baseline. It is 15% of the October Shift Score.</div>
        </div>''')
    rotation_names = [t.get("starter_1",""), t.get("starter_2",""), t.get("starter_3",""), t.get("starter_4","")]
    rotation_names = [str(x).strip() for x in rotation_names if pd.notna(x) and str(x).strip()]
    rotation_cards = [player_card(name, "Ace" if i == 0 else f"Starter {i+1}") for i, name in enumerate(rotation_names)]
    st.html('<div class="section">Projected Postseason Rotation</div>')
    st.html(
        f'''<div class="pitch-panel"><div class="pitch-head"><div class="pitch-title">Starting Rotation</div><div class="pitch-rank">{rank_text(t['projected_rotation_rank'])} MLB</div></div>
        <div class="pitch-summary"><div class="stat-card"><div class="stat-value">{t['projected_rotation_score']:.1f}</div><div class="stat-label">Rotation Score</div></div>
        <div class="stat-card"><div class="stat-value">{t['projected_top_3_score']:.1f}</div><div class="stat-label">Top 3 Score</div></div>
        <div class="stat-card"><div class="stat-value">{t['projected_top_4_score']:.1f}</div><div class="stat-label">Top 4 Score</div></div>
        <div class="stat-card"><div class="stat-value">{t['projected_depth_score']:.1f}</div><div class="stat-label">Depth Score</div></div></div>
        <div class="rotation-player-grid">{''.join(rotation_cards)}</div><div class="pitch-note">Rotation scoring blends run suppression and quality/deep-start performance, then looks at ace strength, top-three quality and four-man depth.</div></div>''')
    bp_row = bullpen[bullpen["team"] == selected]
    bp_names = [] if bp_row.empty else [x.strip() for x in str(bp_row.iloc[0]["projected_top_5"]).split("|") if x.strip()]
    bp_cards = []
    for i, name in enumerate(bp_names[:5]):
        rr = relievers[(relievers["pitcher_name"] == name) & (relievers["team"] == selected)]
        score = "" if rr.empty else f"{rr.iloc[0]['run_prevention_score']:.1f}"
        bp_cards.append(player_card(name, "Top Reliever" if i == 0 else f"Reliever {i+1}", "Run Prevention" if score else "", score))
    st.html('<div class="section">Bullpen</div>')
    st.html(
        f'''<div class="pitch-panel"><div class="pitch-head"><div class="pitch-title">Bullpen Unit</div><div class="pitch-rank">{rank_text(t['bullpen_rank'])} MLB</div></div>
        <div class="pitch-summary"><div class="stat-card"><div class="stat-value">{t['neutral_bullpen_score']:.1f}</div><div class="stat-label">Bullpen Score</div></div>
        <div class="stat-card"><div class="stat-value">{t['top_3_run_prevention']:.1f}</div><div class="stat-label">Top 3 Run Prevention</div></div>
        <div class="stat-card"><div class="stat-value">{t['top_5_run_prevention']:.1f}</div><div class="stat-label">Top 5 Run Prevention</div></div>
        <div class="stat-card"><div class="stat-value">{t['strand_rate']:.1%}</div><div class="stat-label">Inherited Runner Strand Rate</div></div></div>
        <div class="player-grid">{''.join(bp_cards)}</div><div class="pitch-note">Strand rate measures how often inherited runners are kept from scoring after a reliever enters. It is only one part of the bullpen score, alongside run prevention and depth.</div></div>''')

elif page == "Rotations":
    st.html('<div class="page-title">Starting Rotation Rankings</div>')
    st.html('<div class="deck">Projected four-man postseason rotations ranked by run suppression, quality starts, ace strength and depth. The pitchers shown are the four starters currently projected by the model.</div>')

    for _, row in rotations.sort_values("projected_rotation_rank").iterrows():
        names = [
            row.get("starter_1", ""),
            row.get("starter_2", ""),
            row.get("starter_3", ""),
            row.get("starter_4", ""),
        ]
        names = [
            str(name).strip()
            for name in names
            if pd.notna(name) and str(name).strip()
        ]

        cards = []
        for i, name in enumerate(names):
            role = "Ace" if i == 0 else f"Starter {i + 1}"
            cards.append(player_card(name, role))

        st.html(
            f"""<div class="pitch-panel rotation-board">
            <div class="pitch-head">
                <div class="team-cell">
                    {logo_html(row['team'], 'rank-logo')}
                    <div>
                        <div class="pitch-title">#{safe_int(row['projected_rotation_rank'])} {row['team']}</div>
                        <div class="team-meta">Projected postseason rotation</div>
                    </div>
                </div>
                <div class="pitch-rank">Rotation Score {row['projected_rotation_score']:.1f}</div>
            </div>

            <div class="pitch-summary">
                <div class="stat-card"><div class="stat-value">{row['projected_ace_score']:.1f}</div><div class="stat-label">Ace Score</div></div>
                <div class="stat-card"><div class="stat-value">{row['projected_top_3_score']:.1f}</div><div class="stat-label">Top 3 Score</div></div>
                <div class="stat-card"><div class="stat-value">{row['projected_top_4_score']:.1f}</div><div class="stat-label">Top 4 Score</div></div>
                <div class="stat-card"><div class="stat-value">{row['projected_depth_score']:.1f}</div><div class="stat-label">Depth Score</div></div>
            </div>

            <div class="rotation-player-grid">{''.join(cards)}</div>
            </div>""")

elif page == "Bullpens":
    st.html('<div class="page-title">Bullpen Rankings</div>')
    st.html('<div class="deck">Bullpen strength blends individual run prevention, top-three and top-five depth, plus inherited-runner performance.</div>')
    for _, row in bullpen.sort_values("bullpen_rank").iterrows():
        best = row["best_reliever"]
        headshot = pitcher_headshot_url(best)
        photo = f'<img src="{headshot}" alt="{best}">' if headshot else ""
        st.html(
            f'''<div class="board-row"><div class="rank-num">{safe_int(row['bullpen_rank'])}</div>
            <div class="team-cell">{logo_html(row['team'],'rank-logo')}<div><div class="team-name">{row['team']}</div><div class="team-meta">Strand rate {row['strand_rate']:.1%}</div></div></div>
            <div class="player-inline">{photo}<div class="rank-stat">{best}</div></div><div class="rank-stat">Top 5 {row['top_5_run_prevention']:.1f}</div><div class="rank-score">{row['neutral_bullpen_score']:.1f}</div></div>''')


elif page == "Offense":
    st.html('<div class="page-title">Offensive Momentum</div>')
    st.html(
        "<div class=\"deck\">This board is about how dangerous each lineup looks right now, not which offense has been best all season. "
        "The score emphasizes the last 15 games, checks the last 7 for a more immediate signal, and compares recent form with the team\'s season baseline.</div>"
    )

    offense_view = board.sort_values(
        ["offensive_momentum_rank", "team"]
    ).copy()

    hottest = offense_view.iloc[0]
    biggest_rebound = offense_view.sort_values("trend_raw", ascending=False).iloc[0]
    coldest = offense_view.iloc[-1]

    st.html(
        '<div class="movement-summary">'
        f'<div class="move-card"><div class="move-card-label">Hottest Offense</div><div class="move-card-value">{hottest["team"]}</div><div class="move-card-sub">#{safe_int(hottest["offensive_momentum_rank"])} · {hottest["offensive_momentum_score"]:.1f}</div></div>'
        f'<div class="move-card"><div class="move-card-label">Best Recent Trend</div><div class="move-card-value">{biggest_rebound["team"]}</div><div class="move-card-sub">{biggest_rebound["trend_raw"]:+.1f} vs season baseline</div></div>'
        f'<div class="move-card"><div class="move-card-label">Current Level</div><div class="move-card-value">{hottest["offense_level"]}</div><div class="move-card-sub">{hottest["offense_direction"]}</div></div>'
        f'<div class="move-card"><div class="move-card-label">Coldest Offense</div><div class="move-card-value">{coldest["team"]}</div><div class="move-card-sub">#{safe_int(coldest["offensive_momentum_rank"])} · {coldest["offensive_momentum_score"]:.1f}</div></div>'
        '</div>'
    )

    rows = []
    for _, row in offense_view.iterrows():
        logo = team_logo(row["team"])
        logo_tag = f'<img class="move-team-logo" src="{logo}" alt="{row["team"]}">' if logo else '<div class="move-team-logo"></div>'

        level = str(row["offense_level"])
        level_class = (
            "offense-hot" if level == "HOT"
            else "offense-strong" if level == "STRONG"
            else "offense-average" if level == "AVERAGE"
            else "offense-cold"
        )

        rows.append(
            f'<div class="offense-row">'
            f'<div class="move-rank">#{safe_int(row["offensive_momentum_rank"])}</div>'
            f'<div class="move-team">{logo_tag}<div><div class="move-team-name">{row["team"]}</div><div class="team-meta">{row["offense_direction"]}</div></div></div>'
            f'<div><span class="offense-badge {level_class}">{row["offense_level"]}</span></div>'
            f'<div class="move-rank">{row["offensive_momentum_score"]:.1f}</div>'
            f'<div class="rank-stat offense-hide">{row["last_15_offense_score"]:.1f} <span class="team-meta">L15</span></div>'
            f'<div class="rank-stat offense-hide offense-hide-small">{row["last_7_offense_score"]:.1f} <span class="team-meta">L7</span></div>'
            f'</div>'
        )

    st.html(
        '<div class="offense-board">'
        '<div class="move-chart-title">All 30 Offenses</div>'
        '<div class="move-chart-note">Momentum rank · current level · momentum score · last 15 · last 7</div>'
        + ''.join(rows) +
        '</div>'
    )

elif page == "Movement":
    st.html('<div class="page-title">Ranking Movement</div>')

    if history.empty:
        st.info("No ranking snapshots have been saved yet.")
    else:
        dates = history["snapshot_date"].dropna().drop_duplicates().sort_values()

        if len(dates) < 2:
            st.html('<div class="deck">The first snapshot is saved. Movement will become meaningful after another dated snapshot is added.</div>')
        else:
            previous_date = dates.iloc[-2]
            current_date = dates.iloc[-1]

            previous = history[history["snapshot_date"] == previous_date][["team","rank","october_shift_score"]].rename(
                columns={"rank":"previous_rank","october_shift_score":"previous_score"}
            )

            current = history[history["snapshot_date"] == current_date][["team","rank","october_shift_score"]].rename(
                columns={"rank":"current_rank","october_shift_score":"current_score"}
            )

            movement = current.merge(previous, on="team", how="left")
            movement["rank_change"] = movement["previous_rank"] - movement["current_rank"]
            movement["score_change"] = movement["current_score"] - movement["previous_score"]

            st.html(
                f'<div class="deck">Latest shift: <strong>{previous_date.strftime("%b %d")}</strong> '
                f'to <strong>{current_date.strftime("%b %d")}</strong>.</div>'
            )

            if (movement["rank_change"] == 0).all():
                st.html(
                    '<div class="no-movement"><strong>No teams changed rank between these two snapshots yet.</strong> '
                    'That is okay. This page will become more useful as more games are completed and more daily snapshots are saved.</div>'
                )

            riser = movement.sort_values(["rank_change","score_change"], ascending=[False,False]).iloc[0]
            faller = movement.sort_values(["rank_change","score_change"], ascending=[True,True]).iloc[0]
            score_gainer = movement.sort_values("score_change", ascending=False).iloc[0]
            stable = movement.assign(abs_score=movement["score_change"].abs()).sort_values(["rank_change","abs_score"], key=lambda s: s.abs() if s.name=="rank_change" else s).iloc[0]

            def move_text(row):
                change = int(row["rank_change"])
                if change > 0:
                    return f"Up {change}"
                if change < 0:
                    return f"Down {abs(change)}"
                return "No rank change"

            st.html(
                '<div class="movement-summary">'
                f'<div class="move-card"><div class="move-card-icon riser">{icon_img("up",20)}</div><div class="move-card-label">Biggest Riser</div><div class="move-card-value">{riser["team"]}</div><div class="move-card-sub">{move_text(riser)}</div></div>'
                f'<div class="move-card"><div class="move-card-icon faller">{icon_img("down",20)}</div><div class="move-card-label">Biggest Faller</div><div class="move-card-value">{faller["team"]}</div><div class="move-card-sub">{move_text(faller)}</div></div>'
                f'<div class="move-card"><div class="move-card-icon positive">{icon_img("score",20)}</div><div class="move-card-label">Largest Score Gain</div><div class="move-card-value">{score_gainer["team"]}</div><div class="move-card-sub">{score_gainer["score_change"]:+.2f} points</div></div>'
                f'<div class="move-card"><div class="move-card-icon">{icon_img("steady",20)}</div><div class="move-card-label">Most Stable</div><div class="move-card-value">{stable["team"]}</div><div class="move-card-sub">{stable["score_change"]:+.2f} points</div></div>'
                '</div>'
            )

            chart_data = movement.copy()
            chart_data["abs_rank_change"] = chart_data["rank_change"].abs()
            chart_data["abs_score_change"] = chart_data["score_change"].abs()
            chart_data = chart_data.sort_values(["abs_rank_change","abs_score_change","current_rank"], ascending=[False,False,True]).head(15)

            max_abs_score = max(float(chart_data["abs_score_change"].max()), 0.01)
            rows = []

            for _, row in chart_data.iterrows():
                logo = team_logo(row["team"])
                logo_tag = f'<img class="move-team-logo" src="{logo}" alt="{row["team"]}">' if logo else '<div class="move-team-logo"></div>'
                delta = int(row["rank_change"])

                if delta > 0:
                    badge = f'<span class="delta-pill delta-up">▲ {delta}</span>'
                elif delta < 0:
                    badge = f'<span class="delta-pill delta-down">▼ {abs(delta)}</span>'
                else:
                    badge = '<span class="delta-pill delta-flat">—</span>'

                width = min(100, max(4, abs(float(row["score_change"])) / max_abs_score * 100))

                rows.append(
                    f'<div class="move-row">'
                    f'<div class="move-rank">#{int(row["current_rank"])}</div>'
                    f'<div class="move-team">{logo_tag}<div class="move-team-name">{row["team"]}</div></div>'
                    f'<div>{badge}</div>'
                    f'<div class="move-score-col"><div class="score-bar"><div class="score-bar-fill" style="width:{width:.1f}%"></div></div></div>'
                    f'<div class="move-rank">{row["score_change"]:+.2f}</div>'
                    f'</div>'
                )

            st.html(
                '<div class="move-chart">'
                '<div class="move-chart-title">Latest Movement</div>'
                '<div class="move-chart-note">Rank change and October Shift score change</div>'
                + ''.join(rows) +
                '</div>'
            )

elif page == "Model":
    st.html('<div class="page-title">How October Shift Works</div>')

    st.html(
        '<div class="model-intro">'
        'I built October Shift to look at more than the standings. '
        'The question I wanted to answer was simple: which teams look strongest for October based on how they are playing now, '
        'how much they are outscoring opponents, whether the offense is heating up or cooling down, and what their starting rotation and bullpen look like?'
        '</div>'
    )

    weight_rows = []
    for label, weight in MODEL_WEIGHTS.items():
        icon_name = MODEL_ICON_MAP[label]
        bar_width = min(100, weight / 0.20 * 100)
        weight_rows.append(
            f'<div class="weight-item">'
            f'<div class="weight-icon">{icon_img(icon_name,18)}</div>'
            f'<div class="weight-name">{label}</div>'
            f'<div class="weight-track"><div class="weight-fill" style="width:{bar_width:.0f}%"></div></div>'
            f'<div class="weight-pct">{weight:.0%}</div>'
            f'</div>'
        )

    st.html(
        '<div class="model-grid">'
        '<div class="model-panel">'
        f'<div class="model-panel-head">{icon_img("score",21)}<span>What goes into the score</span></div>'
        f'<div class="weight-list">{"".join(weight_rows)}</div>'
        '<div class="model-total"><span>Total</span><span>100%</span></div>'
        '</div>'
        '<div class="model-panel">'
        f'<div class="model-panel-head">{icon_img("quality",21)}<span>What the score means</span></div>'
        '<div class="meaning-list">'
        f'<div class="meaning-item"><div class="meaning-icon">{icon_img("score",19)}</div><div class="meaning-copy">The October Shift Score is <strong>not</strong> a World Series probability. It is a way to compare all 30 teams using the same factors.</div></div>'
        f'<div class="meaning-item"><div class="meaning-icon">{icon_img("up",19)}</div><div class="meaning-copy">A higher score means a team is grading well in more of the areas I am looking at. It also makes it easier to see why teams with similar records can have different postseason profiles.</div></div>'
        f'<div class="meaning-item"><div class="meaning-icon">{icon_img("rotation",19)}</div><div class="meaning-copy">Starting rotation, bullpen and offensive momentum stay separate on purpose. A team can be excellent in one area and weaker in another.</div></div>'
        '</div></div></div>'
    )

    st.html(
        '<div class="model-detail-grid">'
        f'<div class="model-detail"><div class="model-detail-title"><div class="model-detail-icon">{icon_img("rotation",19)}</div><span>Starting Pitching</span></div><p>I look at run prevention and how often starters have worked deep enough to give their team a strong outing. From there, I build a projected four-man postseason rotation and score the ace, top three, top four and depth.</p></div>'
        f'<div class="model-detail"><div class="model-detail-title"><div class="model-detail-icon">{icon_img("bullpen",19)}</div><span>Bullpen</span></div><p>I use actual relief innings and runs allowed, then look at the strength of the best relievers as a group. I also track inherited runners because getting out of another pitcher\'s jam matters in a postseason bullpen. Smaller samples are pulled back toward league average.</p></div>'
        f'<div class="model-detail"><div class="model-detail-title"><div class="model-detail-icon">{icon_img("offense",19)}</div><span>Offensive Momentum</span></div><p>I score how dangerous the offense looks right now. The biggest piece is the last 15 games, with the last 7 adding a more immediate signal and the team\'s season baseline showing whether the lineup is heating up, cooling down or rebounding.</p></div>'
        f'<div class="model-detail"><div class="model-detail-title"><div class="model-detail-icon">{icon_img("record",19)}</div><span>What It Does Not Know</span></div><p>The model cannot know who will be healthy in October, how a team will set its playoff roster, or how a specific matchup will play out. It is meant to be a live snapshot of how teams look based on the 2026 data available right now.</p></div>'
        '</div>'
    )