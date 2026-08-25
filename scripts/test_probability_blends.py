"""
FixtureIQ Stage 6.4.3

Probability Blend Backtest

Tests predefined combinations of:

Stage 5 Outcome Model
+
Stage 6 Poisson Outcome Probabilities

Validation:
    2024/25

Locked:
    2025/26

No retraining.
No random split.
No tuning beyond the predefined weights.

Blend formula:

    Final =
        alpha * Stage5
        +
        (1 - alpha) * Stage6
"""


from pathlib import Path
import sys
import json

import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    log_loss
)


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.append(str(BASE_DIR))


from ml.models.scoreline_model import (
    generate_score_matrix
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
    / "ml"
    / "models"
)


OUTCOME_MODEL_FILE = (
    MODEL_DIR
    / "outcome_model.joblib"
)


HOME_GOAL_MODEL_FILE = (
    MODEL_DIR
    / "home_goal_model.joblib"
)


AWAY_GOAL_MODEL_FILE = (
    MODEL_DIR
    / "away_goal_model.joblib"
)


FEATURE_COLUMNS_FILE = (
    MODEL_DIR
    / "feature_columns.json"
)


OUTPUT_FILE = (
    MODEL_DIR
    / "probability_blend_results.json"
)


# -------------------------------------------------
# Configuration
# -------------------------------------------------

VALIDATION_SEASON = "2024/25"

MAX_GOALS = 10


BLEND_WEIGHTS = [
    1.00,
    0.90,
    0.80,
    0.70,
    0.60,
    0.50,
    0.40,
    0.30,
    0.20,
    0.10,
    0.00
]


# -------------------------------------------------
# Goal model features
# -------------------------------------------------

