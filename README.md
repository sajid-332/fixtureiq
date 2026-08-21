# FixtureIQ

FixtureIQ is a full-stack football match intelligence and prediction platform.

The first version will focus on the English Premier League and will automatically display upcoming fixtures, analyze current and historical football data, and generate explainable pre-match predictions.

## Main Goals

- Show upcoming Premier League fixtures automatically
- Predict Home Win / Draw / Away Win probabilities
- Predict expected goals and likely final score
- Analyze recent team form
- Analyze home and away performance
- Consider league table pressure and games in hand
- Consider head-to-head and rivalry context
- Analyze player and key-player availability when data is available
- Detect momentum shift / upset potential
- Explain why FixtureIQ favors a result
- Show confidence and data completeness

## Planned Tech Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Backend
- Python
- Flask
- Flask-CORS

### Machine Learning
- pandas
- NumPy
- scikit-learn
- statsmodels
- joblib

### Data
- Football-Data.co.uk for historical data
- API-Football for current football data
- SQLite for MVP caching/storage

## MVP Scope

The first release supports the English Premier League only.

FixtureIQ will provide probabilistic forecasts, not guaranteed outcomes.
## Current Development Status

FixtureIQ is currently at **Stage 5: Outcome ML Model**.

Implemented Stage 5 decisions:

- Bookmaker odds are excluded from the core ML model; they may be used later only as an external benchmark.
- The 2025/26 EPL season is locked as the final unseen test set and is not used for model selection or current metrics.
- H2H, momentum/upset and league-pressure features remain available for context/explanations, but are excluded from the core classifier unless chronological validation shows that they improve probability quality.
- Leakage-safe historical-strength features provide an early-season prior without carrying stale EPL form across a relegation/promotion gap.

### Stage 5 commands

Build the Stage 5 feature dataset:

```bash
python ml/features/build_stage5_features.py
```

Train and validate the current outcome model:

```bash
python scripts/train_models.py
```

Run Stage 5 ML tests:

```bash
pytest ml/tests -q
```

The training workflow saves:

- `ml/models/outcome_model.joblib`
- `ml/models/feature_columns.json`
- `ml/models/metrics.json`
- `ml/models/model_metadata.json`

The current model is a development model. Probability calibration and the final locked-season evaluation remain deferred until the broader prediction pipeline is finalized.
