# FixtureIQ

FixtureIQ is a full-stack English Premier League football prediction, context, and match-intelligence platform built around reproducible, leakage-safe, explainable pre-match forecasting.

The system now has three verified production-facing layers:

1. **Stage 7 — Production Prediction Layer**: generates the locked Home Win / Draw / Away Win probabilities and prediction for upcoming EPL fixtures.
2. **Stage 8 — Fixture Context Layer**: adds current standings, recent form, venue form, and fixture context without feeding that information back into the locked prediction model.
3. **Stage 9 — Match Intelligence Layer**: interprets the Stage 7 prediction with verified Stage 8 context, derives confidence/uncertainty and context-alignment signals, creates deterministic explanations, and serves them through a fail-closed REST API.

FixtureIQ produces probabilistic estimates, not guaranteed outcomes.

---

# Current Development Status

| Stage | Component | Status |
| --- | --- | --- |
| 1 | Project Setup | Complete |
| 2 | Historical EPL Data | Complete |
| 3 | Basic Feature Engineering | Complete |
| 4 | H2H, Momentum and League Pressure | Complete |
| 5 | Outcome ML Model | Complete |
| 6 | Goal and Scoreline Model | Complete / Final test recorded |
| 7 | Production Prediction Layer | Complete / Verified |
| 8 | Fixture Context Layer | Complete / Verified |
| 9 | Match Intelligence Layer | Complete / Verified |
| 10+ | Next development phase | Not yet locked in this README |

The authoritative Stage 9 completion artifact is:

```text
data/processed/intelligence/stage9_final_verification.json
```

Final Stage 9 state:

```text
STAGE 9.8: COMPLETE
STAGE 9: COMPLETE
MATCH INTELLIGENCE LAYER: VERIFIED
FIXTUREIQ STAGE 9 FINAL GATE: PASS
```

---

# Architecture

```text
Historical EPL Data
        |
        v
Leakage-Safe Historical Features
        |
        v
Chronological Model Development
        |
        v
Locked Production Prediction Model
        |
        v
Stage 7 Production Predictions
        |
        +-----------------------------+
        |                             |
        v                             v
Stage 8 Current Context        Stage 7 prediction remains locked
        |                             |
        +--------------+--------------+
                       |
                       v
              Stage 9 Intelligence
                       |
                       v
          Explanation + Runtime Safety
                       |
                       v
                 Flask REST API
```

The separation is deliberate:

- Stage 7 owns the prediction.
- Stage 8 owns current football context.
- Stage 9 may interpret the prediction with context.
- Stage 9 may not retrain the model, change probabilities, change the predicted label, recalibrate confidence, or use current context as a hidden model feature.
- Runtime services fail closed when verified dependency snapshots become stale.

---

# Core Engineering Principles

- Only information known before kickoff may influence a prediction.
- The target fixture must never influence its own feature values.
- Historical matches are processed chronologically.
- Random train/test shuffling is avoided for time-dependent football model selection.
- Probability quality is more important than headline accuracy alone.
- Missing information is handled explicitly rather than invented.
- Bookmaker odds are excluded from the core prediction model.
- H2H, momentum, pressure, standings, form, and other context are not silently promoted into the classifier.
- Context may explain a prediction but may not modify it.
- Provider IDs are not FixtureIQ's canonical team identity.
- Production artifacts are verified through downstream SHA-256 dependency chains.
- Runtime APIs fail closed instead of serving stale or partially valid intelligence.
- The 2025/26 EPL season was held out during model development and evaluated at the final-test stage. Its results are retained without post-test tuning.
- The current production season is **2026** (2026/27 EPL).

---

# Stage 1 — Project Setup

## Objective

Create a clean repository for historical data, ML code, backend services, frontend work, scripts, tests, and documentation.

## Implemented

- Python development environment
- Flask backend and Flask-CORS
- Health endpoint at `GET /api/health`
- Next.js frontend shell
- TypeScript and Tailwind CSS
- Separate data, ML, backend, frontend, script, test, and documentation responsibilities
- EPL selected as the first supported competition

