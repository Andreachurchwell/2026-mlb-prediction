
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

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "games_2026.csv"
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

    games["date"] = pd.to_datetime(
        games["date"]
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

    return board, games


board, games = load_data()

latest_game_date = (
    games["date"]
    .max()
    .strftime("%b %d, %Y")
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

    .rank-row { display:grid; grid-template-columns:55px 60px minmax(220px,1.7fr) 105px 105px 105px 110px; gap:12px; align-items:center; padding:15px 14px; border-bottom:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.025); transition:.2s ease; }
    .rank-row:hover { background:rgba(68,244,255,.07); border-left:2px solid var(--cyan); }
    .rank-num { font-family:'Orbitron',sans-serif; font-size:18px; font-weight:700; color:#B9C9CD; }
    .rank-logo { display:block; width:46px; height:46px; object-fit:contain; padding:5px; background:#F7FAFB; border-radius:8px; }
    .rank-team { font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:700; color:#fff; }
    .rank-team-meta { margin-top:3px; font-family:'Orbitron',sans-serif; font-size:9px; font-weight:600; letter-spacing:1.2px; color:#A8B8BC; }
    .rank-stat { font-family:'Orbitron',sans-serif; font-size:11px; font-weight:600; color:#D0DCDF; }
    .rank-score { text-align:right; font-family:'Orbitron',sans-serif; font-size:20px; font-weight:800; color:var(--green); }

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
    .rotation-topline { display:flex; justify-content:space-between; gap:18px; align-items:end; margin-bottom:20px; }
    .rotation-title { font-family:'Orbitron',sans-serif; font-size:12px; font-weight:800; letter-spacing:2px; color:var(--green); }
    .rotation-summary { font-family:'Orbitron',sans-serif; font-size:10px; color:#D7E2E5; }
    .rotation-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
    .rotation-arm { padding:15px 13px; border:1px solid rgba(255,255,255,.12); background:#111D22; }
    .rotation-slot { font-family:'Orbitron',sans-serif; font-size:8px; letter-spacing:1.5px; color:var(--cyan); margin-bottom:7px; }
    .rotation-name { font-family:'Space Grotesk',sans-serif; font-size:15px; font-weight:700; color:#fff; line-height:1.25; }
    .rotation-score { margin-top:8px; font-family:'Orbitron',sans-serif; font-size:17px; font-weight:700; color:var(--green); }
    .rotation-note { margin-top:14px; font-family:'Space Grotesk',sans-serif; font-size:12px; line-height:1.6; color:#A7B8BD; }

    .tech-footer { margin-top:60px; padding-top:18px; border-top:1px solid rgba(255,255,255,.08); font-family:'Orbitron',sans-serif; font-size:8px; font-weight:600; letter-spacing:2px; color:#90A2A6; }

    @media (max-width:900px) {
        .hero { padding:28px 22px; }
        .rank-row { grid-template-columns:35px 50px 1fr 75px; }
        .rank-hide-mobile { display:none; }
        .score-grid { grid-template-columns:repeat(2,1fr); }
        .rotation-grid { grid-template-columns:repeat(2,1fr); }
        .rotation-topline { display:block; }
        .rotation-summary { margin-top:10px; line-height:1.7; }
        .intel-team { font-size:22px; }
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
            season strength and postseason rotation ceiling.

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

                    SYSTEM RANK //
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
                    #{int(team["rotation_rank"])}
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
    for name in str(team.get("top_4_starters", "")).split("|")
    if name.strip()
]

rotation_scores = [
    score.strip()
    for score in str(team.get("top_4_adjusted_scores", "")).split("|")
    if score.strip()
]

rotation_cards = []

for index in range(4):
    name = rotation_names[index] if index < len(rotation_names) else "Depth TBD"
    score = rotation_scores[index] if index < len(rotation_scores) else "—"
    slot = "ACE" if index == 0 else f"SP{index + 1}"

    rotation_cards.append(
        f"""
        <div class="rotation-arm">
            <div class="rotation-slot">{slot}</div>
            <div class="rotation-name">{name}</div>
            <div class="rotation-score">{score}</div>
        </div>
        """
    )

st.html(
    f"""
    <div class="rotation-panel">

        <div class="rotation-topline">
            <div>
                <div class="rotation-title">
                    POSTSEASON ROTATION // CEILING
                </div>
            </div>

            <div class="rotation-summary">
                MLB RANK // #{int(team["rotation_rank"])}
                &nbsp;&nbsp;
                SCORE // {team["postseason_rotation_score"]:.3f}
                &nbsp;&nbsp;
                TOP 3 // {team["top_3_score"]:.3f}
                &nbsp;&nbsp;
                TOP 4 // {team["top_4_score"]:.3f}
            </div>
        </div>

        <div class="rotation-grid">
            {''.join(rotation_cards)}
        </div>

        <div class="rotation-note">
            Rotation ceiling rewards teams that can stack multiple strong 2026 starters.
            It does not assume every pitcher shown will be healthy or available in October;
            availability can be tracked separately without erasing a pitcher's underlying 2026 performance.
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