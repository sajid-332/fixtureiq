git # FixtureIQ

FixtureIQ is a full-stack football match intelligence and prediction platform focused on explainable pre-match forecasting for the English Premier League.

The project combines historical football data, leakage-safe feature engineering, machine learning, current football context, backend APIs, caching, and a web frontend. The first MVP is intentionally limited to the Premier League so that the complete prediction pipeline can be built and validated before additional competitions are added.

FixtureIQ produces probabilistic estimates, not guaranteed outcomes.

## Current Development Status

FixtureIQ has completed the main implementation work for Stages 1 through 5.

| Stage | Component | Status |
| --- | --- | --- |
| 1 | Project Setup | Complete |
| 2 | Historical EPL Data | Complete |
| 3 | Basic Feature Engineering | Complete |
| 4 | H2H, Momentum and League Pressure | Complete |
| 5 | Outcome ML Model | Implemented and validated on development windows |
| 6 | Goal and Scoreline Model | Next |
| 7 | Football API and Database/Cache | Planned |
| 8 | Upcoming Fixtures, Standings and Current Form | Planned |
| 9 | Players and Injuries | Planned |
| 10 | Full Prediction Engine | Planned |
| 11 | Flask REST API | Planned |
| 12 | Next.js Website | Planned |
| 13 | Testing and Deployment | Planned |
| 14 | Documentation and Portfolio Presentation | Planned |

## Main Goals

FixtureIQ is designed to eventually provide:

- Automatic upcoming Premier League fixtures
- Home Win, Draw and Away Win probabilities
- Expected home and away goals
- Likely final scorelines
- Recent team form analysis
- Home and away venue-strength analysis
- League-table context and games-in-hand information
- Head-to-head context
- Momentum and upset-potential signals
- League-pressure context
- Player and key-player availability when reliable data is available
- Human-readable reasons behind predictions
- Confidence and data-completeness information
- Model version and data cut-off information

## Core Engineering Principles

The project follows several rules that are important for reliable football forecasting:

- Only information known before kickoff may be used to predict a fixture.
- The target match must never influence its own feature values.
- Historical matches are processed chronologically.
- Model selection is based on chronological validation rather than random train/test shuffling.
- Probability quality is more important than headline accuracy alone.
- Missing information must be handled explicitly rather than invented.
- Bookmaker odds are excluded from the core prediction model.
- Advanced football-context features are only promoted into the core ML model when out-of-sample validation supports them.
- The 2025/26 season is kept locked as the final unseen test set during model development.

---

# Stage 1 - Project Setup

## Objective

Create a clean development foundation for the historical data pipeline, machine-learning code, Flask backend, Next.js frontend and later API integration.

## Implemented Work

- Created the main `FixtureIQ` project structure.
- Set up a Python development environment.
- Added the initial Flask backend.
- Added Flask-CORS support.
- Added a backend health endpoint at `/api/health`.
- Created the Next.js frontend project with TypeScript.
- Added Tailwind CSS support to the frontend environment.
- Created separate directories for data, ML code, scripts, backend, frontend and documentation.
- Added Git ignore rules for Python environments, cache files, Node modules, Next.js build output, databases, logs and local environment files.
- Established the English Premier League as the first MVP competition.

## Initial Backend Health Check

The current Flask application provides:

```text
GET /api/health
```

Example response:

```json
{
  "status": "ok",
  "project": "FixtureIQ"
}
```

## Current Main Project Structure

```text
FixtureIQ/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── package-lock.json
├── ml/
│   ├── features/
│   ├── models/
│   └── tests/
├── data/
│   ├── historical/
│   │   ├── raw/
│   │   └── processed/
│   └── team_name_mapping.json
├── scripts/
├── docs/
├── .gitignore
└── README.md
```

## Stage 1 Result

The repository can support independent development of the historical pipeline, machine-learning system, backend and frontend without mixing their responsibilities.

---

# Stage 2 - Historical EPL Data Pipeline

## Objective

Build a clean, chronological and reproducible historical Premier League dataset for feature engineering, training and backtesting.

## Historical Data

The current project contains five Premier League seasons from Football-Data.co.uk:

- 2021/22
- 2022/23
- 2023/24
- 2024/25
- 2025/26

The combined historical dataset contains:

- 1,900 matches
- 5 Premier League seasons
- 27 unique clubs across the full period

Each raw season contains 380 Premier League matches.

## Core Historical Fields

The processed historical dataset currently keeps the fields required for the first prediction pipeline:

```text
Date
HomeTeam
AwayTeam
FTHG
FTAG
FTR
Season
```

Definitions:

- `FTHG`: Full-Time Home Goals
- `FTAG`: Full-Time Away Goals
- `FTR`: Full-Time Result
- `H`: Home Win
- `D`: Draw
- `A`: Away Win

The raw Football-Data files contain additional fields such as shots and shots on target. These are not used as same-match inputs because they occur during the target fixture. They may only be used later if transformed into leakage-safe historical rolling features from previous matches.

## Team Name Standardization

Team names are standardized through:

```text
data/team_name_mapping.json
```

The historical preparation script checks that every team appearing in the raw datasets has a valid mapping before processing continues.

## Historical Processing Script

```text
scripts/prepare_historical.py
```

The script:

1. Loads all EPL season CSV files from `data/historical/raw/`.
2. Keeps the required match fields.
3. Adds the season identifier.
4. Validates team-name mappings.
5. Standardizes team names.
6. Parses match dates.
7. Combines the seasons.
8. Sorts the full dataset chronologically.
9. Saves the processed historical dataset.

Output:

```text
data/historical/processed/epl_historical.csv
```

## Historical Validation

The project includes:

```text
scripts/validate_historical.py
```

The validation checks:

- Exactly 1,900 matches are present.
- Required historical fields contain no missing values.
- Duplicate rows are not present.
- `FTR` contains only `H`, `D` or `A`.
- The recorded result agrees with the full-time goal values.

## Leakage Rule Established in Stage 2

Historical data is ordered chronologically because football prediction is time dependent.

For any historical target fixture, the prediction pipeline may only use information that existed before that fixture. Information from the target result or later fixtures is not allowed to flow backward into the prediction features.

## Stage 2 Result

A validated and chronologically ordered historical EPL dataset was created as the base dataset for all later feature engineering.

---

# Stage 3 - Basic Feature Engineering

## Objective

Transform raw historical match results into meaningful pre-match form features while preserving strict chronological leakage protection.

## Generated Dataset

Stage 3 creates:

```text
data/historical/processed/epl_features.csv
```

Current shape:

```text
1,900 rows
11 columns
```

## Recent Form Features

Stage 3 creates recent team-form features based on the previous five completed matches within the current season.

```text
HomeLast5Points
AwayLast5Points
```

Football points are converted as:

```text
Win  = 3
Draw = 1
Loss = 0
```

Example:

```text
W W D L W
3 + 3 + 1 + 0 + 3 = 10 points
```

## Venue-Specific Form Features

The pipeline also creates home-only and away-only rolling form:

```text
Last5HomePoints
Last5AwayPoints
```

These features separate general form from venue performance. This is useful because teams can have substantially different home and away records.

## Leakage-Safe Rolling Logic

The rolling features use a one-match shift before calculating the rolling window.

Conceptually:

```text
Previous completed matches
        |
        v
Calculate pre-match feature
        |
        v
Store feature for target fixture
        |
        v
Target fixture is completed
        |
        v
Its result may influence future fixtures only
```

This ensures that a target fixture never contributes to its own recent-form values.

## Early-Season Missing Values

At the start of a season there may not yet be five completed matches for a club. Stage 3 preserves these limited-history situations rather than filling them with future information.

The early-season weakness created by season-reset form was later addressed more carefully in Stage 5 through historical-strength features.

## Stage 3 Feature Validation

The project includes:

```text
ml/features/validate_features.py
```

The validation checks:

- 1,900 matches are preserved.
- Required match columns exist.
- No duplicate rows are present.
- Core match data is complete.
- Results contain only `H`, `D` and `A`.
- Rolling points features remain within the valid 0 to 15 range.

## Stage 3 Result

FixtureIQ gained its first leakage-safe pre-match football features: recent team form and venue-specific form.

---

# Stage 4 - H2H, Momentum and League Pressure

