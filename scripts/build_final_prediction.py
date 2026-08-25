"""
FixtureIQ Stage 6.4.1

Integrated Final Prediction Layer

Combines:

1. Stage 5 outcome model
   - Home / Draw / Away probabilities

2. Stage 6 goal models
   - Expected home goals
   - Expected away goals

3. Stage 6 Poisson scoreline engine
   - Scoreline probability matrix
   - Top likely scorelines

4. Consistency analysis
   - Convert scoreline probabilities into
     Home / Draw / Away probabilities

Important:
    We do NOT arbitrarily blend Stage 5 and
    scoreline-derived outcome probabilities yet.

    Calibration and validation must determine
    whether a future blend is justified.

Validation season:
    2024/25

Locked final test:
    2025/26
"""


from pathlib import Path
import sys
import json


import pandas as pd
import numpy as np
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
    / "final_prediction_sample.json"
)


# -------------------------------------------------
# Configuration
# -------------------------------------------------

VALIDATION_SEASON = "2024/25"

MAX_GOALS = 10

TOP_SCORELINES = 5


# -------------------------------------------------
# Stage 6 goal-model features
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


    # Support either:
    #
    # ["feature1", "feature2"]
    #
    # or:
    #
    # {"features": [...]}

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
# Normalize outcome class name
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

        return "home_win"


    if text in [
        "d",
        "draw",
        "x",
        "0"
    ]:

        return "draw"


    if text in [
        "a",
        "away",
        "awaywin",
        "away_win",
        "2"
    ]:

        return "away_win"


    raise ValueError(
        f"Unsupported outcome class: {value}"
    )


# -------------------------------------------------
# Extract Stage 5 probabilities
# -------------------------------------------------

def get_outcome_probabilities(
    outcome_model,
    X
):

    probabilities = (
        outcome_model
        .predict_proba(X)[0]
    )


    classes = (
        outcome_model
        .classes_
    )


    result = {
        "home_win": 0.0,
        "draw": 0.0,
        "away_win": 0.0
    }


    for class_name, probability in zip(
        classes,
        probabilities
    ):

        normalized = normalize_outcome_class(
            class_name
        )

        result[normalized] = float(
            probability
        )


    return result


# -------------------------------------------------
# Convert scoreline matrix to H/D/A
# -------------------------------------------------

def derive_outcome_probabilities(
    score_matrix
):

    home_win = score_matrix.loc[
        score_matrix["HomeGoals"]
        >
        score_matrix["AwayGoals"],
        "Probability"
    ].sum()


    draw = score_matrix.loc[
        score_matrix["HomeGoals"]
        ==
        score_matrix["AwayGoals"],
        "Probability"
    ].sum()


    away_win = score_matrix.loc[
        score_matrix["HomeGoals"]
        <
        score_matrix["AwayGoals"],
        "Probability"
    ].sum()


    total = (
        home_win
        +
        draw
        +
        away_win
    )


    if total <= 0:

        raise ValueError(
            "Scoreline probability total is zero."
        )


    return {

        "home_win":
            float(home_win / total),

        "draw":
            float(draw / total),

        "away_win":
            float(away_win / total)

    }


# -------------------------------------------------
# Consistency comparison
# -------------------------------------------------

def calculate_probability_gaps(
    outcome_probabilities,
    scoreline_probabilities
):

    return {

        "home_win_gap":

            round(
                outcome_probabilities["home_win"]
                -
                scoreline_probabilities["home_win"],
                4
            ),

        "draw_gap":

            round(
                outcome_probabilities["draw"]
                -
                scoreline_probabilities["draw"],
                4
            ),

        "away_win_gap":

            round(
                outcome_probabilities["away_win"]
                -
                scoreline_probabilities["away_win"],
                4
            )

    }


# -------------------------------------------------
# Build prediction
# -------------------------------------------------

def build_prediction(
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
    # Validate features
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
    # Build feature vectors
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
    # Stage 5 outcome probabilities
    # ---------------------------------------------

    outcome_probabilities = (
        get_outcome_probabilities(
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


    # Safety guard

    home_lambda = max(
        0.0,
        home_lambda
    )


    away_lambda = max(
        0.0,
        away_lambda
    )


    # ---------------------------------------------
    # Scoreline matrix
    # ---------------------------------------------

    score_matrix = generate_score_matrix(

        home_lambda,

        away_lambda,

        max_goals=MAX_GOALS

    )


    # ---------------------------------------------
    # Scoreline-derived outcomes
    # ---------------------------------------------

    scoreline_outcomes = (
        derive_outcome_probabilities(
            score_matrix
        )
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


    # ---------------------------------------------
    # Predicted score
    # ---------------------------------------------

    predicted_score = (
        likely_scorelines[0]["score"]
    )


    # ---------------------------------------------
    # Probability gaps
    # ---------------------------------------------

    probability_gaps = (
        calculate_probability_gaps(

            outcome_probabilities,

            scoreline_outcomes

        )
    )


    # ---------------------------------------------
    # Probability sums
    # ---------------------------------------------

    outcome_probability_sum = sum(
        outcome_probabilities.values()
    )


    scoreline_probability_sum = sum(
        scoreline_outcomes.values()
    )


    # ---------------------------------------------
    # Final object
    # ---------------------------------------------

    prediction = {

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


        "probabilities": {

            "home_win":
                round(
                    outcome_probabilities[
                        "home_win"
                    ],
                    4
                ),

            "draw":
                round(
                    outcome_probabilities[
                        "draw"
                    ],
                    4
                ),

            "away_win":
                round(
                    outcome_probabilities[
                        "away_win"
                    ],
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
                )

        },


        "predicted_score":
            predicted_score,


        "likely_scorelines":
            likely_scorelines,


        "scoreline_derived_probabilities": {

            "home_win":
                round(
                    scoreline_outcomes[
                        "home_win"
                    ],
                    4
                ),

            "draw":
                round(
                    scoreline_outcomes[
                        "draw"
                    ],
                    4
                ),

            "away_win":
                round(
                    scoreline_outcomes[
                        "away_win"
                    ],
                    4
                )

        },


        "probability_gaps":
            probability_gaps,


        "validation_checks": {

            "stage5_probability_sum":
                round(
                    outcome_probability_sum,
                    6
                ),

            "scoreline_probability_sum":
                round(
                    scoreline_probability_sum,
                    6
                ),

            "expected_goals_non_negative":
                (
                    home_lambda >= 0
                    and
                    away_lambda >= 0
                )

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
            "No validation matches found."
        )


    # Use first validation fixture
    # as an integration test.

    match = validation_df.iloc[0]


    print(
        "\nTesting fixture:"
    )


    print(
        f"{match['HomeTeam']} "
        f"vs "
        f"{match['AwayTeam']}"
    )


    prediction = build_prediction(
        match
    )


    print(
        "\nFinal Prediction Layer"
    )

    print(
        "----------------------"
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