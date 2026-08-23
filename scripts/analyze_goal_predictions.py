"""
FixtureIQ Stage 6.2.2

Expected Goals (Lambda) Analysis

Checks:
- Lambda prediction range
- Predicted vs actual goals
- MAE/RMSE
- Average expected goals
- Prediction distribution

Uses:
    Validation season only (2024/25)

2025/26 remains locked.
"""


from pathlib import Path
import json

import pandas as pd
import numpy as np

import joblib

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
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



OUTPUT_FILE = (
    MODEL_DIR
    /
    "goal_prediction_analysis.json"
)



# -------------------------------------------------
# Configuration
# -------------------------------------------------

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



def load_validation_data():

    df = pd.read_csv(
        DATA_FILE
    )


    df["Date"] = pd.to_datetime(
        df["Date"]
    )


    df = df[
        df["Season"]
        ==
        VALIDATION_SEASON
    ].copy()


    return df



# -------------------------------------------------
# Analysis
# -------------------------------------------------

def analyze():


    print(
        "Loading models..."
    )

    home_model, away_model = load_models()


    print(
        "Loading validation data..."
    )

    df = load_validation_data()



    X = df[FEATURES]


    print(
        "Generating lambda predictions..."
    )


    df["HomeLambda"] = (
        home_model.predict(X)
    )


    df["AwayLambda"] = (
        away_model.predict(X)
    )



    # -------------------------------------------------
    # Metrics
    # -------------------------------------------------

    home_mae = mean_absolute_error(
        df["FTHG"],
        df["HomeLambda"]
    )


    away_mae = mean_absolute_error(
        df["FTAG"],
        df["AwayLambda"]
    )



    home_rmse = np.sqrt(
        mean_squared_error(
            df["FTHG"],
            df["HomeLambda"]
        )
    )


    away_rmse = np.sqrt(
        mean_squared_error(
            df["FTAG"],
            df["AwayLambda"]
        )
    )



    # -------------------------------------------------
    # Report
    # -------------------------------------------------

    report = {


        "validation_season":
            VALIDATION_SEASON,


        "matches_analyzed":
            len(df),



        "average_lambda": {

            "home":
                round(
                    df["HomeLambda"].mean(),
                    4
                ),

            "away":
                round(
                    df["AwayLambda"].mean(),
                    4
                )

        },


        "average_actual_goals": {

            "home":
                round(
                    df["FTHG"].mean(),
                    4
                ),

            "away":
                round(
                    df["FTAG"].mean(),
                    4
                )

        },



        "metrics": {


            "home": {

                "mae":
                    round(
                        home_mae,
                        4
                    ),

                "rmse":
                    round(
                        home_rmse,
                        4
                    )

            },


            "away": {

                "mae":
                    round(
                        away_mae,
                        4
                    ),

                "rmse":
                    round(
                        away_rmse,
                        4
                    )

            }

        },



        "lambda_range": {


            "home": {

                "min":
                    round(
                        df["HomeLambda"].min(),
                        4
                    ),

                "max":
                    round(
                        df["HomeLambda"].max(),
                        4
                    )

            },


            "away": {

                "min":
                    round(
                        df["AwayLambda"].min(),
                        4
                    ),

                "max":
                    round(
                        df["AwayLambda"].max(),
                        4
                    )

            }

        },



        "extreme_predictions": {


            "home_lambda_above_4":

                int(
                    (
                        df["HomeLambda"]
                        >
                        4
                    )
                    .sum()
                ),


            "away_lambda_above_4":

                int(
                    (
                        df["AwayLambda"]
                        >
                        4
                    )
                    .sum()
                )

        }

    }



    # Save report

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            report,
            f,
            indent=4
        )


    print("\nStage 6.2.2 Analysis Complete")
    print("--------------------------------")

    print(
        json.dumps(
            report,
            indent=4
        )
    )

    print(
        "\nSaved:",
        OUTPUT_FILE
    )



if __name__ == "__main__":

    analyze()