## Objective

Extend the basic form dataset with richer pre-match football context while keeping every calculation backtest safe.

## Generated Dataset

Stage 4 creates:

```text
data/historical/processed/epl_stage4_features.csv
```

Current shape:

```text
1,900 rows
57 columns
```

Stage 4 adds four major feature families:

1. League-table state
2. Head-to-head context
3. Momentum and upset potential
4. League pressure

## League-Table State

For every fixture, FixtureIQ reconstructs the table state before that match is processed.

Key features include:

```text
HomeGamesPlayedBefore
AwayGamesPlayedBefore
HomeLeaguePointsBefore
AwayLeaguePointsBefore
LeaguePointsGap
GamesPlayedGap
HomePositionBefore
AwayPositionBefore
```

The target fixture result is applied to the league table only after the pre-match feature snapshot is stored.

This allows the model to know the actual table situation that existed before kickoff without using future table information.

## Head-to-Head Features

Recent historical meetings between the same two clubs are tracked using only meetings that occurred before the target fixture.

Key fields include:

```text
HomeH2HLast5Points
AwayH2HLast5Points
H2HMatchesBefore
H2HMatchesUsed
```

H2H is treated as contextual evidence rather than a dominant rule because old meetings can involve different managers, squads and team strengths.

## Momentum Features

Momentum is represented through measurable performance changes instead of subjective descriptions.

Key fields include:

```text
HomeSeasonPPG
HomeRecentPPG
HomeMomentum
AwaySeasonPPG
AwayRecentPPG
AwayMomentum
MomentumGap
SeasonStrengthGap
RecentFormGap
FormSwing
```

The basic idea is to compare recent performance with the team's broader season level.

A team performing materially above its season baseline can therefore be identified as experiencing a positive momentum shift.

## Upset Potential

Stage 4 also creates:

```text
UpsetPotential
UpsetDirection
```

These fields provide a structured signal for situations where recent form changes and strength differences may increase uncertainty around the favourite.

They are not interpreted as a guaranteed upset prediction.

## League Pressure Features

The project converts title-race, European qualification and relegation pressure into measurable table-state variables.

Key features include:

```text
HomePointsToLeader
AwayPointsToLeader
HomePointsToTop4
AwayPointsToTop4
HomePointsAboveRelegation
AwayPointsAboveRelegation
HomeRelegationDistance
AwayRelegationDistance
HomeInRelegationZone
AwayInRelegationZone
HomeMatchesRemaining
AwayMatchesRemaining
HomeSeasonProgress
AwaySeasonProgress
HomeTitlePressure
AwayTitlePressure
HomeTop4Distance
AwayTop4Distance
HomeTop4Pressure
AwayTop4Pressure
HomeRelegationPressure
AwayRelegationPressure
```

This avoids treating motivation as an unmeasurable psychological variable. Instead, FixtureIQ uses observable league conditions such as points gaps, table zones, remaining matches and season progress.

## Backtest-Safe Processing

Stage 4 follows the same strict chronological pattern used throughout FixtureIQ:

```text
Read pre-match state
        |
        v
Calculate feature snapshot
        |
        v
Save target fixture features
        |
        v
Process target result
        |
        v
Allow result to affect future fixtures only
```

## Feature Creation Versus Model Inclusion

An important Stage 4 design decision is that creating a football feature does not automatically mean that the feature belongs in the core ML classifier.

H2H, momentum, upset potential and league-pressure features remain available in the historical dataset and can later support context and explanations.

They are only included in the core probability model when chronological validation demonstrates an improvement in out-of-sample probability quality.

This rule became important during Stage 5 model selection.

## Stage 4 Result

FixtureIQ finished Stage 4 with a broad pre-match contextual dataset containing team form, venue form, table state, H2H, momentum, upset potential and league-pressure information.

---

# Stage 5 - Outcome Machine-Learning Model

## Objective

Train the first real FixtureIQ outcome model for:

```text
Home Win / Draw / Away Win
```

The Stage 5 model returns probabilities for all three outcomes rather than only a single class label.

## Stage 5 Historical-Strength Layer

The Stage 3 recent-form features reset at each new season. This creates a problem during the first few matchweeks because current-season history is very limited.

