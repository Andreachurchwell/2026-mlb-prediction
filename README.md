# October Shift

**A live 2026 MLB contender-ranking project built around one question: which teams look built for October?**

October Shift is a Python + Streamlit sports analytics project that ranks all 30 MLB teams using current 2026 results, Statcast pitching data, opponent quality, recent form, run differential, and a custom postseason rotation model.

The project did not start this way. I originally tried to build a single-game MLB prediction model. I tested team features, recent performance, starting-pitcher records, run-based starter scores, and several pitching combinations. The more complicated models did not consistently beat the simpler team baseline.

Instead of forcing a weak prediction model, I changed the question.

> **October Shift is a contender-ranking system, not a World Series probability model.**

A score of 84 does **not** mean an 84% chance to win the World Series. It is a relative score used to compare the current profiles of all 30 teams.

---

## Current October Shift Formula

The contender score combines six normalized components:

| Component | Weight |
|---|---:|
| Projected Postseason Rotation | 25% |
| Run Differential | 20% |
| Post-All-Star Performance | 20% |
| Last 10 Games | 15% |
| Quality-Adjusted Performance | 10% |
| Overall Record | 10% |

Each component is normalized across MLB before the final weighted score is calculated.

The weights are intentionally being kept fixed for now. I do not want to keep changing the formula just because I dislike where one team ranks.

---

## Why Starting Pitching Became Its Own Model

Starting pitching did not consistently improve the single-game prediction experiments, but that did not make it irrelevant.

The postseason question is different.

A team with one excellent starter and a large drop-off behind him should not automatically be treated the same as a team that can bring three or four strong starters into a short playoff series.

That led to a separate **Projected Postseason Rotation** system.

### Starter qualification

To avoid treating short openers or tiny samples like established starters, the current projected rotation pool requires:

- At least **5 starts**
- At least **50 pitches per start on average**

A reliability adjustment also pulls smaller samples toward the qualified-starter league average.

That means five good starts still count, but they are not treated as equally trustworthy as twenty-five good starts.

---

## Individual Starter Score

Qualified starters are evaluated using two ideas that survived the pitching experiments:

| Starter Component | Weight |
|---|---:|
| Run Suppression | 60% |
| Quality / Deep-Start Performance | 40% |

### Run suppression

This measures how well a starter has kept runs off the board in his 2026 starts.

### Quality / deep-start performance

This adds information about whether the pitcher is also giving his team meaningful length.

The project uses a quality-start-style proxy built from Statcast pitch data and starter game lines. It rewards starts that reach at least six innings while allowing no more than three runs.

This is not intended to replace official pitching statistics. It is a feature designed for this project.

---

## Projected Postseason Rotation Score

After the individual starter scores are built, October Shift selects one shared projected top four for each team.

The **same four pitchers** are then used throughout the team rotation calculation.

The team rotation score is:

| Rotation Component | Weight |
|---|---:|
| Top 3 Average | 40% |
| Ace Strength | 25% |
| Top 4 Average | 20% |
| #3 / #4 Depth | 15% |

This structure is meant to reward teams that can stack multiple strong starters instead of overvaluing a team with only one ace.

The current rotation score should be read as a **postseason rotation ceiling**.

It does not guarantee that every pitcher will be healthy, active, or used as a starter in October. Availability and injury status are intentionally separate problems.

---

## What the Dashboard Shows

The Streamlit dashboard includes:

- All 30 October Shift rankings
- Overall contender rank
- October Shift score
- Post-All-Star performance
- Last-10 performance
- Run differential per game
- Quality-adjusted win rate
- Projected rotation rank
- Team-level deep scan
- Projected top-four starter cards
- MLB player headshots for projected starters
- Ace, Top 3, Top 4, and rotation score information
- Responsive desktop, tablet, and mobile layouts
- Daily ranking movement support

The interface intentionally uses a darker technical / data-system visual style rather than a standard Streamlit dashboard.

---

## Ranking History

October Shift now saves a dated snapshot of the full 30-team board after every update.

History is stored in:

```text
data/processed/ranking_history_2026.csv
```

The history system avoids duplicate snapshots for the same latest completed-game date. When another game date is available, a new 30-team snapshot is added.

The dashboard is prepared to show:

```text
▲ 3   moved up three places
▼ 2   moved down two places
—     unchanged
NEW   no prior snapshot available
```

With more saved dates, this can later support team trend charts and biggest-riser / biggest-faller views.

---

## One-Command Update Pipeline

The project can now rebuild the live board with one command:

```bash
python update_october_shift.py
```

The updater runs the production pipeline in order:

