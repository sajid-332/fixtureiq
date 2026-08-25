"""
FixtureIQ Stage 6.6

FINAL GOAL + SCORELINE ANALYSIS

This script performs a detailed analysis of the frozen
Stage 6 prediction system on the untouched 2025/26
final test season.

IMPORTANT:

- No retraining
- No tuning
- No feature changes
- No probability-weight changes
- No model selection

Frozen probability rule:

    30% Stage 5
    70% Stage 6

Analysis includes:

1. Outcome accuracy
2. Per-class precision / recall / F1
3. Confusion matrix
4. Predicted class distribution
5. Confidence distribution
6. Calibration
7. Expected-goal MAE
8. Expected-goal RMSE
9. Expected-goal bias
10. Home/away goal comparison
11. Exact-score accuracy
12. Top-3 scoreline accuracy
13. Top-5 scoreline accuracy
14. Actual-score probability
15. Scoreline rank analysis
16. Model agreement
17. Final diagnostic summary
"""


from pathlib import Path
import sys
import json
import math

import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    log_loss
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
    / "stage6_detailed_final_analysis.json"
)


# =================================================
# FROZEN CONFIGURATION
# =================================================

STAGE5_WEIGHT = 0.30

STAGE6_WEIGHT = 0.70

FINAL_TEST_SEASON = "2025/26"

MAX_GOALS = 10

TOP_SCORELINES = 5


# =================================================
# GOAL FEATURES
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
# LOAD FEATURE COLUMNS
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
        f"Unknown result: {value}"
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