Example health response:

```json
{
  "status": "ok",
  "project": "FixtureIQ"
}
```

---

# Stage 2 — Historical EPL Data Pipeline

## Objective

Create a chronological and reproducible historical EPL dataset for feature engineering, model development, and backtesting.

Historical source seasons:

- 2021/22
- 2022/23
- 2023/24
- 2024/25
- 2025/26

Original combined size:

```text
1,900 matches
5 EPL seasons
```

Core fields:

```text
Date
HomeTeam
AwayTeam
FTHG
FTAG
FTR
Season
```

Team names are standardized through:

```text
data/team_name_mapping.json
```

Stage 2 established the project's main leakage rule: a historical target fixture may use only information that existed before that fixture.

---

# Stage 3 — Basic Feature Engineering

Stage 3 built leakage-safe recent-form and venue-form features.

Output:

```text
data/historical/processed/epl_features.csv
```

Important fields include:

```text
HomeLast5Points
AwayLast5Points
Last5HomePoints
Last5AwayPoints
```

Rolling features use a one-match shift so the target match never contributes to its own pre-match feature values.

---

# Stage 4 — H2H, Momentum and League Pressure

Stage 4 expanded the historical feature set with:

- pre-match league-table state
- head-to-head context
- momentum signals
- upset-potential signals
- title/top-four/relegation pressure context

Output:

```text
data/historical/processed/epl_stage4_features.csv
```

Stage 4 also established a key governance rule: **creating a football feature does not automatically mean it belongs in the core classifier**. Model inclusion requires chronological out-of-sample evidence.

---

# Stage 5 — Outcome Machine-Learning Model

## Objective

Build the first reproducible three-class outcome model:

```text
Home Win
Draw
Away Win
```

Stage 5 added leakage-safe historical-strength features, including previous-season strength and cross-season recent form.

Output:

```text
data/historical/processed/epl_stage5_features.csv
```

The selected development feature set was:

```text
core_plus_previous_season
```

with ten features:

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

The Stage 5 development model was a multinomial Logistic Regression pipeline with median imputation and missingness indicators.

Model selection used expanding chronological validation windows and prioritized multiclass log loss over accuracy alone.

A major observed limitation was draw classification, which remained weak despite valid draw probabilities.

---

# Stage 6 — Goal and Scoreline Model

## Objective

Add expected-goal and scoreline modelling and integrate it with the Stage 5 outcome layer.

Completed work:

```text
6.1    Goal feature preparation
6.2    Goal prediction
6.2.2  Lambda analysis
6.3    Poisson scoreline engine
6.4    Integrated prediction
6.4.2  Integrated backtest
6.4.3  Probability blend
6.5.1  Freeze 30/70 blend
6.5.2  Final production pipeline
6.5.3  Validation reproduction
6.5.4  2025/26 final test
6.5.5  Final evaluation
6.6    Detailed goal/scoreline analysis
6.7    Documentation/final checkpoint
```

## Frozen Stage 6 Blend

```text
Stage 5 outcome layer = 30%
Stage 6 scoreline layer = 70%
```

## 2024/25 Validation

| Metric | Result |
| --- | ---: |
| Accuracy | 53.16% |
| Log Loss | 0.9965 |
| Brier Score | 0.5962 |

## 2025/26 Final Test

| Metric | Result |
| --- | ---: |
| Accuracy | 48.42% |
| Log Loss | 1.0473 |
| Brier Score | 0.6321 |

## Scoreline Performance

| Metric | Result |
| --- | ---: |
| Exact Score | 11.84% |
| Top-3 Coverage | 32.37% |
| Top-5 Coverage | 45.53% |

## Expected-Goal Performance

| Metric | Result |
| --- | ---: |
| Home Goal MAE | 0.9798 |
| Away Goal MAE | 0.8548 |

## Calibration

| Metric | Result |
| --- | ---: |
| ECE | 0.0798 |
| MCE | 0.2068 |

Draw performance remained weak:

```text
Precision = 0.0000
Recall    = 0.0000
F1        = 0.0000
```

