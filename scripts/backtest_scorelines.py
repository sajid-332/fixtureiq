"""
FixtureIQ Stage 6.3.3

Scoreline Backtesting

Evaluates:
- Exact score accuracy
- Top-3 score accuracy
- Top-5 score accuracy
- Probability assigned to actual score
"""


from pathlib import Path
import sys
import json

import pandas as pd
import joblib


# -------------------------------------------------
# Add project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.append(str(BASE_DIR))


from ml.models.scoreline_model import (
    generate_score_matrix,
    get_top_scorelines
)



# -------------------------------------------------
# Paths
# -------------------------------------------------

DATA_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "processed"
    / "epl_stage6_goal_features.csv"
)


MODEL_DIR = (
    BASE_DIR
    /
    "ml"
    /
    "models"
)


OUTPUT_FILE = (
    MODEL_DIR
    /
    "scoreline_backtest_metrics.json"
)



VALIDATION_SEASON = "2024/25"



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
        MODEL_DIR /
        "home_goal_model.joblib"
    )


    away_model = joblib.load(
        MODEL_DIR /
        "away_goal_model.joblib"
    )


    return home_model, away_model



def load_data():

    df = pd.read_csv(
        DATA_FILE
    )


    df = df[
        df["Season"]
        ==
        VALIDATION_SEASON
    ].copy()


    return df



# -------------------------------------------------
# Backtest
# -------------------------------------------------

def backtest():

    home_model, away_model = load_models()

    df = load_data()


    exact_hits = 0
    top3_hits = 0
    top5_hits = 0


    actual_probabilities = []

    skipped_scores = 0



    for _, match in df.iterrows():


        X = pd.DataFrame(
            [match[FEATURES]]
        )


        home_lambda = float(
            home_model.predict(X)[0]
        )


        away_lambda = float(
            away_model.predict(X)[0]
        )



        matrix = generate_score_matrix(
            home_lambda,
            away_lambda,
            max_goals=10
        )


        top5 = get_top_scorelines(
            matrix,
            top_n=5
        )



        actual_home = int(
            match["FTHG"]
        )

        actual_away = int(
            match["FTAG"]
        )


        actual_score = (
            actual_home,
            actual_away
        )



        predicted_scores = list(
            zip(
                top5["HomeGoals"],
                top5["AwayGoals"]
            )
        )



        if predicted_scores[0] == actual_score:

            exact_hits += 1



        if actual_score in predicted_scores[:3]:

            top3_hits += 1



        if actual_score in predicted_scores:

            top5_hits += 1



        # -----------------------------------------
        # Safe probability lookup
        # -----------------------------------------

        probability_row = matrix[
            (
                matrix["HomeGoals"]
                ==
                actual_home
            )
            &
            (
                matrix["AwayGoals"]
                ==
                actual_away
            )
        ]


        if len(probability_row) > 0:


            actual_probabilities.append(

                float(
                    probability_row.iloc[0]
                    [
                        "ProbabilityPercent"
                    ]
                )

            )

        else:

            skipped_scores += 1



    total = len(df)



    results = {


        "validation_season":
            VALIDATION_SEASON,


        "matches":
            total,


        "exact_score_accuracy":

            round(
                exact_hits / total,
                4
            ),


        "top3_score_accuracy":

            round(
                top3_hits / total,
                4
            ),


        "top5_score_accuracy":

            round(
                top5_hits / total,
                4
            ),



        "average_actual_score_probability":

            round(
                sum(actual_probabilities)
                /
                len(actual_probabilities),
                4
            )
            if actual_probabilities
            else 0,



        "skipped_probability_checks":

            skipped_scores

    }



    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            results,
            f,
            indent=4
        )


    print(
        json.dumps(
            results,
            indent=4
        )
    )



if __name__ == "__main__":

    backtest()