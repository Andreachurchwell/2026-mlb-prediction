# October Shift

**A 2026 MLB contender-ranking project built around a simple question:
which teams look built for October?**

October Shift is a Python and Streamlit project that uses 2026 MLB
results and Statcast pitching data to rank all 30 teams based on more
than their win-loss record.

The project started as an attempt to predict individual MLB games with
machine learning. After testing multiple models and feature sets, the
results showed that the more complicated models were not consistently
better than a simple baseline. Instead of forcing a weak prediction
model, I shifted the project toward something I found more interesting:
measuring the overall profile of a postseason contender.

October Shift combines team performance, run differential, second-half
form, opponent-adjusted results, and a custom postseason rotation score
designed to reward teams that can potentially bring multiple strong
starting pitchers into a playoff series.

> **Important:** October Shift is a contender-ranking system, not a
> claim that it can predict the World Series winner.

------------------------------------------------------------------------

## Current October Shift Formula

The current contender score is built from six components:

  Component                        Weight
  ------------------------------ --------
  Postseason Rotation                 25%
  Run Differential                    20%
  Post-All-Star Performance           20%
  Last 10 Games                       15%
  Quality-Adjusted Performance        10%
  Overall Record                      10%

Each component is normalized across MLB before the weighted score is
calculated.

The weights are currently being kept fixed rather than changing them to
make individual team rankings look better.

------------------------------------------------------------------------

## Why Pitching Is Different in October

One of the biggest changes during development was how I handled starting
pitching.

My first pitching features included strikeout rate, walk rate,
baserunner rate, recent pitching performance, and starter-associated
team records. Adding those features directly to the single-game model
did not improve it.

But that did not mean starting pitching was unimportant.

For a postseason contender, I wanted to capture something different:

**How strong are the best three or four starters a team could
potentially use in a playoff series?**

A team with one great ace and a large drop-off should not be treated the
same as a team that can potentially start three or four high-quality
pitchers.

That led to the **Postseason Rotation Score**.

------------------------------------------------------------------------

## Postseason Rotation Score

The rotation model ranks qualified starters for each team and looks at:

-   Ace strength
-   Top-three starter strength
-   Top-four starter strength
-   Rotation depth

The rotation score currently uses:

  Rotation Component     Weight
  -------------------- --------
  Top 3 Average             35%
  Ace                       25%
  Top 4 Average             25%
  Rotation Depth            15%

### Filtering Out Openers

An early version exposed an important problem: pitchers who had
technically started games as openers could receive extremely high scores
and incorrectly appear as a team's ace.

The current version requires a pitcher to have:

-   At least 5 starts
-   At least 50 pitches per start on average

This is intended to separate normal starting pitchers from short
openers.

### Small-Sample Reliability

Five strong starts do not provide the same amount of evidence as twenty
strong starts.

October Shift applies a reliability adjustment that pulls small-sample
starter scores toward the qualified-starter league average.

That still gives a pitcher credit for pitching well while preventing a
tiny sample from automatically outranking an established starter.

### Injuries and Recent Activity

The postseason rotation score intentionally does **not** require a
pitcher to have pitched recently.

I did not want an ace who spent time on the injured list to suddenly be
treated as a bad pitcher simply because he had fewer recent appearances.

Because of that, this number should be interpreted as a:

**Postseason Rotation Ceiling**

It does **not** guarantee that every pitcher included will be healthy or
available in October.

A future version may add availability/injury status as a separate
measurement.

------------------------------------------------------------------------

## Current Leaderboard

As of the data pull on **August 16, 2026**, the top 10 were:

    Rank Team                     Record   October Shift Score
  ------ ---------------------- -------- ---------------------
       1 Milwaukee Brewers         76-48                  88.2
       2 Chicago Cubs              72-52                  84.7
       3 Atlanta Braves            73-50                  79.8
       4 Tampa Bay Rays            74-49                  79.4
       5 Los Angeles Dodgers       74-50                  74.3
       6 San Diego Padres          66-58                  72.7
       7 Boston Red Sox            66-57                  70.2
       8 Arizona Diamondbacks      66-58                  67.4
       9 New York Yankees          68-55                  63.1
      10 Detroit Tigers            60-63                  63.0

These rankings will change as more 2026 games are added.

------------------------------------------------------------------------

