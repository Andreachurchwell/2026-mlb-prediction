# October Shift

**A live 2026 MLB analytics project built around one question:**

## Which teams look built for October?

October Shift is a Python + Streamlit sports analytics project that ranks all 30 MLB teams using current results, recent form, run differential, opponent-adjusted performance, projected postseason starting rotations, bullpen strength, and offensive momentum.

The project originally started as a single-game prediction experiment. I tested team features, recent performance, starting-pitcher records, run-based starter scores, and several pitching combinations.

The more complicated models did not consistently beat the simpler team baseline, so I changed the question instead of forcing a prediction model that the results did not support.

> **October Shift is a contender-ranking system, not a World Series probability model.**

A score of 82 does not mean an 82% chance to win the World Series. It is a relative score used to compare the current profiles of all 30 teams.

---

## Live Dashboard

October Shift is deployed with Streamlit:

**https://october-shift.streamlit.app/**

The dashboard updates as new 2026 MLB data is processed and pushed.

---

## Current October Shift Formula

| Component | Weight |
|---|---:|
| Starting Rotation | 20% |
| Run Differential | 20% |
| Offensive Momentum | 15% |
| Post-All-Star Performance | 15% |
| Last 10 Games | 10% |
| Overall Record | 10% |
| Bullpen | 5% |
| Quality-Adjusted Performance | 5% |
| **Total** | **100%** |

The weights are intentionally being kept fixed for now.

I do not want to keep changing the formula just because I dislike where one team ranks. New features should earn their place in the model rather than being added simply because the data exists.

---

# Model Components

## Starting Rotation Model

October Shift builds a projected four-man postseason rotation for each team.

The rotation model is meant to reward teams that can stack several strong starters instead of overvaluing a club with one ace and a large drop-off behind him.

Starter scoring uses run suppression and quality/deep-start performance, along with workload requirements and reliability adjustments to keep short openers and tiny samples from taking over the rankings.

The rotation output includes:

- Projected rotation rank
- Projected ace
- Ace score
- Top-three score
- Top-four score
- Depth score
- Overall rotation score
- Projected four-man rotation

The rotation score should be read as a **postseason rotation profile**, not a guarantee of who will actually start in October.

It does not currently know whether every pitcher will be healthy, active, or used in the same role during the postseason.

---

## Bullpen Model

Bullpen strength is modeled separately from the starting rotation.

The bullpen pipeline uses actual relief appearances and run prevention, then evaluates the strength of a team's best relievers as a group.

It also tracks inherited runners because entering with runners already on base is a different challenge from beginning a clean inning.

Current bullpen output includes:

- Bullpen rank
- Best reliever
- Top-three run-prevention score
- Top-five run-prevention score
- Qualified reliever count
- Inherited runners
- Inherited runners scored
- Inherited runners stranded
- Strand rate
- Neutral bullpen score

Smaller samples are adjusted so a few appearances do not automatically dominate the rankings.

The goal is to measure both **high-end relief quality and bullpen depth**.

---

## Offensive Momentum Model

Offensive Momentum was added because recent team results alone do not tell the full story of what a lineup is doing.

A team can be winning because of its pitching while its offense is cooling down. Another team can have a strong full-season offense that has recently gone cold.

October Shift therefore measures offense separately from wins and losses.

The current offensive model looks at three time horizons:

- **Season baseline**
- **Last 15 games**
- **Last 7 games**

The primary question is:

> **How dangerous does this offense look right now, and which direction is it moving?**

### Offensive strength metrics

Within each time window, team offense is scored using:

- OPS
- Runs per game
- Isolated power
- Walk rate
- Strikeout avoidance

The current offensive-strength blend is:

| Offensive Metric | Weight |
|---|---:|
| OPS | 35% |
| Runs per Game | 30% |
| ISO / Power | 15% |
| Walk Rate | 10% |
| Strikeout Avoidance | 10% |

### Offensive Momentum Score

The final Offensive Momentum Score emphasizes current performance:

| Window | Weight |
|---|---:|
| Last 15 Offensive Strength | 65% |
| Last 7 Offensive Strength | 20% |
| Trend vs. Season Baseline | 15% |

The season baseline helps distinguish between different situations.

For example, an elite offense going through a slump is different from a weak offense simply remaining weak.

The model also creates descriptive labels such as:

### Current level

- HOT
- STRONG
- AVERAGE
- COLD
- VERY COLD

### Direction

- HEATING UP
- RISING
- STEADY
- FADING
- COOLING
- COOLING FROM PEAK
- REBOUNDING

