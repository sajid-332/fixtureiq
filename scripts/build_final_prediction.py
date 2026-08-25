"""
FixtureIQ Stage 6.5.1 + 6.5.2

Final Production Prediction Pipeline

Frozen probability rule:

    30% Stage 5 Outcome Model
    70% Stage 6 Poisson Model

Pipeline:

    Match
       |
       v
    Stage 5 Outcome Model
       |
       +----> H/D/A probabilities
       |
       v
    Stage 6 Goal Models
       |
       +----> Home Lambda
       +----> Away Lambda
       |
       v
    Poisson Score Matrix
       |
       +----> Scoreline probabilities
       +----> H/D/A probabilities
       |
       v
    Frozen 30/70 Blend
       |
       v
    Final FixtureIQ Prediction
"""


from pathlib import Path
import sys
import json

import numpy as np
import pandas as pd
import joblib


# -------------------------------------------------
# Project root
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
    / "final_prediction.json"
)


# -------------------------------------------------
# Frozen configuration
# -------------------------------------------------

STAGE5_WEIGHT = 0.30

STAGE6_WEIGHT = 0.70

MAX_GOALS = 10

TOP_SCORELINES = 5

VALIDATION_SEASON = "2024/25"

LOCKED_TEST_SEASON = "2025/26"


# -------------------------------------------------
# Stage 6 goal features
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
# Load Stage 5 feature columns
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
        "Could not determine Stage 5 feature columns "
        "from feature_columns.json"
    )


# -------------------------------------------------
# Load data
# -------------------------------------------------

def load_data():

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
# Normalize outcome class
# -------------------------------------------------

def normalize_outcome_class(value):

    text = str(value).strip().lower()


    if text in [
        "h",
        "home",
        "homewin",
        "home_win",
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
        "awaywin",
        "away_win",
        "2"
    ]:

        return "A"


    raise ValueError(
        f"Unsupported outcome class: {value}"
    )


# -------------------------------------------------
# Stage 5 outcome probabilities
# -------------------------------------------------

