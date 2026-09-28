# October Shift

**Which MLB teams are built best for October?**

October Shift is a personal 2026 MLB analytics project that ranks all 30 teams by the profiles they bring into the postseason. It combines regular-season performance, recent form, offensive momentum, projected rotation strength, bullpen performance, run differential, and quality-adjusted results in one relative contender rating.

The project began as a single-game prediction experiment. When more complicated pitching features did not consistently improve on a simpler team baseline, the project shifted toward a question the data could answer more honestly: how do the strengths and weaknesses of MLB teams compare entering October?

> **The October Shift Score is a relative contender rating, not a World Series probability.** A score of 80 does not mean an 80% championship chance, and a higher score does not guarantee advancement.

The finished 2026 regular-season baseline is frozen through **September 27, 2026**.

## Dashboard

The Streamlit dashboard is available at:

**https://october-shift.streamlit.app/**

Its pages are:

- **Home** — the actual 2026 postseason starting bracket, October Shift ranks and scores for the 12 playoff teams, and the editorial “What October Shift Saw” analysis
- **Regular Season Final** — the preserved end-of-regular-season Home experience, read directly from the frozen snapshot
- **Rankings** — the complete 30-team October Shift board
- **Teams** — individual team profiles with component results, rotation, bullpen, and offense details
- **Rotations** — projected four-man postseason rotations and pitcher-level detail
- **Bullpens** — team bullpen rankings and reliever detail
- **Offense** — offensive momentum rankings, recent production, and direction labels
- **Movement** — changes between saved ranking snapshots
- **Model** — a plain-language explanation of the components and weights

The interface includes team logos, pitcher headshots where available, and responsive layouts for desktop and smaller screens.

## How the Score Works

Each input is converted to a 0–100 score with MLB-wide min-max normalization. October Shift then applies the following fixed weights:

| Component | Weight |
|---|---:|
| Starting Rotation | 20% |
| Run Differential per Game | 20% |
| Offensive Momentum | 15% |
| Post-All-Star Performance | 15% |
| Last 10 Games | 10% |
| Overall Record | 10% |
| Bullpen | 5% |
| Quality-Adjusted Performance | 5% |
| **Total** | **100%** |

The mix intentionally balances full-season accomplishment with the more recent version of a team. Overall record and run differential provide a broad foundation; post-All-Star results, Last 10, and Offensive Momentum add recency; rotation and bullpen scores describe the pitching staff; and quality-adjusted performance adds opponent context.

The weights are hand-designed and were explored through sensitivity tests. They were not fitted or calibrated as championship probabilities.

### Starting rotation

October Shift projects a four-man rotation from qualifying regular-season starters. Pitcher selection blends adjusted run suppression with quality/deep-start performance, while reliability adjustments keep very small samples from taking over. The team score rewards ace quality, top-three strength, the full top four, and depth.

### Bullpen

The bullpen model uses qualifying relief appearances, reliability-adjusted run prevention, top-reliever quality, unit depth, and inherited-runner strand performance. The final team input blends the best reliever, top three, top five, and strand score.

### Offensive momentum

Offensive Momentum evaluates OPS, runs per game, isolated power, walk rate, and strikeout avoidance. It compares the season baseline with the last 15 and last 7 games, with the largest share placed on last-15 production.

### Team performance

- **Run differential** is measured per game.
- **Post-All-Star performance** uses games after July 14, 2026.
- **Last 10** uses each club’s final 10 completed games.
- **Overall record** represents full-season results.
- **Quality-adjusted performance** weights results by opponent pregame winning percentage and gives post-All-Star games more recency weight than earlier games.

## 2026 Final Snapshot

The final board produced a near tie at the top and several notable disagreements with postseason seeding:

- **Los Angeles Dodgers — OS #1, 87.63.** The model’s top projected rotation, #2 run differential, and 8–2 finish helped Los Angeles narrowly take first.
- **Milwaukee Brewers — OS #2, 87.50.** Milwaukee finished only **0.13 points** behind Los Angeles while ranking #1 in run differential, post-All-Star record, overall record, and quality-adjusted results, plus #3 in rotation and an 8–2 Last 10.
- **San Diego Padres — NL #4 seed, OS #3, 77.30.** San Diego stood out as a lower seed because of its #3 Offensive Momentum, #2 post-All-Star record, #6 bullpen, and 8–2 finish.
- **New York Yankees — AL #4 seed, OS #4, 73.30.** The Yankees were October Shift’s highest-rated AL postseason team, led by the #2 rotation, #4 run differential, and #7 bullpen.
- **Houston Astros — AL #3 seed, OS #13, 56.82.** Houston paired the #2 bullpen and #5 Offensive Momentum with the #21 rotation, a **-0.198** run differential per game, and a .500 record.
- **Philadelphia Phillies — NL #6 seed, OS #14, 53.83.** Philadelphia’s #5 rotation was offset in the full score by the #23 bullpen, #23 Offensive Momentum, and a 4–6 finish.