The 2025/26 holdout was evaluated only at the final-test stage and was not used for post-test tuning.

---

# Stage 7 — Production Prediction Layer

## Objective

Turn the research pipeline into a reproducible, artifact-backed production prediction system for the live EPL season.

Stage 7 is the authoritative prediction source consumed by Stage 9.

## Production Season

```text
Competition: English Premier League
API-Football league ID: 39
Production season: 2026
```

This corresponds to the 2026/27 EPL campaign.

## Current-Data Providers

### API-Football

API-Football integration and normalization were implemented, but the Free plan did not provide access to the required 2026 season. It is therefore not relied upon as the live 2026 production fixture source under the current plan constraint.

### football-data.org

`football-data.org` became the live production fixture/context provider for the EPL.

Competition code:

```text
PL
```

The 2026 competition schedule contains 380 EPL fixtures.

Provider credentials remain environment secrets and are never stored in README or committed source files.

## Production History

Production feature state is built from:

```text
Protected production historical base
+ full 2025/26 results
+ completed 2026/27 fixtures
```

The protected production base contains 760 matches from seasons 2023 and 2024. The live row count then grows as current-season fixtures are completed.

## Team Identity

Provider IDs are not used as FixtureIQ's canonical team identity.

FixtureIQ uses deterministic UUID-based internal team IDs. Important normalization aliases include:

```text
Man City      -> Manchester City
Man United    -> Manchester United
Nott'm Forest -> Nottingham Forest
```

## Production Feature Contract

The Stage 7 production feature schema contains 86 features.

Target encoding:

```text
0 = Draw
1 = Home Win
2 = Away Win
```

Historical production features are generated using strict pre-match logic.

## Locked Production Model

Stage 7 performed final production model selection and locking. The selected production classifier is a locked Random Forest model.

Governance rules:

- no retraining after final locking
- no reselection based on the final test
- no tuning based on the final test
- no bookmaker odds in the core model
- Stage 8 context is not inserted into the Stage 7 feature vector
- Stage 9 cannot alter Stage 7 probabilities

The selected model artifact is verified by the production contract and SHA-based verification chain.

## Final Locked Test Evidence

| Metric | Result |
| --- | ---: |
| Accuracy | 0.442105 |
| Log Loss | 1.046655 |
| Brier Score | 0.629781 |
| ECE | 0.070787 |
| MCE | 0.274838 |
| Macro Precision | 0.296683 |
| Macro Recall | 0.410656 |
| Macro F1 | 0.341003 |
| Matches | 380 |

Selected class-level results:

```text
Home precision = 0.5163
Home recall    = 0.7840
Draw F1        = 0.0000
Away precision = 0.4254
Away recall    = 0.5000
```

The draw weakness remains visible in the production evidence rather than being hidden by post-processing.

## Production Refresh Flow

```text
Build production history
        |
        v
Fetch current EPL fixtures
        |
        v
Prepare production features
        |
        v
Run locked model
        |
        v
Verify prediction artifact
        |
        v
Expose verified predictions
```

Typical commands:

```bash
python scripts/build_production_history.py
python scripts/fetch_production_fixtures.py
python scripts/prepare_production_features.py
python scripts/run_production_predictions.py
python scripts/verify_production_predictions.py
python scripts/verify_stage7_8.py
```

## Stage 7 REST Layer

Production services are exposed under:

```text
/api/v1/production/
```

The API provides status and artifact-backed prediction access, including upcoming, fixture-level, and team-level prediction views.

## Stage 7 Safety

The production repository is fail-closed:

- invalid artifacts are not served
- verification failures produce a not-ready state
- freshness is evaluated dynamically
- only verified public fields are exposed
- provider fetching and model execution are separated from read-only API access

## Stage 7 Result

Stage 7 converted FixtureIQ from model research into a verified production prediction layer for upcoming EPL fixtures.

---

# Stage 8 — Fixture Context Layer

## Objective

Describe the current football situation around a fixture without modifying the locked prediction.

Stage 8 adds information such as:

