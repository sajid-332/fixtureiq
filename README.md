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