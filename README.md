# October Shift

**A live 2026 MLB contender-ranking project built around one question:
which teams look built for October?**

October Shift is a Python + Streamlit sports analytics project that
ranks all 30 MLB teams using current results, recent form, run
differential, opponent-adjusted performance, projected postseason
starting rotations, and bullpen performance.

The project originally started as a single-game prediction experiment. I
tested team features, recent performance, starting-pitcher records,
run-based starter scores, and several pitching combinations. The more
complicated models did not consistently beat the simpler team baseline,
so I changed the question instead of forcing a prediction model that the
results did not support.

> **October Shift is a contender-ranking system, not a World Series
> probability model.**

A score of 82 does not mean an 82% chance to win the World Series. It is
a relative score used to compare the current profiles of all 30 teams.

------------------------------------------------------------------------

## Current October Shift Formula

  Component                          Weight
  ------------------------------ ----------
  Starting Rotation                     20%
  Bullpen                                5%
  Run Differential                      20%
  Post-All-Star Performance             20%
  Last 10 Games                         15%
  Quality-Adjusted Performance          10%
  Overall Record                        10%
  **Total**                        **100%**

The weights are intentionally being kept fixed for now. I do not want to
keep changing the formula just because I dislike where one team ranks.

------------------------------------------------------------------------

## Starting Rotation Model

October Shift builds a projected four-man postseason rotation for each
team. The rotation model is meant to reward teams that can stack several
strong starters instead of overvaluing a club with one ace and a large
drop-off behind him.

Starter scoring uses run suppression and quality/deep-start performance,
along with workload requirements and reliability adjustments to keep
short openers and tiny samples from taking over the rankings.

The rotation output includes projected rotation rank, projected ace, ace
score, top-three score, top-four score, depth score, overall rotation
score, and the projected four-man rotation.

The rotation score should be read as a **postseason rotation ceiling**.
It does not guarantee that every pitcher will be healthy, active, or
used as a starter in October.

------------------------------------------------------------------------

## Bullpen Model

Bullpen strength is now modeled separately from the starting rotation.

The bullpen pipeline uses actual relief appearances and run prevention,
then looks at the strength of the best relievers as a group. It also
tracks inherited runners because escaping another pitcher's jam matters
in a postseason bullpen.

Current bullpen output includes:

-   Bullpen rank
-   Best reliever
-   Top-three run-prevention score
-   Top-five run-prevention score
-   Qualified reliever count
-   Inherited runners, scored and stranded
-   Strand rate
-   Neutral bullpen score

Smaller samples are adjusted so a few appearances do not automatically
dominate the ranking.

------------------------------------------------------------------------

## Dashboard

The Streamlit app is now a multi-page dashboard rather than one long
report.

-   **Home** --- project overview and top contenders
-   **Rankings** --- full contender board
-   **Teams** --- individual team deep scans
-   **Rotations** --- projected postseason rotations with pitcher
    headshots
-   **Bullpens** --- bullpen rankings and reliever detail
-   **Movement** --- changes between saved ranking snapshots
-   **Model** --- plain-language explanation of the score and weights

The interface uses MLB team logos and player headshots where available
and has been worked on for desktop and smaller screens.

------------------------------------------------------------------------

## Ranking History and Movement

October Shift saves dated ranking snapshots in:

``` text
data/processed/ranking_history_2026.csv
```

The Movement page compares the newest snapshot with the previous one and
can show rank change, score change, biggest riser, biggest faller,
largest score gain, and the most stable team.

If two snapshots produce the same rankings, the page says so rather than
inventing movement. This part of the project should become more useful
as more game dates are saved.

------------------------------------------------------------------------

## One-Command Update Pipeline

Rebuild the live board with:

``` bash
python update_october_shift.py
```

The current production updater runs 14 steps in order:

``` text
1.  Fetch latest MLB games
2.  Fetch latest Statcast pitching data
3.  Find starting pitchers
4.  Build starter run scores
5.  Build projected postseason rotations
6.  Build bullpen appearance data
7.  Build inherited-runner entry data
8.  Fetch play-by-play data
9.  Score inherited runners
10. Build reliever outs
11. Build reliever run scores
12. Build bullpen scores
13. Build the October Shift contender board
14. Save ranking history
```

If one step fails, the updater stops instead of continuing with
incomplete downstream data.

Run the dashboard with:

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## Main Outputs

``` text
data/processed/contender_scores_2026.csv
data/processed/projected_rotations_2026.csv
data/processed/bullpen_scores_2026.csv
data/processed/ranking_history_2026.csv
```

The repository also contains the supporting starter, reliever,
inherited-runner, team-feature, training, and experiment files used
during development.

------------------------------------------------------------------------

## Experimental Work

Some of the experiments behind October Shift include:

-   Team-only game prediction
-   Recent-form features
-   XGBoost experiments
-   Starting-pitcher features
-   Starter-associated team records
-   Weighted starter records
-   Recent starter run scores
-   Time-window validation
-   Quality/deep-start scoring
-   Rotation-weight sensitivity testing
-   Bullpen run-prevention scoring
-   Inherited-runner tracking

Not every experiment improved performance. That is part of the project.

One of the biggest lessons has been that **adding more features does not
automatically make a model better**.

------------------------------------------------------------------------

## Tech Stack

-   Python
-   Pandas
-   NumPy
-   scikit-learn
-   XGBoost
-   pybaseball
-   Statcast / MLB data
-   Streamlit
-   HTML / CSS inside Streamlit

------------------------------------------------------------------------

## Running Locally

``` bash
git clone https://github.com/Andreachurchwell/2026-mlb-prediction
cd 2026-mlb-prediction

python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt

python update_october_shift.py
streamlit run app.py
```

Some pitching and play-by-play update steps process a large amount of
season data and can take longer than the rest.

------------------------------------------------------------------------

## What I Learned

This project changed direction because the experiments did not support
the original idea strongly enough.

I expected adding starting-pitcher data to make the daily game model
better. Several reasonable pitching features either did nothing or made
it worse. That forced me to stop asking how to make the model look
better and start asking what the data was actually useful for.

The project has given me practice with pulling and cleaning sports data,
large pitch-level datasets, historical feature engineering without
look-ahead, time-based validation, model comparison, small-sample
reliability adjustments, custom scoring systems, inherited-runner
tracking, multi-step data pipelines, and building a responsive Streamlit
interface.

------------------------------------------------------------------------

## Limitations

**October Shift is not a World Series probability model.** The score is
relative, not a percentage chance of winning the championship.

**The contender weights are hand-designed.** They represent the current
project hypothesis and have not been statistically proven to be optimal
postseason weights.

**Projected rotations are not availability forecasts.** The model does
not currently know who will be healthy or exactly how a team will set
its postseason rotation.

**Bullpen scoring is still evolving.** The current version combines run
prevention, depth, inherited-runner results and reliability adjustments,
but there are other reasonable ways to model relief pitching.

**Offense is represented indirectly.** Run differential and team results
capture offense to an extent, but there is not yet a dedicated
lineup-quality component.

**Postseason baseball is a small sample.** A strong contender profile
cannot remove the randomness of a short playoff series.

------------------------------------------------------------------------

## Next Steps

-   Deploy the current dashboard so other people can test it
-   Keep collecting ranking-history snapshots
-   Improve Movement once more dates exist
-   Consider pitcher health/availability as a separate layer
-   Consider dedicated offensive metrics
-   Compare October Shift with current World Series market rankings
-   Make cloud updates easier or scheduled
-   Test the contender score historically
-   Continue UI cleanup based on real viewer feedback

New features should earn their place instead of being added simply
because the data exists.

------------------------------------------------------------------------

## Status

**Active work in progress --- 2026 MLB season**

The scoring system, starting-rotation model, bullpen model, update
pipeline, ranking history, movement view, and multi-page dashboard are
working. The project is still being developed as new games are played
and the model is tested.