- current league position
- league points
- goal difference
- recent form
- recent goal difference
- recent home form
- recent away form
- recent-history availability
- fixture/context freshness state

## Stage 8 Contract

Stage 8 is context-only. It is forbidden from:

- loading or executing the prediction model
- retraining, tuning, or reselecting a model
- changing probabilities or labels
- mutating the Stage 7 feature schema
- using standings/form as hidden model features
- using future results
- using bookmaker odds
- using fuzzy or silent fallback joins

## Current Standings

Stage 8 builds a canonical 20-team EPL standings snapshot.

## Current Team Form

Current form is calculated from the current season only.

Default rolling window:

```text
5 matches
```

Short early-season histories are allowed when fewer than five completed matches are available.

## Team Context

Standings and form are joined into a canonical team-context artifact using strict identity matching.

## Fixture Context

Upcoming fixtures are enriched with home-team and away-team context.

Primary artifact:

```text
data/processed/context/enriched_upcoming_fixtures.csv
```

Context families include:

```text
League position
League points
Goal difference
Recent points
Recent goal difference
Recent home form
Recent away form
Matches available
Freshness / identity metadata
```

## Runtime Freshness

Stage 8 introduced:

```text
DEPENDENCY_BASED_PLUS_TEMPORAL_BOUNDARY
```

A fixture-context snapshot is valid only while:

1. its verified dependency artifacts remain current, and
2. the fixture is still in the future.

When the temporal boundary is crossed, the service becomes:

```text
NOT_READY
```

It does not continue serving the stale snapshot.

A valid refresh can restore readiness without restarting Flask.

## Stage 8 REST Layer

Context endpoints are exposed under:

```text
/api/v1/context/
```

The verified Stage 8 API has ten context routes.

Runtime behavior:

```text
Healthy                 -> 200
Unknown identity        -> 404
Stale / invalid context -> 503
Write methods           -> 405
```

Responses use a no-store policy.

## Stage 8 Final Verification

Authoritative Stage 8 evidence:

```text
data/processed/context/stage8_final_verification.json
```

Final state:

```text
STAGE 8: COMPLETE
FIXTUREIQ CONTEXT LAYER: VERIFIED
```

---

# Stage 9 — Match Intelligence Layer

## Objective

Interpret the locked Stage 7 prediction using verified Stage 8 context.

Design principle:

```text
Stage 7: What does the model predict?
Stage 8: What is happening around the fixture?
Stage 9: How should the prediction be interpreted with verified context?
```

Stage 9 is **not another prediction model**.

It never changes:

```text
Home probability
Draw probability
Away probability
Predicted label
Stage 7 confidence
```

## Stage 9 Roadmap

```text
9.1  Match Intelligence Contract
9.2  Prediction + Context Join
9.3  Derived Match Intelligence
9.4  Confidence & Uncertainty
9.5  Explanation Engine
9.6  REST API
9.7  Runtime Freshness / Safety
9.8  Final Verification
```

The final Stage 9.8 gate is formally divided into:

```text
9.8.1  Foundation Verification
9.8.2  Prediction Integrity Verification
9.8.3  Intelligence Integrity Verification
9.8.4  API / Runtime / Safety Verification
9.8.5  Final Stage 9 Promotion
```

All five passed.

---

# Stage 9.1 — Match Intelligence Contract

Stage 9.1 locks what the intelligence layer may read, derive, and serve.

Forbidden operations include:

- model loading/execution
- model retraining/reselection/tuning
- feature-schema mutation
- probability modification or recalibration
- prediction-label modification
- context as a model feature
- provider fetching
- future-result use
- bookmaker odds
- fuzzy/fallback joins

The contract uses a dynamic downstream snapshot policy:

```text
CAPTURE_AT_DOWNSTREAM_BUILD
```

The contract locks which dependencies are allowed. Downstream Stage 9 builds record the current SHA-256 identity of those inputs.

A legitimate Stage 7/8 refresh therefore invalidates downstream Stage 9 artifacts and requires a rebuild, but does not require changing the Stage 9.1 contract.

---