These labels are meant to make the underlying numbers easier to interpret. The numeric score still drives the model.

Offensive Momentum currently represents **15% of the overall October Shift Score**.

---

## Run Differential

Run differential per game measures how much a team is outscoring or being outscored by opponents.

This gives the model information that a simple win-loss record can miss.

Two teams may have similar records while one has consistently dominated opponents and the other has played many close games.

---

## Post-All-Star Performance

October Shift gives separate attention to how teams have performed after the All-Star break.

This is intended to capture the second-half version of a club rather than treating March and September as exactly the same information.

Post-All-Star performance currently represents **15% of the final score**.

---

## Last 10 Games

The Last 10 component provides a short-term team-results signal.

It is deliberately smaller than the Offensive Momentum component because a 10-game win-loss stretch can be influenced by pitching, offense, schedule strength, luck, and other factors.

The Last 10 currently represents **10% of October Shift**.

---

## Quality-Adjusted Performance

Not every win comes against the same level of competition.

The project keeps an opponent-adjusted performance measure that gives context to results based partly on the quality of the opponent at the time the game was played.

Pre-All-Star and post-All-Star games are also given different recency weights.

This component currently represents **5% of the final score**.

---

# Dashboard

The Streamlit application is a multi-page dashboard rather than one long report.

Current pages include:

- **Home** — project overview and top contenders
- **Rankings** — complete 30-team October Shift board
- **Teams** — individual team deep scans
- **Rotations** — projected postseason rotations and pitcher detail
- **Bullpens** — bullpen rankings and reliever detail
- **Offense** — offensive momentum rankings for all 30 teams
- **Movement** — changes between saved ranking snapshots
- **Model** — plain-language explanation of the scoring system and weights

The interface includes MLB team logos and pitcher headshots where available.

The layout has also been adjusted for both desktop and smaller screens.

---

# Ranking History and Movement

October Shift saves dated ranking snapshots in:

```text
data/processed/ranking_history_2026.csv
```

The Movement page compares the newest completed-game snapshot with the previous one.

It can show:

- Rank change
- Score change
- Biggest riser
- Biggest faller
- Largest score gain
- Most stable team

If two snapshots produce the same rankings, the dashboard says so rather than inventing movement.

Ranking history uses the latest completed game date rather than simply the date the updater was run.

---

# One-Command Update Pipeline

The entire production system can be rebuilt with:

```bash
python update_october_shift.py
```

The updater currently runs **15 steps in dependency order**:

```text
1.  Fetch latest MLB games
2.  Fetch latest Statcast data
3.  Build offensive momentum
4.  Find starting pitchers
5.  Build starter run scores
6.  Build projected postseason rotations
7.  Build bullpen appearance data
8.  Build inherited-runner entry data
9.  Update MLB play-by-play cache
10. Score inherited runners
11. Calculate actual relief outs
12. Build reliever run-prevention scores
13. Build team bullpen scores
14. Build the October Shift contender board
15. Save ranking history
```

If one step fails, the updater stops instead of continuing with incomplete downstream data.

That protects later outputs from being rebuilt with stale or missing inputs.

Run the dashboard locally with:

```bash
streamlit run app.py
```

---

# Data Pipeline

At a high level:

```text
MLB schedule data
        +
Statcast pitch data
        +
MLB play-by-play
        ↓
Team results / recent form
Starting pitcher scoring
Postseason rotation model
Bullpen / reliever model
Offensive momentum model
        ↓
Normalized component scores
        ↓
October Shift Score
        ↓
30-team contender rankings
        ↓
Ranking history
        ↓
Streamlit dashboard
```

---

# Main Outputs

Important processed outputs include:

```text
data/processed/contender_scores_2026.csv
data/processed/projected_rotations_2026.csv
data/processed/bullpen_scores_2026.csv
data/processed/offensive_momentum_2026.csv
data/processed/ranking_history_2026.csv
```

The repository also contains supporting starter, bullpen, inherited-runner, reliever, testing, and experiment scripts used during development.

Some large raw and intermediate data files are intentionally excluded from Git and can be rebuilt locally.

---

# Experimental Work

October Shift did not begin with the current scoring system.

Some experiments behind the project include:

- Team-only game prediction
- Recent-form features
- XGBoost experiments
- Starting-pitcher features
- Starter-associated team records
- Weighted starter records
- Recent starter run scores
- Time-window validation
- Quality/deep-start scoring
- Rotation-weight sensitivity testing
- Bullpen run-prevention scoring
- Inherited-runner tracking
- Bullpen weight testing
- Starting-pitching split testing
- Offensive momentum construction
- Season vs. Last 15 vs. Last 7 offense comparisons
- Offensive-weight sensitivity testing

