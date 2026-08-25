"""
FixtureIQ Stage 6.4.2

Integrated Backtest

Compares:

1. Stage 5 Outcome Model
   Home / Draw / Away probabilities

2. Stage 6 Poisson Model
   Expected goals -> scoreline probabilities
   -> Home / Draw / Away probabilities

Validation:
    2024/25

Locked:
    2025/26

No retraining is performed.
No random shuffling is used.
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
    / "integrated_backtest_metrics.json"
)


# -------------------------------------------------
# Configuration
# -------------------------------------------------

VALIDATION_SEASON = "2024/25"

MAX_GOALS = 10


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
# Find result column
# -------------------------------------------------

def find_result_column(df):

    candidates = [
        "FTR",
        "Result",
        "Outcome",
        "result"
    ]


    for column in candidates:

        if column in df.columns:

            return column


    raise ValueError(
        "Could not find match-result column. "
        "Expected one of: "
        +
        str(candidates)
    )


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
        f"Unknown match result: {value}"
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
# Convert Stage 5 probabilities to H/D/A
# -------------------------------------------------

def get_stage5_probabilities(
    model,
    X
):

    raw_probabilities = (
        model.predict_proba(X)[0]
    )


    classes = model.classes_


    probabilities = {
        "H": 0.0,
        "D": 0.0,
        "A": 0.0
    }


    for class_name, probability in zip(
        classes,
        raw_probabilities
    ):

        normalized = normalize_model_class(
            class_name
        )


        probabilities[normalized] = float(
            probability
        )


    return probabilities


# -------------------------------------------------
# Scoreline -> H/D/A probabilities
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
            "Scoreline probabilities sum to zero."
        )


    return np.array([

        home_probability / total,

        draw_probability / total,

        away_probability / total

    ])


# -------------------------------------------------
# Brier score
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
# Calibration
# -------------------------------------------------

def calibration_table(
    y_true,
    probabilities
):

    confidence = np.max(
        probabilities,
        axis=1
    )


    predicted_indices = np.argmax(
        probabilities,
        axis=1
    )


    class_to_index = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    actual_indices = np.array([

        class_to_index[value]

        for value in y_true

    ])


    correct = (
        predicted_indices
        ==
        actual_indices
    )


    bins = [
        (0.00, 0.40),
        (0.40, 0.50),
        (0.50, 0.60),
        (0.60, 0.70),
        (0.70, 0.80),
        (0.80, 1.01)
    ]


    rows = []


    for lower, upper in bins:

        mask = (
            (confidence >= lower)
            &
            (confidence < upper)
        )


        count = int(
            mask.sum()
        )


        if count == 0:

            continue


        rows.append({

            "confidence_range":
                f"{lower:.2f}-{upper:.2f}",

            "matches":
                count,

            "average_confidence":
                round(
                    float(
                        confidence[mask].mean()
                    ),
                    4
                ),

            "actual_accuracy":
                round(
                    float(
                        correct[mask].mean()
                    ),
                    4
                )

        })


    return rows


# -------------------------------------------------
# Main backtest
# -------------------------------------------------

def backtest():

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


    print(
        f"Result column: {result_column}"
    )


    # ---------------------------------------------
    # Validate required columns
    # ---------------------------------------------

    missing_outcome = [

        feature

        for feature in outcome_features

        if feature not in df.columns

    ]


    if missing_outcome:

        raise ValueError(
            "Missing Stage 5 features: "
            +
            str(missing_outcome)
        )


    missing_goal = [

        feature

        for feature in GOAL_FEATURES

        if feature not in df.columns

    ]


    if missing_goal:

        raise ValueError(
            "Missing Stage 6 goal features: "
            +
            str(missing_goal)
        )


    # ---------------------------------------------
    # Storage
    # ---------------------------------------------

    y_true = []


    stage5_probabilities = []


    poisson_probabilities = []


    stage5_predictions = []


    poisson_predictions = []


    probability_agreements = []


    probability_differences = []


    # ---------------------------------------------
    # Match-by-match prediction
    # ---------------------------------------------

    for _, match in df.iterrows():


        actual = normalize_result(
            match[result_column]
        )


        # Stage 5 features

        outcome_X = pd.DataFrame(
            [
                match[outcome_features]
            ]
        )


        # Stage 6 features

        goal_X = pd.DataFrame(
            [
                match[GOAL_FEATURES]
            ]
        )


        # -----------------------------------------
        # Stage 5 prediction
        # -----------------------------------------

        stage5 = (
            get_stage5_probabilities(
                outcome_model,
                outcome_X
            )
        )


        stage5_array = np.array([

            stage5["H"],
            stage5["D"],
            stage5["A"]

        ])


        # -----------------------------------------
        # Stage 6 lambda prediction
        # -----------------------------------------

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


        # -----------------------------------------
        # Poisson scoreline model
        # -----------------------------------------

        score_matrix = (
            generate_score_matrix(

                home_lambda,

                away_lambda,

                max_goals=MAX_GOALS

            )
        )


        poisson_array = (
            scoreline_to_outcomes(
                score_matrix
            )
        )


        # -----------------------------------------
        # Store
        # -----------------------------------------

        y_true.append(actual)


        stage5_probabilities.append(
            stage5_array
        )


        poisson_probabilities.append(
            poisson_array
        )


        stage5_predictions.append(
            np.argmax(stage5_array)
        )


        poisson_predictions.append(
            np.argmax(poisson_array)
        )


        probability_agreements.append(
            np.argmax(stage5_array)
            ==
            np.argmax(poisson_array)
        )


        probability_differences.append(

            np.abs(
                stage5_array
                -
                poisson_array
            ).mean()

        )


    # ---------------------------------------------
    # Convert arrays
    # ---------------------------------------------

    stage5_probabilities = np.array(
        stage5_probabilities
    )


    poisson_probabilities = np.array(
        poisson_probabilities
    )


    y_true = np.array(
        y_true
    )


    # ---------------------------------------------
    # Actual labels for sklearn
    # ---------------------------------------------

    label_to_index = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    y_indices = np.array([

        label_to_index[value]

        for value in y_true

    ])


    class_labels = [
        "H",
        "D",
        "A"
    ]


    # ---------------------------------------------
    # Stage 5 metrics
    # ---------------------------------------------

    stage5_predictions_index = (
        np.argmax(
            stage5_probabilities,
            axis=1
        )
    )


    stage5_accuracy = accuracy_score(
        y_indices,
        stage5_predictions_index
    )


    stage5_log_loss = log_loss(
        y_indices,
        stage5_probabilities,
        labels=[0, 1, 2]
    )


    stage5_brier = (
        multiclass_brier_score(
            y_true,
            stage5_probabilities
        )
    )


    # ---------------------------------------------
    # Poisson metrics
    # ---------------------------------------------

    poisson_predictions_index = (
        np.argmax(
            poisson_probabilities,
            axis=1
        )
    )


    poisson_accuracy = accuracy_score(
        y_indices,
        poisson_predictions_index
    )


    poisson_log_loss = log_loss(
        y_indices,
        poisson_probabilities,
        labels=[0, 1, 2]
    )


    poisson_brier = (
        multiclass_brier_score(
            y_true,
            poisson_probabilities
        )
    )


    # ---------------------------------------------
    # Agreement
    # ---------------------------------------------

    agreement_rate = (
        np.mean(
            probability_agreements
        )
    )


    average_probability_difference = (
        np.mean(
            probability_differences
        )
    )


    # ---------------------------------------------
    # Calibration
    # ---------------------------------------------

    stage5_calibration = (
        calibration_table(
            y_true,
            stage5_probabilities
        )
    )


    poisson_calibration = (
        calibration_table(
            y_true,
            poisson_probabilities
        )
    )


    # ---------------------------------------------
    # Average probabilities
    # ---------------------------------------------

    stage5_average_probabilities = (
        stage5_probabilities.mean(
            axis=0
        )
    )


    poisson_average_probabilities = (
        poisson_probabilities.mean(
            axis=0
        )
    )


    # ---------------------------------------------
    # Final report
    # ---------------------------------------------

    report = {

        "validation_season":
            VALIDATION_SEASON,


        "matches":
            len(df),


        "stage5_outcome_model": {

            "accuracy":
                round(
                    float(stage5_accuracy),
                    4
                ),

            "log_loss":
                round(
                    float(stage5_log_loss),
                    4
                ),

            "brier_score":
                round(
                    float(stage5_brier),
                    4
                ),

            "average_probabilities": {

                "home":
                    round(
                        float(
                            stage5_average_probabilities[0]
                        ),
                        4
                    ),

                "draw":
                    round(
                        float(
                            stage5_average_probabilities[1]
                        ),
                        4
                    ),

                "away":
                    round(
                        float(
                            stage5_average_probabilities[2]
                        ),
                        4
                    )

            },

            "calibration":
                stage5_calibration

        },


        "stage6_poisson_model": {

            "accuracy":
                round(
                    float(poisson_accuracy),
                    4
                ),

            "log_loss":
                round(
                    float(poisson_log_loss),
                    4
                ),

            "brier_score":
                round(
                    float(poisson_brier),
                    4
                ),

            "average_probabilities": {

                "home":
                    round(
                        float(
                            poisson_average_probabilities[0]
                        ),
                        4
                    ),

                "draw":
                    round(
                        float(
                            poisson_average_probabilities[1]
                        ),
                        4
                    ),

                "away":
                    round(
                        float(
                            poisson_average_probabilities[2]
                        ),
                        4
                    )

            },

            "calibration":
                poisson_calibration

        },


        "model_comparison": {

            "outcome_model_better_accuracy":
                (
                    "stage5"
                    if stage5_accuracy
                    >
                    poisson_accuracy

                    else
                    "stage6_poisson"
                ),

            "better_log_loss":
                (
                    "stage5"
                    if stage5_log_loss
                    <
                    poisson_log_loss

                    else
                    "stage6_poisson"
                ),

            "better_brier_score":
                (
                    "stage5"
                    if stage5_brier
                    <
                    poisson_brier

                    else
                    "stage6_poisson"
                ),

            "prediction_agreement_rate":
                round(
                    float(
                        agreement_rate
                    ),
                    4
                ),

            "average_probability_difference":
                round(
                    float(
                        average_probability_difference
                    ),
                    4
                )

        }

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
        "\nStage 6.4.2 Integrated Backtest"
    )

    print(
        "================================"
    )


    print("\nStage 5 Outcome Model")

    print(
        f"Accuracy : {stage5_accuracy:.4f}"
    )

    print(
        f"Log Loss : {stage5_log_loss:.4f}"
    )

    print(
        f"Brier    : {stage5_brier:.4f}"
    )


    print("\nStage 6 Poisson Model")

    print(
        f"Accuracy : {poisson_accuracy:.4f}"
    )

    print(
        f"Log Loss : {poisson_log_loss:.4f}"
    )

    print(
        f"Brier    : {poisson_brier:.4f}"
    )


    print("\nModel Agreement")

    print(
        f"Agreement rate: "
        f"{agreement_rate:.4f}"
    )


    print(
        f"Average probability difference: "
        f"{average_probability_difference:.4f}"
    )


    print(
        "\nSaved:"
    )

    print(
        OUTPUT_FILE
    )


# -------------------------------------------------
# Entry point
# -------------------------------------------------

if __name__ == "__main__":

    backtest()