GOAL_FEATURES = [

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
# Load models
# -------------------------------------------------

def load_models():

    print("Loading models...")

    outcome_model = joblib.load(
        OUTCOME_MODEL_FILE
    )

    home_goal_model = joblib.load(
        HOME_GOAL_MODEL_FILE
    )

    away_goal_model = joblib.load(
        AWAY_GOAL_MODEL_FILE
    )

    return (
        outcome_model,
        home_goal_model,
        away_goal_model
    )


# -------------------------------------------------
# Load Stage 5 features
# -------------------------------------------------

def load_outcome_features():

    with open(
        FEATURE_COLUMNS_FILE,
        "r"
    ) as f:

        data = json.load(f)


    if isinstance(data, list):

        return data


    if isinstance(data, dict):

        for key in [
            "features",
            "feature_columns",
            "selected_features"
        ]:

            if key in data:

                return data[key]


    raise ValueError(
        "Could not determine Stage 5 feature columns."
    )


# -------------------------------------------------
# Load validation data
# -------------------------------------------------

def load_validation_data():

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


    df = df[
        df["Season"]
        ==
        VALIDATION_SEASON
    ].copy()


    return df


# -------------------------------------------------
# Normalize result
# -------------------------------------------------

def normalize_result(value):

    text = str(value).strip().lower()


    if text in [
        "h",
        "home",
        "home_win",
        "homewin",
        "1"
    ]:

        return "H"


    if text in [
        "d",
        "draw",
        "x",
        "0"
    ]:

        return "D"


    if text in [
        "a",
        "away",
        "away_win",
        "awaywin",
        "2"
    ]:

        return "A"


    raise ValueError(
        f"Unknown result: {value}"
    )


# -------------------------------------------------
# Normalize model class
# -------------------------------------------------

def normalize_model_class(value):

    text = str(value).strip().lower()


    if text in [
        "h",
        "home",
        "home_win",
        "homewin",
        "1"
    ]:

        return "H"


    if text in [
        "d",
        "draw",
        "x",
        "0"
    ]:

        return "D"


    if text in [
        "a",
        "away",
        "away_win",
        "awaywin",
        "2"
    ]:

        return "A"


    raise ValueError(
        f"Unknown model class: {value}"
    )


# -------------------------------------------------
# Find result column
# -------------------------------------------------

def find_result_column(df):

    for column in [
        "FTR",
        "Result",
        "Outcome",
        "result"
    ]:

        if column in df.columns:

            return column


    raise ValueError(
        "Could not find result column."
    )


# -------------------------------------------------
# Stage 5 probabilities
# -------------------------------------------------

def get_stage5_probabilities(
    model,
    X
):

    raw = model.predict_proba(X)[0]

    classes = model.classes_


    probabilities = {
        "H": 0.0,
        "D": 0.0,
        "A": 0.0
    }


    for class_name, probability in zip(
        classes,
        raw
    ):

        normalized = normalize_model_class(
            class_name
        )


        probabilities[normalized] = float(
            probability
        )


    return np.array([

        probabilities["H"],
        probabilities["D"],
        probabilities["A"]

    ])


# -------------------------------------------------
# Poisson -> H/D/A
# -------------------------------------------------

def poisson_outcome_probabilities(
    home_lambda,
    away_lambda
):

    matrix = generate_score_matrix(

        home_lambda,

        away_lambda,

        max_goals=MAX_GOALS

    )


    home_probability = matrix.loc[
        matrix["HomeGoals"]
        >
        matrix["AwayGoals"],
        "Probability"
    ].sum()


    draw_probability = matrix.loc[
        matrix["HomeGoals"]
        ==
        matrix["AwayGoals"],
        "Probability"
    ].sum()


    away_probability = matrix.loc[
        matrix["HomeGoals"]
        <
        matrix["AwayGoals"],
        "Probability"
    ].sum()


    total = (
        home_probability
        +
        draw_probability
        +
        away_probability
    )


    return np.array([

        home_probability / total,

        draw_probability / total,

        away_probability / total

    ])


# -------------------------------------------------
# Multiclass Brier score
# -------------------------------------------------

def multiclass_brier_score(
    y_true,
    probabilities
):

    class_to_index = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    total = 0.0


    for actual, probability in zip(
        y_true,
        probabilities
    ):

        actual_index = (
            class_to_index[actual]
        )


        one_hot = np.zeros(3)

        one_hot[actual_index] = 1.0


        total += np.sum(
            (
                probability
                -
                one_hot
            )
            ** 2
        )


    return total / len(y_true)


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():

    (
        outcome_model,
        home_goal_model,
        away_goal_model
    ) = load_models()


    outcome_features = (
        load_outcome_features()
    )


    df = load_validation_data()


    result_column = find_result_column(
        df
    )


    print(
        f"\nValidation matches: {len(df)}"
    )


    # ---------------------------------------------
    # Generate predictions once
    # ---------------------------------------------

    y_true = []

    stage5_predictions = []

    stage6_predictions = []


    for _, match in df.iterrows():

        actual = normalize_result(
            match[result_column]
        )


        y_true.append(actual)


        # Stage 5

        outcome_X = pd.DataFrame(
            [
                match[outcome_features]
            ]
        )


        stage5 = (
            get_stage5_probabilities(
                outcome_model,
                outcome_X
            )
        )


        stage5_predictions.append(
            stage5
        )


        # Stage 6

        goal_X = pd.DataFrame(
            [
                match[GOAL_FEATURES]
            ]
        )


        home_lambda = float(
            home_goal_model
            .predict(goal_X)[0]
        )


        away_lambda = float(
            away_goal_model
            .predict(goal_X)[0]
        )


        home_lambda = max(
            0.0,
            home_lambda
        )


        away_lambda = max(
            0.0,
            away_lambda
        )


        stage6 = (
            poisson_outcome_probabilities(

                home_lambda,

                away_lambda

            )
        )


        stage6_predictions.append(
            stage6
        )


    y_true = np.array(
        y_true
    )


    stage5_predictions = np.array(
        stage5_predictions
    )


    stage6_predictions = np.array(
        stage6_predictions
    )


    # ---------------------------------------------
    # Test blends
    # ---------------------------------------------

    results = []


    for alpha in BLEND_WEIGHTS:


        beta = 1.0 - alpha


        blended = (

            alpha
            *
            stage5_predictions

            +

            beta
            *
            stage6_predictions

        )


        # Numerical normalization

        blended = (
            blended
            /
            blended.sum(
                axis=1,
                keepdims=True
            )
        )


        predictions = np.argmax(
            blended,
            axis=1
        )


        y_indices = np.array([

            {
                "H": 0,
                "D": 1,
                "A": 2
            }[value]

            for value in y_true

        ])


        accuracy = accuracy_score(
            y_indices,
            predictions
        )


        logloss = log_loss(
            y_indices,
            blended,
            labels=[0, 1, 2]
        )


        brier = multiclass_brier_score(
            y_true,
            blended
        )


        results.append({

            "stage5_weight":
                round(alpha, 2),

            "stage6_weight":
                round(beta, 2),

            "accuracy":
                round(
                    float(accuracy),
                    4
                ),

            "log_loss":
                round(
                    float(logloss),
                    4
                ),

            "brier_score":
                round(
                    float(brier),
                    4
                )

        })


    # ---------------------------------------------
    # Find best results
    # ---------------------------------------------

    best_accuracy = max(
        results,
        key=lambda x:
        x["accuracy"]
    )


    best_log_loss = min(
        results,
        key=lambda x:
        x["log_loss"]
    )


    best_brier = min(
        results,
        key=lambda x:
        x["brier_score"]
    )


    # ---------------------------------------------
    # Full report
    # ---------------------------------------------

    report = {

        "validation_season":
            VALIDATION_SEASON,

        "matches":
            len(df),

        "tested_blends":
            results,

        "best_by_accuracy":
            best_accuracy,

        "best_by_log_loss":
            best_log_loss,

        "best_by_brier":
            best_brier

    }


    # ---------------------------------------------
    # Save
    # ---------------------------------------------

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            report,
            f,
            indent=4
        )


    # ---------------------------------------------
    # Print
    # ---------------------------------------------

    print(
        "\nStage 6.4.3 Probability Blend Test"
    )

    print(
        "==================================="
    )


    print(
        "\n"
        "Stage5  Stage6  Accuracy  "
        "LogLoss  Brier"
    )


    print(
        "-"
        * 50
    )


    for result in results:

        print(

            f"{result['stage5_weight']:.0%}"
            f"      "
            f"{result['stage6_weight']:.0%}"
            f"      "
            f"{result['accuracy']:.4f}"
            f"     "
            f"{result['log_loss']:.4f}"
            f"   "
            f"{result['brier_score']:.4f}"

        )


    print(
        "\nBest by Accuracy:"
    )

    print(
        best_accuracy
    )


    print(
        "\nBest by Log Loss:"
    )

    print(
        best_log_loss
    )


    print(
        "\nBest by Brier Score:"
    )

    print(
        best_brier
    )


    print(
        "\nSaved:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()