def poisson_outcomes(
    score_matrix
):

    home = score_matrix.loc[

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


    away = score_matrix.loc[

        score_matrix["HomeGoals"]
        <
        score_matrix["AwayGoals"],

        "Probability"

    ].sum()


    total = home + draw + away


    if total <= 0:

        raise ValueError(
            "Poisson probability total is zero."
        )


    return np.array([

        home / total,

        draw / total,

        away / total

    ])


# =================================================
# BRIER SCORE
# =================================================

def multiclass_brier(
    y_true,
    probabilities
):

    mapping = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    total = 0.0


    for actual, probability in zip(
        y_true,
        probabilities
    ):

        actual_index = mapping[actual]


        target = np.zeros(3)

        target[actual_index] = 1.0


        total += np.sum(
            (
                probability
                -
                target
            ) ** 2
        )


    return total / len(y_true)


# =================================================
# CALIBRATION
# =================================================

def calculate_calibration(
    y_true,
    probabilities
):

    mapping = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    actual = np.array([

        mapping[value]

        for value in y_true

    ])


    predictions = np.argmax(
        probabilities,
        axis=1
    )


    confidence = np.max(
        probabilities,
        axis=1
    )


    correct = (
        predictions
        ==
        actual
    )


    bins = [

        (0.00, 0.40),

        (0.40, 0.50),

        (0.50, 0.60),

        (0.60, 0.70),

        (0.70, 0.80),

        (0.80, 0.90),

        (0.90, 1.01)

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


        avg_confidence = float(
            confidence[mask].mean()
        )


        actual_accuracy = float(
            correct[mask].mean()
        )


        rows.append({

            "range":
                f"{lower:.2f}-{upper:.2f}",

            "matches":
                count,

            "average_confidence":
                round(
                    avg_confidence,
                    4
                ),

            "actual_accuracy":
                round(
                    actual_accuracy,
                    4
                ),

            "calibration_gap":
                round(
                    actual_accuracy
                    -
                    avg_confidence,
                    4
                )

        })


    # Expected Calibration Error

    ece = 0.0


    for row in rows:

        weight = (
            row["matches"]
            /
            len(y_true)
        )


        ece += (

            weight
            *
            abs(
                row["calibration_gap"]
            )

        )


    # Maximum calibration error

    mce = (

        max(
            [
                abs(
                    row["calibration_gap"]
                )

                for row in rows
            ]
        )

        if rows

        else 0.0

    )


    return {

        "expected_calibration_error":
            round(
                float(ece),
                4
            ),

        "maximum_calibration_error":
            round(
                float(mce),
                4
            ),

        "bins":
            rows

    }


# =================================================
# MAIN ANALYSIS
# =================================================

def main():

    print(
        "=============================================="
    )

    print(
        "FixtureIQ Stage 6.6"
    )

    print(
        "Detailed Goal + Scoreline Analysis"
    )

    print(
        "=============================================="
    )


    print(
        "\nFrozen model:"
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
        f"Final test: "
        f"{FINAL_TEST_SEASON}"
    )


    # =================================================
    # LOAD
    # =================================================

    (
        outcome_model,
        home_goal_model,
        away_goal_model
    ) = load_models()


    outcome_features = (
        load_outcome_features()
    )


    df = load_data()


    # =================================================
    # VALIDATE COLUMNS
    # =================================================

    required_columns = [

        "Season",
        "FTR",
        "FTHG",
        "FTAG"

    ]


    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"Missing required column: {column}"
            )


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
            "Missing Stage 6 features: "
            +
            str(missing_goal)
        )


    # =================================================
    # FINAL TEST DATA
    # =================================================

    test_df = df[
        df["Season"]
        ==
        FINAL_TEST_SEASON
    ].copy()


    if len(test_df) == 0:

        raise ValueError(
            "No 2025/26 matches found."
        )


    print(
        f"\nMatches analyzed: "
        f"{len(test_df)}"
    )


    # =================================================
    # STORAGE
    # =================================================

    y_true = []


    final_probabilities = []


    stage5_probabilities = []


    stage6_probabilities = []


    actual_home_goals = []

    actual_away_goals = []


    predicted_home_goals = []

    predicted_away_goals = []


    exact_score_hits = 0

    top3_hits = 0

    top5_hits = 0


    score_rank_values = []


    actual_score_probability = []


    scoreline_entropy = []


    model_agreement_count = 0


    # Track predicted and actual score distributions

    predicted_score_counts = {}

    actual_score_counts = {}


    # =================================================
    # MATCH LOOP
    # =================================================

    for _, match in test_df.iterrows():

        actual_result = normalize_result(
            match["FTR"]
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


        # ---------------------------------------------
        # Feature vectors
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

        stage5 = (
            get_stage5_probabilities(
                outcome_model,
                outcome_X
            )
        )


        # ---------------------------------------------
        # Goal models
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
        # Score matrix
        # ---------------------------------------------

        score_matrix = generate_score_matrix(

            home_lambda,

            away_lambda,

            max_goals=MAX_GOALS

        )


        # ---------------------------------------------
        # Stage 6 probabilities
        # ---------------------------------------------

        stage6 = (
            poisson_outcomes(
                score_matrix
            )
        )


        # ---------------------------------------------
        # Frozen blend
        # ---------------------------------------------

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


        # ---------------------------------------------
        # Store
        # ---------------------------------------------

        y_true.append(
            actual_result
        )


        final_probabilities.append(
            final
        )


        stage5_probabilities.append(
            stage5
        )


        stage6_probabilities.append(
            stage6
        )


        actual_home_goals.append(
            actual_home
        )


        actual_away_goals.append(
            actual_away
        )


        predicted_home_goals.append(
            home_lambda
        )


        predicted_away_goals.append(
            away_lambda
        )


        # ---------------------------------------------
        # Model agreement
        # ---------------------------------------------

        if (
            np.argmax(stage5)
            ==
            np.argmax(stage6)
        ):

            model_agreement_count += 1


        # ---------------------------------------------
        # Top scorelines
        # ---------------------------------------------

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


        if (
            len(predicted_scores) > 0
            and
            predicted_scores[0]
            ==
            actual_score
        ):

            exact_score_hits += 1


        if actual_score in predicted_scores[:3]:

            top3_hits += 1


        if actual_score in predicted_scores[:5]:

            top5_hits += 1


        # ---------------------------------------------
        # Score rank of actual result
        # ---------------------------------------------

        all_scores = score_matrix.sort_values(

            "Probability",

            ascending=False

        ).reset_index(drop=True)


        matching_rows = all_scores[

            (
                all_scores["HomeGoals"]
                ==
                actual_home
            )

            &

            (
                all_scores["AwayGoals"]
                ==
                actual_away
            )

        ]


        if len(matching_rows) > 0:

            actual_probability = float(

                matching_rows.iloc[0][
                    "Probability"
                ]

            )


            rank = int(
                matching_rows.index[0]
            ) + 1


            score_rank_values.append(
                rank
            )


            actual_score_probability.append(
                actual_probability
            )


        # ---------------------------------------------
        # Scoreline entropy
        # ---------------------------------------------

        probabilities = (
            score_matrix["Probability"]
            .to_numpy()
        )


        probabilities = probabilities[
            probabilities > 0
        ]


        entropy = float(

            -np.sum(

                probabilities
                *
                np.log2(
                    probabilities
                )

            )

        )


        scoreline_entropy.append(
            entropy
        )


        # ---------------------------------------------
        # Score distributions
        # ---------------------------------------------

        top_predicted_score = (
            predicted_scores[0]
            if predicted_scores
            else None
        )


        if top_predicted_score is not None:

            score_key = (
                f"{top_predicted_score[0]}"
                f"-"
                f"{top_predicted_score[1]}"
            )


            predicted_score_counts[
                score_key
            ] = (

                predicted_score_counts.get(
                    score_key,
                    0
                )
                +
                1

            )


        actual_key = (
            f"{actual_home}"
            f"-"
            f"{actual_away}"
        )


        actual_score_counts[
            actual_key
        ] = (

            actual_score_counts.get(
                actual_key,
                0
            )
            +
            1

        )


    # =================================================
    # ARRAYS
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


    actual_home_goals = np.array(
        actual_home_goals
    )


    actual_away_goals = np.array(
        actual_away_goals
    )


    predicted_home_goals = np.array(
        predicted_home_goals
    )


    predicted_away_goals = np.array(
        predicted_away_goals
    )


    # =================================================
    # OUTCOME METRICS
    # =================================================

    mapping = {
        "H": 0,
        "D": 1,
        "A": 2
    }


    y_indices = np.array([

        mapping[value]

        for value in y_true

    ])


    predictions = np.argmax(
        final_probabilities,
        axis=1
    )


    accuracy = accuracy_score(

        y_indices,

        predictions

    )


    precision, recall, f1, support = (

        precision_recall_fscore_support(

            y_indices,

            predictions,

            labels=[0, 1, 2],

            zero_division=0

        )

    )


    outcome_logloss = log_loss(

        y_indices,

        final_probabilities,

        labels=[0, 1, 2]

    )


    outcome_brier = multiclass_brier(

        y_true,

        final_probabilities

    )


    # =================================================
    # CONFUSION MATRIX
    # =================================================

    matrix = confusion_matrix(

        y_indices,

        predictions,

        labels=[0, 1, 2]

    )


    # =================================================
    # GOAL METRICS
    # =================================================

    home_mae = mean_absolute_error(

        actual_home_goals,

        predicted_home_goals

    )


    away_mae = mean_absolute_error(

        actual_away_goals,

        predicted_away_goals

    )


    home_rmse = math.sqrt(

        mean_squared_error(

            actual_home_goals,

            predicted_home_goals

        )

    )


    away_rmse = math.sqrt(

        mean_squared_error(

            actual_away_goals,

            predicted_away_goals

        )

    )


    home_bias = float(

        np.mean(

            predicted_home_goals
            -
            actual_home_goals

        )

    )


    away_bias = float(

        np.mean(

            predicted_away_goals
            -
            actual_away_goals

        )

    )


    # =================================================
    # GOAL AVERAGES
    # =================================================

    average_actual_home = float(
        actual_home_goals.mean()
    )


    average_actual_away = float(
        actual_away_goals.mean()
    )


    average_predicted_home = float(
        predicted_home_goals.mean()
    )


    average_predicted_away = float(
        predicted_away_goals.mean()
    )


    # =================================================
    # SCORELINE METRICS
    # =================================================

    total_matches = len(test_df)


    exact_accuracy = (

        exact_score_hits
        /
        total_matches

    )


    top3_accuracy = (

        top3_hits
        /
        total_matches

    )


    top5_accuracy = (

        top5_hits
        /
        total_matches

    )


    average_actual_score_probability = (

        float(
            np.mean(
                actual_score_probability
            )
        )

        if actual_score_probability

        else 0.0

    )


    median_actual_score_rank = (

        float(
            np.median(
                score_rank_values
            )
        )

        if score_rank_values

        else 0.0

    )


    mean_actual_score_rank = (

        float(
            np.mean(
                score_rank_values
            )
        )

        if score_rank_values

        else 0.0

    )


    # =================================================
    # MODEL AGREEMENT
    # =================================================

    agreement_rate = (

        model_agreement_count
        /
        total_matches

    )


    # =================================================
    # CALIBRATION
    # =================================================

    calibration = calculate_calibration(

        y_true,

        final_probabilities

    )


    # =================================================
    # PREDICTED CLASS DISTRIBUTION
    # =================================================

    class_names = {
        0: "Home",
        1: "Draw",
        2: "Away"
    }


    predicted_class_counts = {}


    for index in range(3):

        predicted_class_counts[
            class_names[index]
        ] = int(

            np.sum(
                predictions == index
            )

        )


    actual_class_counts = {

        "Home":
            int(
                np.sum(
                    y_indices == 0
                )
            ),

        "Draw":
            int(
                np.sum(
                    y_indices == 1
                )
            ),

        "Away":
            int(
                np.sum(
                    y_indices == 2
                )
            )

    }


    # =================================================
    # TOP SCORE DISTRIBUTIONS
    # =================================================

    top_predicted_scores = sorted(

        predicted_score_counts.items(),

        key=lambda item:
        item[1],

        reverse=True

    )[:10]


    top_actual_scores = sorted(

        actual_score_counts.items(),

        key=lambda item:
        item[1],

        reverse=True

    )[:10]


    # =================================================
    # DIAGNOSTIC FLAGS
    # =================================================

    diagnostics = []


    # Goal bias

    if home_bias > 0.15:

        diagnostics.append(
            "Home goals are systematically over-predicted."
        )


    elif home_bias < -0.15:

        diagnostics.append(
            "Home goals are systematically under-predicted."
        )


    if away_bias > 0.15:

        diagnostics.append(
            "Away goals are systematically over-predicted."
        )


    elif away_bias < -0.15:

        diagnostics.append(
            "Away goals are systematically under-predicted."
        )


    # Draw prediction

    draw_recall = float(
        recall[1]
    )


    if draw_recall < 0.20:

        diagnostics.append(
            "Draw recall is weak on the final test season."
        )


    # Calibration

    if calibration[
        "expected_calibration_error"
    ] > 0.05:

        diagnostics.append(
            "Outcome probabilities show noticeable calibration error."
        )


    # Scoreline

    if exact_accuracy < 0.10:

        diagnostics.append(
            "Exact-score prediction is difficult and remains below 10%."
        )


    if top5_accuracy >= 0.40:

        diagnostics.append(
            "The scoreline model provides useful top-5 score coverage."
        )


    # Agreement

    if agreement_rate >= 0.85:

        diagnostics.append(
            "Stage 5 and Stage 6 generally agree on the leading outcome."
        )


    # Generalization

    diagnostics.append(
        "2025/26 results are treated as final out-of-sample evidence and are not used for tuning."
    )


    # =================================================
    # FINAL REPORT
    # =================================================

    report = {

        "stage":
            "6.6",

        "analysis":
            "Detailed final goal and scoreline analysis",


        "test_season":
            FINAL_TEST_SEASON,


        "matches":
            total_matches,


        "frozen_model": {

            "stage5_weight":
                STAGE5_WEIGHT,

            "stage6_weight":
                STAGE6_WEIGHT,

            "weights_locked":
                True

        },


        "outcome_performance": {

            "accuracy":
                round(
                    float(accuracy),
                    4
                ),

            "log_loss":
                round(
                    float(outcome_logloss),
                    4
                ),

            "brier_score":
                round(
                    float(outcome_brier),
                    4
                ),

            "classes": {

                "Home": {

                    "precision":
                        round(
                            float(precision[0]),
                            4
                        ),

                    "recall":
                        round(
                            float(recall[0]),
                            4
                        ),

                    "f1":
                        round(
                            float(f1[0]),
                            4
                        ),

                    "support":
                        int(support[0])

                },

                "Draw": {

                    "precision":
                        round(
                            float(precision[1]),
                            4
                        ),

                    "recall":
                        round(
                            float(recall[1]),
                            4
                        ),

                    "f1":
                        round(
                            float(f1[1]),
                            4
                        ),

                    "support":
                        int(support[1])

                },

                "Away": {

                    "precision":
                        round(
                            float(precision[2]),
                            4
                        ),

                    "recall":
                        round(
                            float(recall[2]),
                            4
                        ),

                    "f1":
                        round(
                            float(f1[2]),
                            4
                        ),

                    "support":
                        int(support[2])

                }

            }

        },


        "confusion_matrix": {

            "labels": [
                "Home",
                "Draw",
                "Away"
            ],

            "matrix":
                matrix.tolist()

        },


        "outcome_distribution": {

            "actual":
                actual_class_counts,

            "predicted":
                predicted_class_counts

        },


        "calibration":
            calibration,


        "expected_goals": {

            "actual_average": {

                "home":
                    round(
                        average_actual_home,
                        4
                    ),

                "away":
                    round(
                        average_actual_away,
                        4
                    ),

                "total":
                    round(
                        average_actual_home
                        +
                        average_actual_away,
                        4
                    )

            },


            "predicted_average": {

                "home":
                    round(
                        average_predicted_home,
                        4
                    ),

                "away":
                    round(
                        average_predicted_away,
                        4
                    ),

                "total":
                    round(
                        average_predicted_home
                        +
                        average_predicted_away,
                        4
                    )

            },


            "mae": {

                "home":
                    round(
                        float(home_mae),
                        4
                    ),

                "away":
                    round(
                        float(away_mae),
                        4
                    )

            },


            "rmse": {

                "home":
                    round(
                        float(home_rmse),
                        4
                    ),

                "away":
                    round(
                        float(away_rmse),
                        4
                    )

            },


            "bias": {

                "home":
                    round(
                        home_bias,
                        4
                    ),

                "away":
                    round(
                        away_bias,
                        4
                    )

            }

        },


        "scoreline_performance": {

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

            "average_probability_of_actual_score":
                round(
                    average_actual_score_probability,
                    4
                ),

            "mean_rank_of_actual_score":
                round(
                    mean_actual_score_rank,
                    2
                ),

            "median_rank_of_actual_score":
                round(
                    median_actual_score_rank,
                    2
                ),

            "average_scoreline_entropy_bits":
                round(
                    float(
                        np.mean(
                            scoreline_entropy
                        )
                    ),
                    4
                )

        },


        "scoreline_distributions": {

            "top_predicted_scorelines":
                [
                    {
                        "score":
                            score,

                        "matches":
                            int(count),

                        "frequency":
                            round(
                                count
                                /
                                total_matches,
                                4
                            )
                    }

                    for score, count
                    in top_predicted_scores
                ],


            "top_actual_scorelines":
                [
                    {
                        "score":
                            score,

                        "matches":
                            int(count),

                        "frequency":
                            round(
                                count
                                /
                                total_matches,
                                4
                            )
                    }

                    for score, count
                    in top_actual_scores
                ]

        },


        "model_agreement": {

            "stage5_stage6_agreement_rate":
                round(
                    float(agreement_rate),
                    4
                )

        },


        "diagnostics":
            diagnostics

    }


    # =================================================
    # SAVE
    # =================================================

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            report,
            f,
            indent=4
        )


    # =================================================
    # TERMINAL SUMMARY
    # =================================================

    print(
        "\n=============================================="
    )

    print(
        "STAGE 6.6 FINAL ANALYSIS"
    )

    print(
        "=============================================="
    )


    print(
        "\nOutcome Performance"
    )

    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Log Loss : {outcome_logloss:.4f}"
    )

    print(
        f"Brier    : {outcome_brier:.4f}"
    )


    print(
        "\nPer-Class Performance"
    )


    print(
        f"Home  -> "
        f"Precision {precision[0]:.4f}, "
        f"Recall {recall[0]:.4f}, "
        f"F1 {f1[0]:.4f}"
    )


    print(
        f"Draw  -> "
        f"Precision {precision[1]:.4f}, "
        f"Recall {recall[1]:.4f}, "
        f"F1 {f1[1]:.4f}"
    )


    print(
        f"Away  -> "
        f"Precision {precision[2]:.4f}, "
        f"Recall {recall[2]:.4f}, "
        f"F1 {f1[2]:.4f}"
    )


    print(
        "\nCalibration"
    )

    print(
        f"ECE: "
        f"{calibration['expected_calibration_error']:.4f}"
    )

    print(
        f"MCE: "
        f"{calibration['maximum_calibration_error']:.4f}"
    )


    print(
        "\nExpected Goals"
    )

    print(
        f"Actual average: "
        f"{average_actual_home:.4f} - "
        f"{average_actual_away:.4f}"
    )

    print(
        f"Predicted average: "
        f"{average_predicted_home:.4f} - "
        f"{average_predicted_away:.4f}"
    )


    print(
        f"Home MAE: "
        f"{home_mae:.4f}"
    )

    print(
        f"Away MAE: "
        f"{away_mae:.4f}"
    )


    print(
        f"Home RMSE: "
        f"{home_rmse:.4f}"
    )

    print(
        f"Away RMSE: "
        f"{away_rmse:.4f}"
    )


    print(
        f"Home bias: "
        f"{home_bias:.4f}"
    )

    print(
        f"Away bias: "
        f"{away_bias:.4f}"
    )


    print(
        "\nScoreline Performance"
    )

    print(
        f"Exact score: "
        f"{exact_accuracy:.4f}"
    )

    print(
        f"Top-3: "
        f"{top3_accuracy:.4f}"
    )

    print(
        f"Top-5: "
        f"{top5_accuracy:.4f}"
    )

    print(
        f"Average probability of actual score: "
        f"{average_actual_score_probability:.4f}"
    )

    print(
        f"Mean rank of actual score: "
        f"{mean_actual_score_rank:.2f}"
    )


    print(
        "\nModel Agreement"
    )

    print(
        f"Stage 5 / Stage 6: "
        f"{agreement_rate:.4f}"
    )


    print(
        "\nDiagnostics"
    )


    for item in diagnostics:

        print(
            f"- {item}"
        )


    print(
        "\nSaved:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()