def get_stage5_probabilities(
    outcome_model,
    X
):

    raw_probabilities = (
        outcome_model
        .predict_proba(X)[0]
    )


    classes = (
        outcome_model
        .classes_
    )


    probabilities = {

        "H": 0.0,

        "D": 0.0,

        "A": 0.0

    }


    for class_name, probability in zip(
        classes,
        raw_probabilities
    ):

        normalized = normalize_outcome_class(
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
# Scoreline -> H/D/A
# -------------------------------------------------

def scoreline_to_outcomes(
    score_matrix
):

    home_probability = score_matrix.loc[

        score_matrix["HomeGoals"]
        >
        score_matrix["AwayGoals"],

        "Probability"

    ].sum()


    draw_probability = score_matrix.loc[

        score_matrix["HomeGoals"]
        ==
        score_matrix["AwayGoals"],

        "Probability"

    ].sum()


    away_probability = score_matrix.loc[

        score_matrix["HomeGoals"]
        <
        score_matrix["AwayGoals"],

        "Probability"

    ].sum()


    total = (

        home_probability

        +

        draw_probability

        +

        away_probability

    )


    if total <= 0:

        raise ValueError(
            "Scoreline probability total is zero."
        )


    return np.array([

        home_probability / total,

        draw_probability / total,

        away_probability / total

    ])


# -------------------------------------------------
# Convert probabilities to names
# -------------------------------------------------

def probability_names(
    probabilities
):

    return {

        "home_win":
            float(probabilities[0]),

        "draw":
            float(probabilities[1]),

        "away_win":
            float(probabilities[2])

    }


# -------------------------------------------------
# Main prediction function
# -------------------------------------------------

def build_final_prediction(
    match
):

    (
        outcome_model,
        home_goal_model,
        away_goal_model
    ) = load_models()


    outcome_features = (
        load_outcome_features()
    )


    # ---------------------------------------------
    # Validate Stage 5 features
    # ---------------------------------------------

    missing_outcome_features = [

        feature

        for feature in outcome_features

        if feature not in match.index

    ]


    if missing_outcome_features:

        raise ValueError(
            "Missing Stage 5 features: "
            +
            str(missing_outcome_features)
        )


    # ---------------------------------------------
    # Validate Stage 6 features
    # ---------------------------------------------

    missing_goal_features = [

        feature

        for feature in GOAL_FEATURES

        if feature not in match.index

    ]


    if missing_goal_features:

        raise ValueError(
            "Missing Stage 6 features: "
            +
            str(missing_goal_features)
        )


    # ---------------------------------------------
    # Prepare feature vectors
    # ---------------------------------------------

    outcome_X = pd.DataFrame(
        [
            match[outcome_features]
        ]
    )


    goal_X = pd.DataFrame(
        [
            match[GOAL_FEATURES]
        ]
    )


    # ---------------------------------------------
    # Stage 5
    # ---------------------------------------------

    stage5_probabilities = (
        get_stage5_probabilities(
            outcome_model,
            outcome_X
        )
    )


    # ---------------------------------------------
    # Stage 6 expected goals
    # ---------------------------------------------

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


    # ---------------------------------------------
    # Generate Poisson score matrix
    # ---------------------------------------------

    score_matrix = generate_score_matrix(

        home_lambda,

        away_lambda,

        max_goals=MAX_GOALS

    )


    # ---------------------------------------------
    # Stage 6 outcome probabilities
    # ---------------------------------------------

    stage6_probabilities = (
        scoreline_to_outcomes(
            score_matrix
        )
    )


    # ---------------------------------------------
    # Frozen 30/70 blend
    # ---------------------------------------------

    final_probabilities = (

        STAGE5_WEIGHT
        *
        stage5_probabilities

        +

        STAGE6_WEIGHT
        *
        stage6_probabilities

    )


    # Numerical normalization

    final_probabilities = (

        final_probabilities

        /

        final_probabilities.sum()

    )


    # ---------------------------------------------
    # Final outcome
    # ---------------------------------------------

    outcome_labels = [
        "H",
        "D",
        "A"
    ]


    predicted_index = int(
        np.argmax(
            final_probabilities
        )
    )


    predicted_outcome = (
        outcome_labels[
            predicted_index
        ]
    )


    outcome_name = {

        "H":
            "Home Win",

        "D":
            "Draw",

        "A":
            "Away Win"

    }[
        predicted_outcome
    ]


    confidence = float(
        final_probabilities[
            predicted_index
        ]
    )


    # ---------------------------------------------
    # Top scorelines
    # ---------------------------------------------

    top_scores = get_top_scorelines(

        score_matrix,

        top_n=TOP_SCORELINES

    )


    likely_scorelines = []


    for _, row in top_scores.iterrows():

        likely_scorelines.append({

            "score":

                f"{int(row['HomeGoals'])}"
                "-"
                f"{int(row['AwayGoals'])}",

            "probability":

                round(
                    float(
                        row[
                            "ProbabilityPercent"
                        ]
                    )
                    /
                    100,
                    4
                )

        })


    predicted_score = (
        likely_scorelines[0]["score"]
    )


    # ---------------------------------------------
    # Probability gaps
    # ---------------------------------------------

    probability_gaps = {

        "home_win":

            round(
                float(
                    stage5_probabilities[0]
                    -
                    stage6_probabilities[0]
                ),
                4
            ),

        "draw":

            round(
                float(
                    stage5_probabilities[1]
                    -
                    stage6_probabilities[1]
                ),
                4
            ),

        "away_win":

            round(
                float(
                    stage5_probabilities[2]
                    -
                    stage6_probabilities[2]
                ),
                4
            )

    }


    # ---------------------------------------------
    # Validation checks
    # ---------------------------------------------

    stage5_sum = float(
        stage5_probabilities.sum()
    )


    stage6_sum = float(
        stage6_probabilities.sum()
    )


    final_sum = float(
        final_probabilities.sum()
    )


    probabilities_valid = bool(

        abs(stage5_sum - 1.0)
        < 0.000001

        and

        abs(stage6_sum - 1.0)
        < 0.000001

        and

        abs(final_sum - 1.0)
        < 0.000001

    )


    expected_goals_non_negative = bool(

        home_lambda >= 0

        and

        away_lambda >= 0

    )


    # ---------------------------------------------
    # Final prediction object
    # ---------------------------------------------

    prediction = {

        "model_version": {

            "stage5_weight":
                float(STAGE5_WEIGHT),

            "stage6_weight":
                float(STAGE6_WEIGHT),

            "weights_locked":
                True,

            "validation_season":
                VALIDATION_SEASON,

            "locked_test_season":
                LOCKED_TEST_SEASON

        },


        "fixture": {

            "home_team":
                str(match["HomeTeam"]),

            "away_team":
                str(match["AwayTeam"]),

            "season":
                str(match["Season"]),

            "date":
                str(match["Date"])

        },


        "final_prediction": {

            "outcome":
                outcome_name,

            "outcome_code":
                predicted_outcome,

            "confidence":
                round(
                    confidence,
                    4
                ),

            "home_win_probability":
                round(
                    float(
                        final_probabilities[0]
                    ),
                    4
                ),

            "draw_probability":
                round(
                    float(
                        final_probabilities[1]
                    ),
                    4
                ),

            "away_win_probability":
                round(
                    float(
                        final_probabilities[2]
                    ),
                    4
                )

        },


        "expected_goals": {

            "home":
                round(
                    home_lambda,
                    4
                ),

            "away":
                round(
                    away_lambda,
                    4
                ),

            "total":
                round(
                    home_lambda
                    +
                    away_lambda,
                    4
                )

        },


        "predicted_score":
            predicted_score,


        "likely_scorelines":
            likely_scorelines,


        "stage5_probabilities":
            probability_names(
                stage5_probabilities
            ),


        "stage6_poisson_probabilities":
            probability_names(
                stage6_probabilities
            ),


        "stage5_vs_stage6_probability_gap":
            probability_gaps,


        "validation_checks": {

            "stage5_probability_sum":
                round(
                    stage5_sum,
                    6
                ),

            "stage6_probability_sum":
                round(
                    stage6_sum,
                    6
                ),

            "final_probability_sum":
                round(
                    final_sum,
                    6
                ),

            "probabilities_valid":
                probabilities_valid,

            "expected_goals_non_negative":
                expected_goals_non_negative

        }

    }


    return prediction


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():

    print(
        "Loading Stage 6 dataset..."
    )


    df = load_data()


    validation_df = df[
        df["Season"]
        ==
        VALIDATION_SEASON
    ].copy()


    if len(validation_df) == 0:

        raise ValueError(
            "No 2024/25 validation matches found."
        )


    match = validation_df.iloc[0]


    print(
        "\nTesting fixture:"
    )


    print(

        f"{match['HomeTeam']}"
        f" vs "
        f"{match['AwayTeam']}"

    )


    prediction = build_final_prediction(
        match
    )


    print(
        "\nFINAL FIXTUREIQ PREDICTION"
    )


    print(
        "==========================="
    )


    print(
        json.dumps(
            prediction,
            indent=4
        )
    )


    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            prediction,
            f,
            indent=4
        )


    print(
        "\nSaved:"
    )


    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()