# Stage 9.2 — Prediction + Context Join

Stage 9.2 joins:

```text
Stage 7 production prediction
+
Stage 8 verified fixture context
```

The five locked Stage 7 values are copied explicitly:

```text
prob_home_win   -> stage7_prob_home_win
prob_draw       -> stage7_prob_draw
prob_away_win   -> stage7_prob_away_win
predicted_label -> stage7_predicted_label
confidence      -> stage7_confidence
```

The join is strict and uses no fuzzy fallback.

Artifacts:

```text
data/processed/intelligence/match_intelligence_base.csv
data/processed/intelligence/match_intelligence_base_report.json
```

---

# Stage 9.3 — Derived Match Intelligence

Stage 9.3 derives deterministic interpretation fields.

Probability metrics:

```text
stage9_top_probability
stage9_second_probability
stage9_probability_margin
```

Context gaps:

```text
stage9_league_position_gap
stage9_points_gap
stage9_goal_difference_gap
stage9_recent_points_gap
stage9_recent_goal_difference_gap
stage9_venue_form_points_gap
```

## Five-Signal Context Support Score

Signals:

```text
League position
League points
Goal difference
Recent points
Venue-specific recent points
```

Each contributes:

```text
+1 = home-side context advantage
-1 = away-side context advantage
 0 = tie or unavailable
```

Range:

```text
-5 to +5
```

## Context Alignment

Possible values:

```text
SUPPORTIVE
MIXED
CONTRADICTORY
NEUTRAL
```

Alignment is interpreted relative to the locked Stage 7 outcome and does not alter it.

---

# Stage 9.4 — Confidence and Uncertainty

## Confidence Band

Derived from the existing Stage 7 confidence value:

```text
< 0.40        VERY_LOW
0.40 - <0.50  LOW
0.50 - <0.60  MODERATE
0.60 - <0.70  HIGH
>= 0.70       VERY_HIGH
```

## Uncertainty Band

Uncertainty is based on Shannon entropy of the full three-outcome probability vector:

```text
H = -Σ p ln(p)
```

Normalized entropy:

```text
H_normalized = H / ln(3)
```

Bands:

```text
< 0.20        VERY_LOW
0.20 - <0.40  LOW
0.40 - <0.60  MODERATE
0.60 - <0.80  HIGH
>= 0.80       VERY_HIGH
```

Confidence and uncertainty are intentionally separate concepts.

---

# Stage 9.5 — Deterministic Explanation Engine

Stage 9.5 creates human-readable interpretation without using an LLM and without changing the prediction.

Outputs:

```text
stage9_explanation_headline
stage9_explanation_summary
```

The summary includes:

- Stage 7 leading outcome
- leading probability
- margin over the next outcome
- fixed context-support score
- number of signals favoring each team
- context alignment
- confidence band
- uncertainty band
- an explicit statement that the explanation does not alter the prediction

Example structure:

```text
Stage 7 gives [subject] the highest probability at X%, Y percentage
points above the next outcome. The fixed context score is N: H signals
favor [home team], A favor [away team], and Z are neutral or unavailable.
Context alignment is ...; confidence is ... and uncertainty is ....
This interprets the existing prediction and does not alter or replace it.
```

The explanation engine rejects certainty/guarantee language.

---

# Stage 9.6 — Match Intelligence REST API

The final intelligence API has exactly five routes:

```text
GET /api/v1/intelligence/status
GET /api/v1/intelligence/matches
GET /api/v1/intelligence/matches/<fixture_id>
GET /api/v1/intelligence/team/<path:team_name>
GET /api/v1/intelligence/upcoming
```

The API is GET-only and exposes public fixture, context, prediction, uncertainty, alignment, and explanation fields while excluding internal model metadata.

---

# Stage 9.7 — Runtime Freshness / Safety

Runtime policy:

```text
DUAL_UPSTREAM_DEPENDENCY_PLUS_TEMPORAL_BOUNDARY
```

Every intelligence read revalidates the required dependency state.

Runtime checks include:

- Stage 9.1 contract integrity
- Stage 9.2 dependency snapshot identity
- Stage 7 verification evidence
- Stage 8 verification evidence
- current `FixtureContextService` readiness
- Stage 9.3–9.5 artifact integrity
- Stage 9.6 API verification
- final intelligence artifact SHA
- canonical schema
- fixture uniqueness
- explanation completeness

## Fail-Closed Behavior

```text
Healthy intelligence            -> 200 READY
Unknown fixture/team            -> 404 NOT_FOUND
Stale or invalid intelligence   -> 503 NOT_READY
POST / PUT / DELETE             -> 405
```

No stale-row fallback is allowed.

## Cache Policy

```text
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
```

## Recovery

Stage 9.7 verifies same-process recovery:

```text
READY
  |
upstream/context becomes stale
  v
NOT_READY
  |
valid snapshot restored
  v
READY
```

No Flask restart is required.

---

# Stage 9.8 — Final Verification

## 9.8.1 — Foundation Verification

Verifies the locked Stage 9 contract, exact allowed dependency set, dynamic snapshot policy, Stage 9.2 join foundation, Stage 9.3–9.5 verified state, Stage 9.6 API evidence, Stage 9.7 runtime evidence, and write protection.

Evidence:

```text
data/processed/intelligence/stage9_8_1_foundation_verification.json
```

## 9.8.2 — Prediction Integrity Verification

Independently proves that Stage 7 predictions were preserved exactly through Stage 9.

It checks all five locked fields for every fixture:

```text
Home probability
Draw probability
Away probability
Predicted label
Confidence
```

It also verifies probability-vector validity, label consistency, confidence consistency, fixture identity, and prediction-distribution preservation.

Evidence:

```text
data/processed/intelligence/stage9_8_2_prediction_integrity_verification.json
```

## 9.8.3 — Intelligence Integrity Verification

Independently recomputes and validates:

```text
Top probability
Second probability
Probability margin
Six context gaps
Five-signal support score
Context alignment
Shannon entropy
Normalized entropy
Confidence band
Uncertainty band
Deterministic explanation headline
Deterministic explanation summary
```

It also proves that Stage 9.2 base/context values were preserved exactly.

Evidence:

```text
data/processed/intelligence/stage9_8_3_intelligence_integrity_verification.json
```

## 9.8.4 — API / Runtime / Safety Verification

Independently verifies:

- exact five-route API surface
- GET-only contract
- live service readiness
- `200 READY`
- `404 NOT_FOUND`
- `405` write rejection
- fail-closed `503 NOT_READY`
- no-store headers
- safe public projection
- Stage 7/8 dependency revalidation
- temporal-boundary propagation
- no stale fallback
- same-process stale-to-healthy recovery
- no provider fetch
- no model execution
- no protected artifact mutation

Evidence:

```text
data/processed/intelligence/stage9_8_4_api_runtime_safety_verification.json
```

## 9.8.5 — Final Stage 9 Promotion

This is the only authoritative Stage 9 promotion gate.

Promotion requires:

```text
9.8.1 = PASS
9.8.2 = PASS
9.8.3 = PASS
9.8.4 = PASS
```

and all evidence snapshots must still be current at promotion time.

Final result:

```text
STAGE 9.8.5: PASS
FINAL STAGE 9 PROMOTION: VERIFIED

STAGE 9.8: COMPLETE
STAGE 9: COMPLETE
MATCH INTELLIGENCE LAYER: VERIFIED
FIXTUREIQ STAGE 9 FINAL GATE: PASS
```

Authoritative final artifact:

```text
data/processed/intelligence/stage9_final_verification.json
```

---

# Important Stage 9 Artifacts

Main directory:

```text
data/processed/intelligence/
```

Important files:

```text
stage9_intelligence_contract.json
stage9_intelligence_contract_verification.json

match_intelligence_base.csv
match_intelligence_base_report.json

match_intelligence.csv
match_intelligence_report.json

intelligence_api_verification.json
intelligence_runtime_verification.json

stage9_8_1_foundation_verification.json
stage9_8_2_prediction_integrity_verification.json
stage9_8_3_intelligence_integrity_verification.json
stage9_8_4_api_runtime_safety_verification.json

stage9_final_verification.json
```