Not every experiment improved the project.

That is part of the point.

One of the biggest lessons has been that **adding more features does not automatically make a model better**.

---

# Tech Stack

- Python
- Pandas
- NumPy
- scikit-learn
- XGBoost
- pybaseball
- Statcast
- MLB Stats API
- MLB play-by-play data
- Requests
- Streamlit
- HTML / CSS inside Streamlit
- Git / GitHub

---

# Running Locally

Clone the repository:

```bash
git clone https://github.com/Andreachurchwell/2026-mlb-prediction
cd 2026-mlb-prediction
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full update pipeline:

```bash
python update_october_shift.py
```

Launch the dashboard:

```bash
streamlit run app.py
```

Some Statcast, pitching, and play-by-play steps process a large amount of season data and can take longer than the rest of the pipeline.

---

# What I Learned

This project changed direction because the experiments did not support the original idea strongly enough.

I originally expected that adding more detailed starting-pitcher information would automatically improve a daily game prediction model.

It did not.

Several reasonable pitching features either added very little or made the model worse.

That forced me to stop asking how to make the model look more sophisticated and start asking what the data was actually useful for.

That eventually led to October Shift.

The project has given me practice with:

- Pulling data from APIs
- Working with large pitch-level datasets
- Cleaning and joining baseball data from multiple sources
- Feature engineering
- Time-based validation
- Comparing simpler and more complicated models
- Avoiding look-ahead
- Building custom scoring systems
- Handling small-sample reliability
- Projecting postseason rotations
- Modeling bullpen depth
- Tracking inherited runners
- Measuring offensive momentum across multiple time windows
- Testing model-weight sensitivity
- Building multi-step update pipelines
- Saving historical model snapshots
- Designing and deploying a responsive Streamlit application

One of the more important additions was Offensive Momentum.

Recent wins alone were not enough to tell me whether the bats were actually getting better or worse.

That led me to separate current offensive strength from full-season strength and compare season performance with the last 15 and last 7 games.

---

# Limitations

### October Shift is not a World Series probability model

The score is relative.

It does not represent a percentage chance of winning the championship.

### The contender weights are hand-designed

The current weights represent the project hypothesis and the results of sensitivity testing.

They have not been statistically proven to be the optimal postseason formula.

### Offensive Momentum is intentionally recent

Recent offense can change quickly.

A hot or cold stretch should influence the contender profile, but short windows also contain noise.

That is why the offense model uses multiple windows rather than relying only on the most recent few games.

### Projected rotations are not availability forecasts

The model does not currently know who will be healthy in October or exactly how each team will configure its postseason rotation.

### Bullpen roles can change

The current bullpen model evaluates 2026 relief performance and depth, but real postseason usage can differ significantly from regular-season bullpen roles.

### Trades, injuries and roster changes are difficult to represent immediately

October Shift is built from performance data.

A major roster move may take time to show up fully in the statistical profile.

### Postseason baseball is still a small sample

A strong contender profile cannot remove the randomness of a short playoff series.

---

# Next Steps

Version 1 of the core model is now working and deployed.

The priority is to let the model run rather than constantly changing the formula.

Possible future work includes:

- Continue collecting daily ranking-history snapshots
- Watch how Offensive Momentum behaves over a longer period
- Evaluate the model as the playoff field becomes clearer
- Consider player health and availability as a separate layer
- Explore better handling of trades and roster changes
- Compare October Shift rankings with external contender or market rankings
- Test the current formula historically on prior MLB seasons
- Explore automated cloud updates
- Continue UI cleanup based on real viewer feedback
- Review the model after the 2026 postseason and compare its rankings with actual results

New features should earn their place instead of being added simply because the data exists.

---

# Status

**October Shift v1 — Live during the 2026 MLB season**

The current system includes:

- MLB game-data ingestion
- Statcast ingestion
- Starting-pitcher analysis
- Projected postseason rotations
- Bullpen and reliever analysis
- Inherited-runner tracking
- Offensive Momentum
- Weighted contender scoring
- Full 30-team rankings
- Ranking history
- Movement tracking
- One-command updates
- Multi-page Streamlit dashboard
- Public deployment

The core model is now in a stable version.

The project will continue collecting 2026 data while the rankings are observed and evaluated through the rest of the season.
