"""
FixtureIQ Stage 6.5.3 + 6.5.4 + 6.5.5

FINAL STAGE 6 EVALUATION

6.5.3
------
Reproduce the frozen 30/70 validation result
on 2024/25.

Expected approximately:
    Accuracy : 0.5316
    Log Loss : 0.9965
    Brier    : 0.5962


6.5.4
------
Run the exact same frozen pipeline on
the untouched 2025/26 season.

NO tuning.
NO retraining.
NO weight changes.


6.5.5
------
Generate final evaluation:

- Accuracy
- Log Loss
- Brier Score
- Calibration
- Confusion Matrix
- Scoreline exact accuracy
- Scoreline top-3 accuracy
- Scoreline top-5 accuracy
- Average probability assigned to actual score
- Average expected goals
- Model agreement information

Frozen probability rule:

    30% Stage 5
    70% Stage 6

2024/25 = validation
2025/26 = final test
"""


from pathlib import Path
import sys
import json

import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    confusion_matrix
)


# =================================================
# PROJECT ROOT
# =================================================

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.append(str(BASE_DIR))


from ml.models.scoreline_model import (
    generate_score_matrix,
    get_top_scorelines
)


# =================================================
# PATHS
# =================================================

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
    / "stage6_final_evaluation.json"
)


# =================================================
# FROZEN CONFIGURATION
# =================================================

STAGE5_WEIGHT = 0.30

STAGE6_WEIGHT = 0.70

MAX_GOALS = 10

TOP_SCORELINES = 5


VALIDATION_SEASON = "2024/25"

FINAL_TEST_SEASON = "2025/26"


# Expected validation results from 6.4.3

EXPECTED_VALIDATION = {

    "accuracy": 0.5316,

    "log_loss": 0.9965,

    "brier_score": 0.5962

}


# =================================================
# STAGE 6 GOAL FEATURES
# =================================================

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


# =================================================
# LOAD MODELS
# =================================================

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


# =================================================
# LOAD STAGE 5 FEATURES
# =================================================

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


# =================================================
# LOAD DATA
# =================================================

def load_data():

    df = pd.read_csv(
        DATA_FILE
    )


    if "Season" not in df.columns:

        raise ValueError(
            "Season column is missing."
        )


    if "FTR" not in df.columns:

        raise ValueError(
            "FTR column is missing."
        )


    if "FTHG" not in df.columns:

        raise ValueError(
            "FTHG column is missing."
        )


    if "FTAG" not in df.columns:

        raise ValueError(
            "FTAG column is missing."
        )


    if "Date" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"]
        )

        df = (
            df
            .sort_values("Date")
            .reset_index(drop=True)
        )


    return df


# =================================================
# NORMALIZE RESULT
# =================================================

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
        f"Unknown result value: {value}"
    )


# =================================================
# STAGE 5 PROBABILITIES
# =================================================

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

        normalized = normalize_result(
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


# =================================================
# POISSON OUTCOME PROBABILITIES
# =================================================

def get_poisson_probabilities(
    home_lambda,
    away_lambda
):

    score_matrix = generate_score_matrix(

        home_lambda,

        away_lambda,

        max_goals=MAX_GOALS

    )


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
            "Poisson outcome probabilities sum to zero."
        )


    return np.array([

        home_probability / total,

        draw_probability / total,

        away_probability / total

    ])


# =================================================
# BRIER SCORE
# =================================================

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


# =================================================
# CALIBRATION
# =================================================