## Current Top Rotations

At the same point in the season, the rotation model ranked the top five:

    Rank Team
  ------ ---------------------
       1 Milwaukee Brewers
       2 Los Angeles Dodgers
       3 Atlanta Braves
       4 Chicago Cubs
       5 Boston Red Sox

The purpose of this ranking is not to identify the single best pitcher
in baseball. It is meant to measure how much high-end starting depth a
team could potentially bring into a postseason series.

------------------------------------------------------------------------

## How the Project Evolved

October Shift did not start as a power-ranking project.

The original goal was to build an XGBoost model for individual MLB
games.

I created historical pre-game features so each training row only
contained information that would have been known before that game. This
was important to avoid leaking future results into the model.

The first XGBoost test performed worse than simply picking the home
team:

  Model                      Accuracy
  ------------------------ ----------
  Home-Team Baseline            54.7%
  Original XGBoost Model        48.8%

Rather than adding more features and assuming that would solve the
problem, I compared several smaller feature sets.

The strongest version in the August holdout used recent team performance
and run differential:

  Metric                     Result
  ------------------------ --------
  Accuracy                    57.6%
  ROC AUC                     0.563
  Log Loss                    0.683
  Home Baseline Accuracy      54.7%

That was an improvement, but not strong enough for me to describe it as
a reliable game-prediction system.

------------------------------------------------------------------------

## Pitching Experiments

I pulled more than **546,000 Statcast pitches** and experimented with
several ways of adding starting pitching to the game model.

Features tested included:

-   Season strikeout rate
-   Recent strikeout rate
-   Walk rate
-   Baserunner rate
-   Starter-associated team win percentage
-   Weighted starter record
-   Recent starter record
-   Runs allowed
-   Custom starter run scores
-   Season and recent pitching combinations

In the August holdout, the team-only model remained stronger by accuracy
than the pitching versions.

One version using a recent starter run score slightly improved ROC AUC:

  Model                       Accuracy   ROC AUC   Log Loss
  ------------------------- ---------- --------- ----------
  Team Only                      57.6%     0.563      0.683
  Team + Recent Run Score        54.2%     0.564      0.690

That small difference was not enough to justify claiming that the
pitching model was better.

------------------------------------------------------------------------

## Testing Over Time

I also tested the team-only and starter-run versions across multiple
date windows.

The results moved around considerably. Sometimes the pitching feature
helped, and sometimes the team-only model performed better.

Average results across the tested windows were roughly:

  Model                       Avg. Accuracy   Avg. ROC AUC
  ------------------------- --------------- --------------
  Team Only                           51.5%          0.514
  Team + Recent Run Score             51.6%          0.529

That was another reason to stop treating the project as if I had
discovered a strong daily game predictor.

The failed and weaker experiments are part of the project. They
influenced what October Shift eventually became.

------------------------------------------------------------------------

## Data Pipeline

The project currently follows roughly this pipeline:

``` text
MLB completed games
        |
        v
games_2026.csv
        |
        +----------------------+
        |                      |
        v                      v
Team statistics         Statcast pitching data
        |                      |
        v                      v
Historical features     Identify game starters
        |                      |
        |                      v
        |               Starter appearances
        |                      |
        |                      v
        |               Starter run scores
        |                      |
        |                      v
        |               Rotation qualification
        |                      |
        |                      v
        |               Postseason Rotation Score
        |                      |
        +-----------+----------+
                    |
                    v
          October Shift Score
                    |
                    v
          Streamlit Dashboard
```

------------------------------------------------------------------------

## Main Scripts

``` text
src/
├── fetch_data.py
├── inspect_data.py
├── build_team_stats.py
├── build_features.py
├── build_training_data.py
├── train_model.py
├── compare_models.py
├── fetch_pitching.py
├── build_pitcher_starts.py
├── build_pitcher_features.py
├── compare_pitching_models.py
├── build_starter_records.py
├── compare_starter_record_models.py
├── build_starter_run_scores.py
├── compare_starter_run_models.py
├── validate_over_time.py
├── build_rotation_scores.py
└── build_contender_board.py
```

Some scripts are experiments rather than part of the final
contender-scoring pipeline. I have kept them because they document how
the project changed and which ideas did or did not work.

------------------------------------------------------------------------

