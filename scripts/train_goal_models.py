"""
FixtureIQ Stage 6.2
Expected Goals Model

Trains Poisson regression models:

1. Home goals model
2. Away goals model

Output:
    ml/models/home_goal_model.joblib
    ml/models/away_goal_model.joblib
    ml/models/goal_model_metrics.json
"""


from pathlib import Path
import json

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from sklearn.linear_model import PoissonRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)

import numpy as np



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


MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)



# -------------------------------------------------
# Configuration
# -------------------------------------------------

VALIDATION_SEASON = "2024/25"

LOCKED_TEST_SEASON = "2025/26"



# -------------------------------------------------
# Features
# -------------------------------------------------

FEATURES = [

    # Goal features

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


    # Stage 5 strength information

    "HomePreviousSeasonPPG",
    "AwayPreviousSeasonPPG",

    "HomePositionBefore",
    "AwayPositionBefore",

    "LeaguePointsGap",
    "GamesPlayedGap"

]



# -------------------------------------------------
# Load data
# -------------------------------------------------

def load_data():

    print("Loading Stage 6 dataset...")

    df = pd.read_csv(
        DATA_FILE
    )


    df["Date"] = pd.to_datetime(
        df["Date"]
    )


    df = (
        df
        .sort_values("Date")
        .reset_index(drop=True)
    )


    return df



# -------------------------------------------------
# Train model
# -------------------------------------------------

def build_model():


    return Pipeline([

        (
            "imputer",
            SimpleImputer(
                strategy="median"
            )
        ),


        (
            "model",
            PoissonRegressor(
                alpha=0.1,
                max_iter=1000
            )
        )

    ])



# -------------------------------------------------
# Evaluation
# -------------------------------------------------

def evaluate(
    model,
    X,
    y
):

    prediction = model.predict(X)


    return {

        "mae":
            round(
                mean_absolute_error(
                    y,
                    prediction
                ),
                4
            ),


        "rmse":
            round(
                np.sqrt(
                    mean_squared_error(
                        y,
                        prediction
                    )
                ),
                4
            )

    }



# -------------------------------------------------
# Main
# -------------------------------------------------

def train_goal_models():


    df = load_data()



    print("\nDataset:")
    print(df["Season"].value_counts())



    # ---------------------------------------------
    # Keep 2025/26 untouched
    # ---------------------------------------------

    train_df = df[
        df["Season"]
        .isin(
            [
                "2021/22",
                "2022/23",
                "2023/24"
            ]
        )
    ]


    validation_df = df[
        df["Season"]
        ==
        VALIDATION_SEASON
    ]


    print("\nTrain:")
    print(len(train_df))


    print(
        "Validation:"
    )

    print(
        len(validation_df)
    )


    print(
        "Locked test:",
        LOCKED_TEST_SEASON
    )



    X_train = train_df[FEATURES]

    X_val = validation_df[FEATURES]



    # ---------------------------------------------
    # Home goals model
    # ---------------------------------------------

    print(
        "\nTraining home goal model..."
    )


    home_model = build_model()


    home_model.fit(
        X_train,
        train_df["FTHG"]
    )


    home_metrics = evaluate(
        home_model,
        X_val,
        validation_df["FTHG"]
    )



    # ---------------------------------------------
    # Away goals model
    # ---------------------------------------------

    print(
        "Training away goal model..."
    )


    away_model = build_model()


    away_model.fit(
        X_train,
        train_df["FTAG"]
    )


    away_metrics = evaluate(
        away_model,
        X_val,
        validation_df["FTAG"]
    )



    # ---------------------------------------------
    # Save models
    # ---------------------------------------------

    joblib.dump(

        home_model,

        MODEL_DIR
        /
        "home_goal_model.joblib"

    )


    joblib.dump(

        away_model,

        MODEL_DIR
        /
        "away_goal_model.joblib"

    )



    metrics = {

        "validation_season":
            VALIDATION_SEASON,


        "locked_test_season":
            LOCKED_TEST_SEASON,


        "home_goal_metrics":
            home_metrics,


        "away_goal_metrics":
            away_metrics

    }



    with open(

        MODEL_DIR
        /
        "goal_model_metrics.json",

        "w"

    ) as f:

        json.dump(
            metrics,
            f,
            indent=4
        )



    print("\nStage 6.2 completed")
    print("-------------------")


    print(
        "Home goal metrics:",
        home_metrics
    )


    print(
        "Away goal metrics:",
        away_metrics
    )



if __name__ == "__main__":

    train_goal_models()