```text
1. Fetch latest completed MLB games
2. Fetch current Statcast pitching data
3. Identify starting pitchers
4. Rebuild starter run scores
5. Rebuild projected postseason rotations
6. Rebuild the October Shift contender board
7. Save the dated ranking-history snapshot
```

If one step fails, the updater stops instead of continuing with partially updated data.

After updating, launch the dashboard with:

```bash
streamlit run app.py
```

---

## Main Production Files

```text
2026-mlb-prediction/
│
├── app.py
├── update_october_shift.py
├── README.md
├── requirements.txt
│
├── assets/
│   └── MLB team logo files
│
├── data/
│   ├── raw/
│   │   ├── games_2026.csv
│   │   └── pitching_2026.csv
│   │
│   └── processed/
│       ├── pitcher_starts_2026.csv
│       ├── starter_run_scores_2026.csv
│       ├── projected_rotations_2026.csv
│       ├── contender_scores_2026.csv
│       └── ranking_history_2026.csv
│
└── src/
    ├── fetch_data.py
    ├── fetch_pitching.py
    ├── build_pitcher_starts.py
    ├── build_starter_run_scores.py
    ├── build_projected_rotations.py
    ├── build_contender_board.py
    └── save_ranking_history.py
```

There are additional experiment scripts in `src/`. I have kept them because they document the path of the project and show which ideas did and did not work.

---

## Experimental Work Kept in the Repository

Some of the experiments included:

- Team-only game prediction
- Recent-form features
- XGBoost experiments
- Starting-pitcher features
- Starter-associated team records
- Weighted starter records
- Recent starter run scores
- Time-window validation
- Quality-start scoring
- Rotation-weight sensitivity testing

Not every experiment improved performance.

That is part of the project.

One of the main lessons from October Shift has been that **adding more features does not automatically make a model better**.

---

## Tech Stack

- Python
- Pandas
- NumPy
- scikit-learn
- XGBoost
- pybaseball
- Statcast data
- Streamlit
- HTML / CSS inside Streamlit

---

## Running the Project

Clone the repository:

```bash
git clone <YOUR-REPOSITORY-URL>
cd 2026-mlb-prediction
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it in Windows / Git Bash:

```bash
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Update the data and rankings:

```bash
python update_october_shift.py
```

Run the dashboard:

```bash
streamlit run app.py
```

---

## What I Learned

This project changed direction because the experiments did not support the original idea strongly enough.

I expected adding starting-pitcher data to make the daily game model better. Several reasonable pitching features either did nothing or made it worse.

That forced me to stop asking, “How can I make this model look better?” and start asking, “What is the data actually useful for?”

The project gave me practice with:

- Pulling and cleaning sports data
- Working with hundreds of thousands of Statcast pitch records
- Building historical features without looking ahead
- Time-based validation
- Comparing models against baselines
- Feature engineering
- Small-sample reliability adjustments
- Testing ideas that fail
- Designing custom scoring systems
- Building an automated multi-step data pipeline
- Building a responsive Streamlit interface
- Turning analysis into something another person can actually explore

---

## Limitations

**October Shift is not a World Series probability model.**  
The score is relative. It is not a percentage chance of winning the championship.

**The contender weights are hand-designed.**  
They represent the current project hypothesis and have not been statistically proven to be optimal postseason weights.

**The projected rotation is a ceiling.**  
It uses 2026 performance and workload but does not currently model injury status or guarantee postseason availability.

**Bullpens are not modeled separately yet.**  
The pitching work currently focuses on starting rotations.

**Offense is represented indirectly.**  
Run differential and team results capture offense to an extent, but there is not yet a dedicated lineup-quality component.

**The quality-start feature is a project proxy.**  
It is built from the available pitch/game data and should not be treated as an official MLB quality-start statistic.

**Postseason baseball is a small sample.**  
A strong contender profile cannot remove the randomness of a short playoff series.

---

## Possible Next Steps

The project is still active. The most useful next additions are likely:

- Bullpen strength
- Pitcher health / availability as a separate layer
- Dedicated offensive metrics
- Rank-over-time charts after more history accumulates
- Biggest risers and fallers
- World Series market / betting-rank comparison
- Scheduled cloud updates for the deployed dashboard
- Historical testing of whether higher October Shift scores are associated with deeper postseason runs

New features should earn their place instead of being added simply because the data exists.

---

## About the Name

**October Shift** is about how the picture changes as the season moves toward October.

The question is not simply:

> Who has the best record?

It is:

> Which teams begin to look more or less dangerous when current form, run differential, opponent quality, overall strength, and postseason rotation depth are considered together?

---

## Status

**Active project — 2026 MLB season**

The scoring system, update pipeline, ranking history, and responsive dashboard are working. The project is still being developed as new games are played and new ideas are tested.