## Project Structure

A simplified view:

``` text
2026-mlb-prediction/
│
├── app.py
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/
│   │   ├── games_2026.csv
│   │   └── pitching_2026.csv
│   │
│   └── processed/
│       ├── team_stats_2026.csv
│       ├── team_features_2026.csv
│       ├── training_data_2026.csv
│       ├── pitcher_starts_2026.csv
│       ├── pitcher_features_2026.csv
│       ├── starter_records_2026.csv
│       ├── starter_run_scores_2026.csv
│       ├── rotation_scores_2026.csv
│       └── contender_scores_2026.csv
│
├── models/
│   └── xgb_2026.json
│
└── src/
    └── ...
```

------------------------------------------------------------------------

## Tech Stack

-   Python
-   Pandas
-   NumPy
-   scikit-learn
-   XGBoost
-   pybaseball / Statcast
-   Streamlit

------------------------------------------------------------------------

## Running the Project

Clone the repository and move into the project directory:

``` bash
git clone https://github.com/Andreachurchwell/2026-mlb-prediction
cd 2026-mlb-prediction
```

Create and activate a virtual environment.

Windows / Git Bash:

``` bash
python -m venv venv
source venv/Scripts/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Run the Streamlit dashboard:

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## Rebuilding the Data

The project is still being developed, so the update process is not fully
automated.

The general order is:

``` bash
python src/fetch_data.py
python src/build_team_stats.py
python src/build_features.py
python src/build_training_data.py
python src/fetch_pitching.py
python src/build_pitcher_starts.py
python src/build_starter_run_scores.py
python src/build_rotation_scores.py
python src/build_contender_board.py
```

Some of these steps, especially the Statcast download, can take longer
than others.

------------------------------------------------------------------------

## What I Learned From This Project

The biggest lesson was that adding more data does not automatically make
a model better.

I expected starting-pitcher statistics to improve the individual-game
model. Several reasonable pitching features actually made it worse.

That forced me to look at what the results were saying instead of what I
expected them to say.

The project also gave me practice with:

-   Pulling and cleaning sports data
-   Working with a large pitch-level dataset
-   Building historical features without using future information
-   Comparing models against a baseline
-   Time-based train/test splits
-   Feature engineering
-   Testing ideas that did not work
-   Building custom scoring systems
-   Turning analysis into a Streamlit application

The current version of October Shift came out of those experiments
rather than being the original plan.

------------------------------------------------------------------------

## Limitations

October Shift has several important limitations.

**It is not a World Series probability model.**\
A score of 88 does not mean an 88% chance of winning the World Series.

**The weights are hand-designed.**\
The contender weights represent the current project hypothesis. They
have not been statistically proven to be the optimal postseason weights.

**Rotation score is a ceiling.**\
It measures pitcher performance and depth but does not currently
guarantee health or postseason availability.

**Bullpens are not modeled separately yet.**\
The pitching work currently focuses heavily on starting rotations.

**Offense is represented indirectly.**\
Run differential and team results capture offense to an extent, but
there is not yet a dedicated lineup/offensive-quality model.

**Postseason baseball is a small sample.**\
Even an excellent team can lose a short series.

These limitations are part of why I describe October Shift as a
contender-ranking project rather than a World Series prediction engine.

------------------------------------------------------------------------

## Possible Next Steps

The project is still in progress. Ideas I may explore next include:

-   Separate pitcher injury/availability status
-   Bullpen strength
-   Dedicated offensive metrics
-   Saving daily ranking history
-   Showing how teams move up and down over time
-   Comparing October Shift rankings with World Series betting markets
-   Automating daily data updates
-   Testing whether higher October Shift scores are associated with
    later postseason success
-   Improving the Streamlit team-detail pages

I do not plan to add every possible feature just because it is
available. New features should earn their place by either improving the
analysis or making the contender score easier to understand.

------------------------------------------------------------------------

## About the Name

**October Shift** reflects the point of the project.

The question is not simply who has the best record today.

It is about how the picture changes as the season moves toward October
and which teams begin to look more or less dangerous when recent
performance, run differential, opponent quality, and postseason rotation
depth are considered together.

------------------------------------------------------------------------

## Status

**Active project --- 2026 MLB season**

The model, rankings, and dashboard are still being developed as new
games are played.