`stage9_final_verification.json` is the authoritative proof of Stage 9 completion.

---

# Refreshing the Current Production Pipeline

A live refresh must preserve dependency order.

## 1. Refresh Stage 7 Predictions

```bash
python scripts/build_production_history.py
python scripts/fetch_production_fixtures.py
python scripts/prepare_production_features.py
python scripts/run_production_predictions.py
python scripts/verify_production_predictions.py
python scripts/verify_stage7_8.py
```

A legitimate Stage 7 refresh changes production artifact hashes and therefore makes dependent Stage 8/9 snapshots stale until rebuilt.

## 2. Rebuild Stage 8 Context

```bash
python scripts/verify_stage8_standings_source.py
python scripts/build_current_standings.py
python scripts/verify_canonical_standings.py
python scripts/verify_standings_service.py
python scripts/verify_stage8_2.py

python scripts/verify_stage8_team_form_source.py
python scripts/build_current_team_form.py
python scripts/verify_canonical_team_form.py
python scripts/verify_team_form_service.py
python scripts/verify_stage8_3.py

python scripts/build_team_context.py
python scripts/verify_stage8_team_context_build.py
python scripts/verify_team_context_independent.py
python scripts/verify_team_context_service.py
python scripts/verify_stage8_4.py

python scripts/build_enriched_upcoming_fixtures.py
python scripts/verify_stage8_fixture_context_build.py
python scripts/verify_fixture_context_independent.py
python scripts/verify_fixture_context_service.py
python scripts/verify_stage8_5.py

python scripts/verify_context_api.py
python scripts/verify_context_runtime_fail_closed.py
python scripts/verify_context_runtime_remaining.py
python scripts/verify_stage8_final.py
```

Before rebuilding Stage 9, `FixtureContextService` should report `READY`.

## 3. Rebuild Stage 9 Intelligence

Stage 9.1 remains locked during an ordinary production refresh.

```bash
python scripts/verify_stage9_prediction_context_foundation.py
python scripts/build_match_intelligence_base.py
python scripts/verify_match_intelligence_base.py
python scripts/verify_stage9_2.py

python scripts/build_match_intelligence.py
python scripts/verify_match_intelligence.py

python scripts/build_match_uncertainty.py
python scripts/verify_match_uncertainty.py

python scripts/build_match_explanations.py
python scripts/verify_match_explanations.py

python scripts/verify_intelligence_api.py
python scripts/verify_intelligence_runtime.py
```

For a canonical promoted Stage 9 snapshot, rerun the final five-gate chain:

```bash
python scripts/verify_stage9_8_1_foundation.py
python scripts/verify_stage9_8_2_prediction_integrity.py
python scripts/verify_stage9_8_3_intelligence_integrity.py
python scripts/verify_stage9_8_4_api_runtime_safety.py
python scripts/verify_stage9_8_5_final_promotion.py
```

---

# Running the Backend

From the project root:

```bash
python backend/app.py
```

Registered API families include:

```text
/api/health
/api/v1/production/...
/api/v1/context/...
/api/v1/intelligence/...
```

The backend uses separate blueprints for production predictions, fixture context, and match intelligence.

---

# Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend remains separate from the verified backend prediction/context/intelligence pipeline and should consume public REST contracts rather than reading ML artifacts directly.

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

## Data and ML

- pandas
- NumPy
- scikit-learn
- statsmodels
- joblib
- pytest

## Historical Data

- Football-Data.co.uk EPL CSV files

## Current EPL Data

- football-data.org for the current production fixture/context flow
- API-Football integration retained subject to plan/season-access constraints

## Verification / Runtime Design

- SHA-256 artifact identity
- deterministic downstream build snapshots
- artifact-backed services
- dependency freshness checks
- temporal fixture boundaries
- fail-closed REST behavior
- no-store API responses

---

# Model and Prediction Governance

The currently served prediction is owned by Stage 7.