Stage 5 therefore adds leakage-safe historical-strength features.

Generated dataset:

```text
data/historical/processed/epl_stage5_features.csv
```

Current shape:

```text
1,900 rows
65 columns
```

New historical-strength fields include:

```text
HomePreviousSeasonPPG
AwayPreviousSeasonPPG
HomePreviousSeasonDataAvailable
AwayPreviousSeasonDataAvailable
HomeCrossSeasonRecentPPG
AwayCrossSeasonRecentPPG
HomeCrossSeasonMatchesUsed
AwayCrossSeasonMatchesUsed
```

## Previous-Season Strength

Previous-season points per game provides a prior estimate of a team's strength before enough matches have been played in the new season.

This reduces the early-season information gap without using future current-season matches.

## Promoted and Returning Team Handling

The historical-strength implementation does not invent previous Premier League information for newly promoted teams.

It also avoids incorrectly carrying stale EPL form across a relegation gap. For example, if a club leaves the Premier League and returns later, old EPL last-five form is not treated as if it came directly before the new season.

## Bookmaker Odds Policy

Bookmaker odds are excluded from the core ML training features.

They may be used later only as an external benchmark for comparing FixtureIQ against market expectations.

This keeps FixtureIQ's own prediction model independent of bookmaker probabilities.

## Core Model Feature Policy

Stage 5 compared simple and advanced feature combinations rather than automatically using every Stage 4 variable.

Candidate feature sets included:

```text
core_form_table
core_plus_previous_season
core_plus_cross_season
core_plus_all_historical
```

Model selection used chronological validation log loss as the primary criterion.

The selected feature set is:

```text
core_plus_previous_season
```

## Selected Core Features

The current outcome model uses 10 features:

```text
HomeLast5Points
AwayLast5Points
Last5HomePoints
Last5AwayPoints
LeaguePointsGap
GamesPlayedGap
HomePositionBefore
AwayPositionBefore
HomePreviousSeasonPPG
AwayPreviousSeasonPPG
```

H2H, momentum/upset, league pressure and bookmaker odds are currently excluded from the core classifier.

They remain available for future context, explanations and further validation.

## Model Type

The current Stage 5 model is a multinomial Logistic Regression pipeline implemented with scikit-learn.

The pipeline uses:

- Median imputation for missing numeric values
- Missingness indicators
- Logistic Regression for three-class outcome probabilities

## Chronological Model Selection

The project does not randomly shuffle football seasons for model selection.

The feature candidates were compared through expanding chronological validation windows.

### Validation Window 1

```text
Training:   2021/22 + 2022/23
Validation: 2023/24
```

### Validation Window 2

```text
Training:   2021/22 + 2022/23 + 2023/24
Validation: 2024/25
```

The mean log-loss comparison was:

| Candidate | Mean Log Loss | Mean Accuracy | Mean Macro F1 |
| --- | ---: | ---: | ---: |
| core_plus_previous_season | 0.9864 | 54.34% | 0.4137 |
| core_plus_all_historical | 0.9866 | 54.47% | 0.4151 |
| core_plus_cross_season | 0.9878 | 54.74% | 0.4101 |
| core_form_table | 0.9948 | 55.00% | 0.4114 |

Although the simple core model had slightly higher mean accuracy, `core_plus_previous_season` produced the best mean log loss and was therefore selected.

This reflects FixtureIQ's model-selection priority: probability quality is more important than accuracy alone.

## Current 2024/25 Validation Performance

Using the selected feature set:

| Metric | Result |
| --- | ---: |
| Matches | 380 |
| Accuracy | 52.37% |
| Multiclass Log Loss | 1.0109 |
| Macro F1 | 0.3894 |
| Multiclass Brier Score | 0.6051 |
| Home Recall | 84.52% |
| Draw Recall | 0.00% |
| Away Recall | 51.52% |

Current validation confusion matrix:

```text
             Pred H   Pred D   Pred A
Actual H       131       0       24
Actual D        60       0       33
Actual A        64       0       68
```

## Baseline Comparison

The selected model is compared against simple baselines.

```text
Always-home baseline accuracy:       40.79%
Training-frequency baseline log loss: 1.0826
```