These differences are central to the project. Postseason seeds describe where teams finished within their leagues and divisions; October Shift compares all 30 statistical profiles on the same scale.

## Postseason Bracket

After the regular-season field was set, the Home page added the actual 2026 MLB postseason starting bracket. It shows:

- Actual American League and National League seeds
- Wild Card matchups
- The fixed advancement paths from each Wild Card series to the Division Series
- October Shift rank and score beside every postseason team
- Empty Championship Series and World Series positions until results are recorded

The bracket places the model’s view directly beside the real tournament structure. It does **not** select winners or predict which teams will advance.

## What October Shift Saw

The Home page also includes a short editorial analysis of the final field. Its main stories are:

- **Two #4 seeds jump the line:** San Diego ranks OS #3 and New York ranks OS #4 despite both entering as fourth seeds.
- **Same score, different formula:** Los Angeles and Milwaukee are separated by 0.13 points but reach the top through different combinations of strengths.
- **Houston’s contradictory profile:** an elite bullpen and strong recent offense coexist with a much weaker rotation ranking and negative run differential.
- **One elite unit is not enough:** Philadelphia’s #5 rotation cannot by itself overcome weaker bullpen, offense, and recent-form components in the combined score.

These are profile comparisons, not postseason winner predictions.

## Limitations

October Shift preserves what the regular-season model produced, including its blind spots.

- **Postseason pitching usage:** Rotation and bullpen components come from qualifying regular-season performance. Teams can shorten rotations, skip starters, alter bullpen roles, or deploy pitchers differently in October.
- **Offensive depth:** Offensive Momentum measures aggregate team production rather than player-level lineup depth. It does not model exact lineups, hitter-pitcher matchups, platoons, or situational and high-leverage hitting.
- **Roster and availability:** The frozen score does not know confirmed postseason rosters, injuries, availability, fatigue, return workloads, or late role changes.
- **Matchup context:** Opponent-specific matchups, probable starters, park effects, rest, travel, bracket difficulty, and betting markets are outside the model.
- **Short-series variance:** Recent windows can be volatile, and no regular-season rating removes the randomness of a short postseason series.
- **Relative scale:** Min-max component scores are relative to the 2026 MLB field, and the quality adjustment is not a complete strength-of-schedule model.

**October Shift is a lens for comparing the profiles teams bring into October—not a World Series probability model or a guarantee of who advances.**

## Data and Pipeline

The project uses MLB schedule and game results, Statcast pitch data through `pybaseball`, and MLB play-by-play feeds. The update orchestrator runs 15 dependent steps covering data collection, offensive momentum, starter and rotation scoring, bullpen and inherited-runner analysis, the final contender board, and ranking history.

The final baseline is archived in:

```text
data/snapshots/2026-regular-season-final/
```

That archive contains the September 27 raw inputs, processed outputs, ranking history, environment record, and checksums. The `Regular Season Final` dashboard page reads its board and history directly from this frozen snapshot.

## Running Locally

The frozen environment used Python **3.12.3**. From the repository root:

```bash
python -m venv venv
```

Activate the environment on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install the declared dependencies and launch the dashboard:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The repository includes the processed files needed by the dashboard. Rebuilding the full data pipeline is optional and substantially slower because it fetches and processes season-level Statcast and play-by-play data:

```bash
python update_october_shift.py
```

The updater stops if a step fails so later outputs are not rebuilt from incomplete inputs.

## Project Structure

```text
app.py                         Streamlit dashboard
update_october_shift.py        15-step pipeline orchestrator
src/                           Data, feature, scoring, and experiment scripts
data/processed/                Dashboard-ready outputs
data/snapshots/
  2026-regular-season-final/   Frozen September 27 baseline and metadata
assets/                        Team logos, player images, and app assets
requirements.txt               Python dependencies
```

## Tech Stack

- Python 3.12
- Streamlit
- pandas and NumPy
- Requests and the MLB Stats API / play-by-play feeds
- `pybaseball` and Statcast
- HTML and CSS embedded in Streamlit
- scikit-learn and XGBoost for the earlier prediction experiments and validation work

## Project Status

The 2026 regular-season version of October Shift is complete. Its formula and final September 27 baseline are preserved, the actual postseason field is shown beside the model’s rankings, and the dashboard retains both the postseason-facing Home page and the frozen regular-season view.

This was built for baseball exploration and for the fun of asking a difficult October question with data. It is not an MLB production system, a betting model, or a claim that a formula can remove the uncertainty that makes postseason baseball interesting.
