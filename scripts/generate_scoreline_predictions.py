"""
FixtureIQ Stage 6.3.2

Generate scoreline predictions
using:

1. Goal prediction models
2. Poisson scoreline engine

Flow:

Match features
        ↓
Home Goal Model
        ↓
Away Goal Model
        ↓
Lambda values
        ↓
Poisson Matrix
        ↓
Top scorelines
"""


from pathlib import Path

import pandas as pd
import joblib
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.append(str(BASE_DIR))


from ml.models.scoreline_model import (
    generate_score_matrix,
    get_top_scorelines
)



# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]


DATA_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "processed"
    / "epl_stage6_goal_features.csv"
)


MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "models"
)



# -------------------------------------------------
# Features
# -------------------------------------------------

FEATURES = [

    "HomeAvgGoalsScoredLast5",
    "HomeAvgGoalsConcededLast5",
    "HomeGoalDifferenceLast5",

    "AwayAvgGoalsScoredLast5",
    "AwayAvgGoalsConcededLast5",
    "AwayGoalDifferenceLast5",

    "HomeVenueGoalsScoredLast5",
    "HomeVenueGoalsConcededLast5",

    "AwayVenueGoalsScoredLast5",
    "AwayVenueGoalsConcededLast5",

    "AttackStrengthDifference",
    "DefenseStrengthDifference",
    "GoalDifferenceStrengthGap",

    "HomeAttackAwayDefenseGap",
    "AwayAttackHomeDefenseGap",

    "HomePreviousSeasonPPG",
    "AwayPreviousSeasonPPG",

    "HomePositionBefore",
    "AwayPositionBefore",

    "LeaguePointsGap",
    "GamesPlayedGap"

]



# -------------------------------------------------
# Load
# -------------------------------------------------

def load_models():

    home_model = joblib.load(
        MODEL_DIR
        /
        "home_goal_model.joblib"
    )


    away_model = joblib.load(
        MODEL_DIR
        /
        "away_goal_model.joblib"
    )


    return home_model, away_model



def load_match_data():

    df = pd.read_csv(
        DATA_FILE
    )


    return df



# -------------------------------------------------
# Prediction
# -------------------------------------------------

def predict_scoreline(
    match_index=0
):


    home_model, away_model = load_models()


    df = load_match_data()



    match = df.iloc[
        match_index
    ]



    X = df.loc[
        [match_index],
        FEATURES
    ]



    # Predict lambda

    home_lambda = float(
        home_model.predict(X)[0]
    )


    away_lambda = float(
        away_model.predict(X)[0]
    )



    print("\nFixture")
    print("----------------")

    print(
        match["HomeTeam"],
        "vs",
        match["AwayTeam"]
    )


    print("\nExpected Goals")

    print(
        "Home λ:",
        round(home_lambda,3)
    )

    print(
        "Away λ:",
        round(away_lambda,3)
    )



    # Generate score matrix

    matrix = generate_score_matrix(

        home_lambda,

        away_lambda

    )



    top_scores = get_top_scorelines(
        matrix,
        top_n=5
    )


    print("\nTop Scorelines")

    print("----------------")

    print(
        top_scores.to_string(
            index=False
        )
    )



# -------------------------------------------------

if __name__ == "__main__":

    predict_scoreline()