Current FixtureIQ validation:

```text
Accuracy: 52.37%
Log loss: 1.0109
```

The model therefore improves substantially on the trivial always-home accuracy baseline and improves probability quality over the naive class-frequency probability baseline.

## Early-Season Validation

Stage 5 specifically evaluates matches where both teams had fewer than five current-season matches before kickoff.

Current early-season validation results:

| Metric | Result |
| --- | ---: |
| Matches | 50 |
| Accuracy | 50.00% |
| Log Loss | 0.9830 |
| Macro F1 | 0.3911 |
| Brier Score | 0.5891 |

The historical-strength layer was introduced specifically to make this early-season period more informative.

## Locked Final Test Season

The 2025/26 season is present in the historical data but remains locked as the final unseen test set.

Current policy:

```text
2025/26 = locked_not_evaluated
```

No Stage 5 development metric is calculated on the 2025/26 season.

This prevents repeated model decisions from indirectly tuning the project to the final test data.

## Stage 5 Model Artifacts

Training generates:

```text
ml/models/outcome_model.joblib
ml/models/feature_columns.json
ml/models/metrics.json
ml/models/model_metadata.json
```

The metadata records:

- Model version
- Model type
- Training seasons
- Validation season
- Locked test season
- Selected feature set
- Exact feature columns
- Target definition
- Model classes
- Missing-value policy
- Leakage policy
- Bookmaker-odds policy
- Calibration status

Current model version:

```text
0.5.0-stage5
```

## Stage 5 Tests

Automated ML tests are stored in:

```text
ml/tests/
```

The current Stage 5 test suite checks areas including:

- Historical-strength leakage protection
- Promoted-team handling
- Relegation-gap handling
- Early-season historical fallback
- Chronological model selection
- Probability sums
- Finite evaluation metrics
- Model artifact creation
- Protection of the locked 2025/26 test season

Current result:

```text
9 passed
```

## Current Stage 5 Limitation

The major current weakness is draw classification.

On the 2024/25 validation set, the model produces valid draw probabilities but never makes Draw the highest-probability class, resulting in 0% draw recall.

This is being treated as a model-quality issue rather than hidden or artificially corrected. Probability calibration and broader outcome-quality analysis are deferred until Stage 6 and final pipeline validation.

## Stage 5 Result

FixtureIQ now has a working, reproducible and leakage-safe three-class outcome prediction pipeline that:

- Builds model-ready historical features
- Uses chronological validation
- Selects features based primarily on log loss
- Produces Home/Draw/Away probabilities
- Saves reusable model artifacts
- Preserves an untouched final test season
- Includes automated tests for critical modelling assumptions

---

# Running the Current Pipeline

Run all commands from the `FixtureIQ` project root.

## 1. Prepare Historical Data

```bash
python scripts/prepare_historical.py
```

## 2. Validate Historical Data

```bash
python scripts/validate_historical.py
```

Expected historical size:

```text
1900 matches
5 seasons
```

## 3. Build Stage 3 Features

```bash
python ml/features/build_features.py
```

## 4. Validate Stage 3 Features

```bash
python ml/features/validate_features.py
```

## 5. Build Stage 4 Features

```bash
python ml/features/build_stage4_features.py
```

## 6. Build Stage 5 Features

```bash
python ml/features/build_stage5_features.py
```

Expected output dataset:

```text
data/historical/processed/epl_stage5_features.csv
```

Expected size:

```text
1900 matches
65 columns
```

## 7. Train the Stage 5 Outcome Model

```bash
python scripts/train_models.py
```

The output should confirm that:

```text
Selected feature set: core_plus_previous_season
```

and that:

```text
2025/26 remains LOCKED
```

## 8. Run ML Tests

```bash
pytest ml/tests -q
```

Current expected result:

```text
9 passed
```

---

# Running the Backend

From the project root:

```bash
python backend/app.py
```

The current backend health endpoint is:

```text
GET /api/health
```

The larger prediction REST API is planned for Stage 11.

---

# Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The current Next.js frontend is still an early project shell. Automatic fixture and prediction pages are planned for Stage 12 after the data/API and prediction-engine stages are complete.

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- Python
- Flask
- Flask-CORS