Stage 8 and Stage 9 may not improve-looking results by altering the prediction after it has been produced.

The context/intelligence path prohibits:

```text
Model retraining
Model reselection
Model tuning
Feature-schema mutation
Probability modification
Probability recalibration
Prediction-label modification
Confidence modification
Context-as-hidden-model-feature
Bookmaker-odds injection
Future-result use
Provider fetch inside read-only intelligence serving
Fuzzy or silent fallback joins
```

This separation is one of FixtureIQ's main architectural guarantees.

---

# Evaluation Philosophy

FixtureIQ does not judge models only by accuracy.

Important metrics include:

1. Multiclass log loss
2. Brier score
3. Calibration error
4. Accuracy
5. Macro precision / recall / F1
6. Per-class performance
7. Goal MAE where applicable
8. Scoreline coverage where applicable
9. Baseline comparison
10. Final holdout integrity

A model can have acceptable overall accuracy while still showing a serious class-specific weakness such as Draw. Those weaknesses remain visible rather than being hidden by post-processing.

---

# Current Known Limitations

## Draw Prediction

Draw remains the clearest model-quality weakness. Stage 9 deliberately does not repair it by modifying the locked prediction.

## Provider Access

API-Football Free-plan season access is insufficient for the live 2026 production season, so the current production pipeline relies on football-data.org for live EPL fixture/context data.

## Temporal Freshness

A verified context/intelligence artifact is intentionally temporary. Once its fixture temporal boundary is crossed, runtime becomes `NOT_READY` until the upstream/downstream refresh chain is completed.

This is a safety feature, not a condition to bypass.

## Player / Injury Data

The verified Stage 7–9 production path does not currently depend on player/injury data. Any future integration should have its own leakage-safe and freshness-aware contract.

## Frontend Integration

The backend prediction/context/intelligence stack is currently more mature than the frontend. The UI still needs to be developed against the verified public APIs.

---

# Prediction Philosophy

FixtureIQ is a football analytics and probabilistic forecasting project.

It is not a guaranteed betting system, a "sure win" service, or an in-play certainty engine.

A useful FixtureIQ response should communicate:

- Home Win probability
- Draw probability
- Away Win probability
- predicted outcome
- confidence
- uncertainty
- current team/table context
- whether context supports or contradicts the prediction
- deterministic explanation
- data freshness
- missing information where relevant

Every prediction remains an estimate.

The explanation layer must never transform an estimate into a certainty claim.

---

# Current Project State

```text
Stage 1  — Project Setup                         COMPLETE
Stage 2  — Historical EPL Data                   COMPLETE
Stage 3  — Basic Feature Engineering             COMPLETE
Stage 4  — H2H / Momentum / League Pressure      COMPLETE
Stage 5  — Outcome ML Model                      COMPLETE
Stage 6  — Goal and Scoreline Model              COMPLETE
Stage 7  — Production Prediction Layer           COMPLETE / VERIFIED
Stage 8  — Fixture Context Layer                 COMPLETE / VERIFIED
Stage 9  — Match Intelligence Layer              COMPLETE / VERIFIED
```

Final Stage 9 verification:

```text
9.8.1  Foundation Verification                  PASS
9.8.2  Prediction Integrity Verification        PASS
9.8.3  Intelligence Integrity Verification      PASS
9.8.4  API / Runtime / Safety Verification      PASS
9.8.5  Final Stage 9 Promotion                  PASS
```

Authoritative evidence:

```text
data/processed/intelligence/stage9_final_verification.json
```

---

# Next Development Checkpoint

Stage 9 is now a locked, verified foundation.

Before beginning the next major stage, its scope should be explicitly defined and documented instead of reusing the old pre-Stage-7 roadmap.

Any future stage should preserve these guarantees:

```text
Stage 7 prediction integrity
Stage 8 context isolation
Stage 9 interpretation-only behavior
Artifact provenance
Temporal freshness
Fail-closed serving
No stale fallback
No silent probability mutation
```

That gives FixtureIQ a stable base for the next product-facing or analytical layer.