def calibration_table(
    y_true,
    probabilities
):

    confidence = np.max(
        probabilities,
        axis=1
    )


    predictions = np.argmax(
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
        predictions
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


# =================================================
# CONFUSION MATRIX
# =================================================

def build_confusion_matrix(
    y_true,
    probabilities
):

    labels = [
        "H",
        "D",
        "A"
    ]


    class_to_index = {

        "H": 0,
        "D": 1,
        "A": 2

    }


    y_true_indices = np.array([

        class_to_index[value]

        for value in y_true

    ])


    y_pred_indices = np.argmax(
        probabilities,
        axis=1
    )


    matrix = confusion_matrix(

        y_true_indices,

        y_pred_indices,

        labels=[0, 1, 2]

    )


    return {

        "labels":
            labels,

        "matrix":
            matrix.tolist()

    }


# =================================================
# RUN ONE SEASON
# =================================================

def evaluate_season(
    df,
    season,
    outcome_model,
    home_goal_model,
    away_goal_model,
    outcome_features
):

    season_df = df[
        df["Season"]
        ==
        season
    ].copy()


    if len(season_df) == 0:

        raise ValueError(

            f"No matches found for {season}. "
            "The final test cannot be performed."

        )


    print(
        f"\nEvaluating {season}..."
    )


    print(
        f"Matches: {len(season_df)}"
    )


    y_true = []


    final_probabilities = []


    stage5_probabilities = []


    stage6_probabilities = []


    exact_score_hits = 0

    top3_score_hits = 0

    top5_score_hits = 0


    actual_score_probabilities = []


    expected_home_goals = []

    expected_away_goals = []


    agreement_count = 0


    for _, match in season_df.iterrows():

        actual_result = normalize_result(
            match["FTR"]
        )


        actual_home_goals = int(
            match["FTHG"]
        )


        actual_away_goals = int(
            match["FTAG"]
        )


        # -----------------------------------------
        # Feature vectors
        # -----------------------------------------

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


        # -----------------------------------------
        # Stage 5
        # -----------------------------------------

        stage5 = (
            get_stage5_probabilities(
                outcome_model,
                outcome_X
            )
        )


        # -----------------------------------------
        # Stage 6 lambdas
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


        expected_home_goals.append(
            home_lambda
        )


        expected_away_goals.append(
            away_lambda
        )


        # -----------------------------------------
        # Poisson score matrix
        # -----------------------------------------

        score_matrix = generate_score_matrix(

            home_lambda,

            away_lambda,

            max_goals=MAX_GOALS

        )


        # -----------------------------------------
        # Stage 6 H/D/A
        # -----------------------------------------

        stage6 = (
            get_poisson_probabilities(

                home_lambda,

                away_lambda

            )
        )


        # -----------------------------------------
        # Frozen 30/70 blend
        # -----------------------------------------

        final = (

            STAGE5_WEIGHT
            *
            stage5

            +

            STAGE6_WEIGHT
            *
            stage6

        )


        final = (
            final
            /
            final.sum()
        )


        # -----------------------------------------
        # Store outcome data
        # -----------------------------------------

        y_true.append(
            actual_result
        )


        stage5_probabilities.append(
            stage5
        )


        stage6_probabilities.append(
            stage6
        )


        final_probabilities.append(
            final
        )


        # -----------------------------------------
        # Model agreement
        # -----------------------------------------

        if (
            np.argmax(stage5)
            ==
            np.argmax(stage6)
        ):

            agreement_count += 1


        # -----------------------------------------
        # Scoreline predictions
        # -----------------------------------------

        top_scores = get_top_scorelines(

            score_matrix,

            top_n=TOP_SCORELINES

        )


        predicted_scores = [

            (
                int(row["HomeGoals"]),

                int(row["AwayGoals"])

            )

            for _, row
            in top_scores.iterrows()

        ]


        actual_score = (

            actual_home_goals,

            actual_away_goals

        )


        if (
            len(predicted_scores) > 0
            and
            predicted_scores[0]
            ==
            actual_score
        ):

            exact_score_hits += 1


        if actual_score in predicted_scores[:3]:

            top3_score_hits += 1


        if actual_score in predicted_scores[:5]:

            top5_score_hits += 1


        # -----------------------------------------
        # Actual score probability
        # -----------------------------------------

        probability_row = score_matrix[

            (
                score_matrix["HomeGoals"]
                ==
                actual_home_goals
            )

            &

            (
                score_matrix["AwayGoals"]
                ==
                actual_away_goals
            )

        ]


        if len(probability_row) > 0:

            actual_score_probability = float(

                probability_row.iloc[0][
                    "ProbabilityPercent"
                ]

            ) / 100.0


            actual_score_probabilities.append(
                actual_score_probability
            )


    # =================================================
    # Convert arrays
    # =================================================

    y_true = np.array(
        y_true
    )


    final_probabilities = np.array(
        final_probabilities
    )


    stage5_probabilities = np.array(
        stage5_probabilities
    )


    stage6_probabilities = np.array(
        stage6_probabilities
    )


    # =================================================
    # Labels
    # =================================================

    label_to_index = {

        "H": 0,
        "D": 1,
        "A": 2

    }


    y_indices = np.array([

        label_to_index[value]

        for value in y_true

    ])


    # =================================================
    # FINAL METRICS
    # =================================================

    predictions = np.argmax(

        final_probabilities,

        axis=1

    )


    accuracy = accuracy_score(

        y_indices,

        predictions

    )


    logloss = log_loss(

        y_indices,

        final_probabilities,

        labels=[0, 1, 2]

    )


    brier = multiclass_brier_score(

        y_true,

        final_probabilities

    )


    # =================================================
    # SCORELINE METRICS
    # =================================================

    total_matches = len(
        season_df
    )


    exact_accuracy = (
        exact_score_hits
        /
        total_matches
    )


    top3_accuracy = (
        top3_score_hits
        /
        total_matches
    )


    top5_accuracy = (
        top5_score_hits
        /
        total_matches
    )


    # =================================================
    # MODEL AGREEMENT
    # =================================================

    agreement_rate = (

        agreement_count
        /
        total_matches

    )


    # =================================================
    # AVERAGES
    # =================================================

    average_actual_score_probability = (

        float(
            np.mean(
                actual_score_probabilities
            )
        )

        if actual_score_probabilities

        else 0.0

    )


    average_home_lambda = float(
        np.mean(
            expected_home_goals
        )
    )


    average_away_lambda = float(
        np.mean(
            expected_away_goals
        )
    )


    # =================================================
    # FINAL REPORT
    # =================================================

    result = {

        "season":
            season,

        "matches":
            total_matches,


        "probability_metrics": {

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

        },


        "scoreline_metrics": {

            "exact_score_accuracy":
                round(
                    float(exact_accuracy),
                    4
                ),

            "top3_score_accuracy":
                round(
                    float(top3_accuracy),
                    4
                ),

            "top5_score_accuracy":
                round(
                    float(top5_accuracy),
                    4
                ),

            "average_actual_score_probability":
                round(
                    average_actual_score_probability,
                    4
                )

        },


        "expected_goals": {

            "average_home_lambda":
                round(
                    average_home_lambda,
                    4
                ),

            "average_away_lambda":
                round(
                    average_away_lambda,
                    4
                ),

            "average_total_lambda":
                round(
                    average_home_lambda
                    +
                    average_away_lambda,
                    4
                )

        },


        "model_agreement": {

            "stage5_stage6_agreement_rate":
                round(
                    float(agreement_rate),
                    4
                )

        },


        "calibration":
            calibration_table(

                y_true,

                final_probabilities

            ),


        "confusion_matrix":
            build_confusion_matrix(

                y_true,

                final_probabilities

            )

    }


    return result


# =================================================
# VALIDATION REPRODUCTION CHECK
# =================================================

def validation_reproduction_check(
    validation_result
):

    actual_accuracy = (
        validation_result[
            "probability_metrics"
        ][
            "accuracy"
        ]
    )


    actual_logloss = (
        validation_result[
            "probability_metrics"
        ][
            "log_loss"
        ]
    )


    actual_brier = (
        validation_result[
            "probability_metrics"
        ][
            "brier_score"
        ]
    )


    # Allow tiny numerical differences.

    tolerance = 0.0002


    accuracy_match = bool(

        abs(
            actual_accuracy
            -
            EXPECTED_VALIDATION[
                "accuracy"
            ]
        )
        <= tolerance

    )


    logloss_match = bool(

        abs(
            actual_logloss
            -
            EXPECTED_VALIDATION[
                "log_loss"
            ]
        )
        <= tolerance

    )


    brier_match = bool(

        abs(
            actual_brier
            -
            EXPECTED_VALIDATION[
                "brier_score"
            ]
        )
        <= tolerance

    )


    return {

        "expected":

            EXPECTED_VALIDATION,

        "actual": {

            "accuracy":
                actual_accuracy,

            "log_loss":
                actual_logloss,

            "brier_score":
                actual_brier

        },

        "accuracy_match":
            accuracy_match,

        "log_loss_match":
            logloss_match,

        "brier_match":
            brier_match,

        "reproduction_success":
            bool(

                accuracy_match
                and
                logloss_match
                and
                brier_match

            )

    }


# =================================================
# MAIN
# =================================================

def main():

    print(
        "=============================================="
    )

    print(
        "FixtureIQ FINAL STAGE 6 EVALUATION"
    )

    print(
        "=============================================="
    )


    print(
        "\nFrozen configuration:"
    )


    print(
        f"Stage 5 weight: "
        f"{STAGE5_WEIGHT:.0%}"
    )


    print(
        f"Stage 6 weight: "
        f"{STAGE6_WEIGHT:.0%}"
    )


    print(
        f"Validation: "
        f"{VALIDATION_SEASON}"
    )


    print(
        f"Final test: "
        f"{FINAL_TEST_SEASON}"
    )


    # =================================================
    # LOAD
    # =================================================

    models = load_models()


    (
        outcome_model,
        home_goal_model,
        away_goal_model
    ) = models


    outcome_features = (
        load_outcome_features()
    )


    df = load_data()


    # =================================================
    # CHECK FEATURES
    # =================================================

    missing_outcome_features = [

        feature

        for feature in outcome_features

        if feature not in df.columns

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

        if feature not in df.columns

    ]


    if missing_goal_features:

        raise ValueError(

            "Missing Stage 6 features: "
            +
            str(missing_goal_features)

        )


    # =================================================
    # 6.5.3
    # VALIDATION REPRODUCTION
    # =================================================

    print(
        "\n"
        "=============================================="
    )

    print(
        "6.5.3 — 2024/25 VALIDATION REPRODUCTION"
    )

    print(
        "=============================================="
    )


    validation_result = evaluate_season(

        df,

        VALIDATION_SEASON,

        outcome_model,

        home_goal_model,

        away_goal_model,

        outcome_features

    )


    reproduction = (
        validation_reproduction_check(
            validation_result
        )
    )


    print(
        "\nValidation result:"
    )


    print(
        json.dumps(
            validation_result[
                "probability_metrics"
            ],
            indent=4
        )
    )


    print(
        "\nReproduction check:"
    )


    print(
        json.dumps(
            reproduction,
            indent=4
        )
    )


    if not reproduction[
        "reproduction_success"
    ]:

        raise RuntimeError(

            "2024/25 reproduction FAILED. "
            "Do not continue to the final test. "
            "The frozen pipeline does not reproduce "
            "the selected validation result."

        )


    print(
        "\n2024/25 reproduction PASSED."
    )


    # =================================================
    # 6.5.4
    # FINAL 2025/26 TEST
    # =================================================

    print(
        "\n"
        "=============================================="
    )

    print(
        "6.5.4 — 2025/26 FINAL TEST"
    )

    print(
        "=============================================="
    )


    print(
        "\nIMPORTANT:"
    )

    print(
        "The model is frozen."
    )

    print(
        "No tuning will be performed."
    )

    print(
        "No weights will be changed."
    )

    print(
        "No retraining will be performed."
    )


    final_test_result = evaluate_season(

        df,

        FINAL_TEST_SEASON,

        outcome_model,

        home_goal_model,

        away_goal_model,

        outcome_features

    )


    print(
        "\n2025/26 final-test probability metrics:"
    )


    print(
        json.dumps(
            final_test_result[
                "probability_metrics"
            ],
            indent=4
        )
    )


    # =================================================
    # 6.5.5
    # FINAL EVALUATION REPORT
    # =================================================

    print(
        "\n"
        "=============================================="
    )

    print(
        "6.5.5 — FINAL EVALUATION"
    )

    print(
        "=============================================="
    )


    final_report = {

        "stage":
            "Stage 6",

        "evaluation_status":
            "completed",


        "frozen_model": {

            "stage5_weight":
                STAGE5_WEIGHT,

            "stage6_weight":
                STAGE6_WEIGHT,

            "weights_locked":
                True

        },


        "seasons": {

            "validation":
                VALIDATION_SEASON,

            "final_test":
                FINAL_TEST_SEASON

        },


        "stage_6_5_3_validation_reproduction":
            reproduction,


        "validation_2024_25":
            validation_result,


        "final_test_2025_26":
            final_test_result

    }


    # =================================================
    # SAVE
    # =================================================

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            final_report,
            f,
            indent=4
        )


    # =================================================
    # FINAL SUMMARY
    # =================================================

    print(
        "\n"
        "=============================================="
    )

    print(
        "FINAL STAGE 6 SUMMARY"
    )

    print(
        "=============================================="
    )


    print(
        "\n2024/25 Validation:"
    )


    print(
        f"Accuracy : "
        f"{validation_result['probability_metrics']['accuracy']:.4f}"
    )


    print(
        f"Log Loss : "
        f"{validation_result['probability_metrics']['log_loss']:.4f}"
    )


    print(
        f"Brier    : "
        f"{validation_result['probability_metrics']['brier_score']:.4f}"
    )


    print(
        "\n2025/26 Final Test:"
    )


    print(
        f"Accuracy : "
        f"{final_test_result['probability_metrics']['accuracy']:.4f}"
    )


    print(
        f"Log Loss : "
        f"{final_test_result['probability_metrics']['log_loss']:.4f}"
    )


    print(
        f"Brier    : "
        f"{final_test_result['probability_metrics']['brier_score']:.4f}"
    )


    print(
        "\n2025/26 Scoreline:"
    )


    print(
        f"Exact : "
        f"{final_test_result['scoreline_metrics']['exact_score_accuracy']:.4f}"
    )


    print(
        f"Top-3 : "
        f"{final_test_result['scoreline_metrics']['top3_score_accuracy']:.4f}"
    )


    print(
        f"Top-5 : "
        f"{final_test_result['scoreline_metrics']['top5_score_accuracy']:.4f}"
    )


    print(
        "\nSaved:"
    )


    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()