## Data and Machine Learning

- pandas
- NumPy
- scikit-learn
- statsmodels
- joblib
- pytest

## Historical Data

- Football-Data.co.uk Premier League CSV files

## Planned Current Data

- API-Football / API-SPORTS as the primary current-data provider
- football-data.org as a possible limited fallback for basic fixture/table data

## Planned Storage and Cache

- SQLite for current data snapshots and quota-aware API caching

---

# Data Files

## Raw Historical Data

```text
data/historical/raw/epl_2021_22.csv
data/historical/raw/epl_2022_23.csv
data/historical/raw/epl_2023_24.csv
data/historical/raw/epl_2024_25.csv
data/historical/raw/epl_2025_26.csv
```

## Processed Data

```text
data/historical/processed/epl_historical.csv
data/historical/processed/epl_features.csv
data/historical/processed/epl_stage4_features.csv
data/historical/processed/epl_stage5_features.csv
```

---

# Current Model Features

The production candidate selected at Stage 5 currently uses:

```text
HomeLast5Points
AwayLast5Points
Last5HomePoints
Last5AwayPoints
LeaguePointsGap
GamesPlayedGap
HomePositionBefore
AwayPositionBefore
HomePreviousSeasonPPG
AwayPreviousSeasonPPG
```

The following engineered feature groups exist but are currently excluded from the core classifier pending stronger validation evidence:

```text
H2H
Momentum
Upset potential
League pressure
```

Bookmaker odds are intentionally excluded from model training.

---

# Model Evaluation Strategy

FixtureIQ evaluates football models chronologically.

The project avoids random shuffling because a random split can allow a model-development process to learn patterns using future football periods that would not have been known at prediction time.

Current priorities are:

1. Multiclass log loss
2. Calibration / probability reliability
3. Accuracy
4. Macro F1
5. Per-class recall
6. Brier-style probability quality
7. Baseline comparison

The final 2025/26 test evaluation remains locked until the broader prediction pipeline is finalized.

---

# Next Stage

The next development phase is Stage 6: Goal and Scoreline Model.

Planned work includes:

- Separate expected home-goals and away-goals models
- Poisson-style count modelling
- Expected-goals output
- Scoreline probability matrix
- Top likely final scorelines
- Goal MAE evaluation
- Integration of outcome probabilities with the scoreline layer
- Probability/calibration analysis before final model locking

Stage 6 will not replace the Stage 5 Home/Draw/Away model. It will add the goal and likely-scoreline layer required by the full FixtureIQ prediction output.

---

# Future Roadmap

After Stage 6, the planned development sequence is:

```text
Stage 7  - Football API + Database/Cache
Stage 8  - Upcoming Fixtures + Standings + Current Form
Stage 9  - Players + Injuries
Stage 10 - Full Prediction Engine
Stage 11 - Flask REST API
Stage 12 - Next.js Website
Stage 13 - Testing + Deployment
Stage 14 - Documentation + Portfolio Presentation
```

The project will remain Premier League focused until the complete automatic fixture-to-prediction flow works reliably.

---

# Known Current Limitations

- Draw classification remains weak in the Stage 5 development model.
- Probability calibration has not yet been finalized.
- The 2025/26 final test season has intentionally not been evaluated.
- Current player, injury and lineup data are not yet integrated.
- Current upcoming-fixture data are not yet connected to an external football API.
- The current Flask backend only contains the initial health endpoint.
- The current Next.js frontend is not yet connected to the prediction pipeline.
- Previous-season EPL strength is unavailable for newly promoted teams unless comparable historical data are added later.

These limitations are intentionally documented rather than hidden because FixtureIQ is designed as an explainable and reproducible forecasting project.

---

# Prediction Philosophy

FixtureIQ is a football analytics and probabilistic forecasting project.

It is not designed as a guaranteed betting system, a "sure win" service or an in-play betting product.

A future prediction should communicate:

- The probability of each outcome
- The likely scoreline distribution
- The evidence supporting the leading outcome
- Evidence supporting the opponent
- Important uncertainties
- Missing or stale data
- Model version
- Data update time

All predictions should be treated as estimates rather than certainties.
