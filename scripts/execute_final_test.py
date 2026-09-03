"""
FixtureIQ Stage 7.7.4
Final Test Execution & Evaluation

IMPORTANT
---------
This is the first stage allowed to evaluate the 2025/26
final-test dataset.

The locked production model is used exactly as packaged.

Rules:
1. Never retrain the model.
2. Never modify the model.
3. Never use 2025/26 for training or selection.
4. Verify the model SHA256 before prediction.
5. Verify the canonical 86-feature schema.
6. Keep fixture_id outside the model input.
7. Generate three-class probabilities.
8. Evaluate only against the separated final-test target.
9. Save immutable prediction/evaluation artifacts.
10. Record that the final test has now been used.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(BASE_DIR),
)


# ============================================================
# PATHS
# ============================================================

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

FINAL_TEST_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_test"
)

LOCK_FILE = (
    MODEL_DIR
    / "selected_model.json"
)

MODEL_FILE = (
    MODEL_DIR
    / "selected"
    / "selected_model.joblib"
)

X_FINAL_FILE = (
    FINAL_TEST_DIR
    / "final_test_features.csv"
)

Y_FINAL_FILE = (
    FINAL_TEST_DIR
    / "final_test_targets.csv"
)

FINAL_METADATA_FILE = (
    FINAL_TEST_DIR
    / "final_test_metadata.json"
)

QUALITY_FILE = (
    FINAL_TEST_DIR
    / "final_test_quality_report.json"
)

PREDICTIONS_FILE = (
    FINAL_TEST_DIR
    / "final_test_predictions.csv"
)

EVALUATION_FILE = (
    FINAL_TEST_DIR
    / "final_test_evaluation.json"
)

EXECUTION_METADATA_FILE = (
    FINAL_TEST_DIR
    / "final_test_execution_metadata.json"
)

FINAL_LOCK_FILE = (
    FINAL_TEST_DIR
    / "final_test_used.lock"
)


# ============================================================
# CONSTANTS
# ============================================================

EXPECTED_ROWS = 380
EXPECTED_FEATURES = 86

TARGET_MAPPING = {
    0: "draw",
    1: "home_win",
    2: "away_win",
}

PROBABILITY_COLUMNS = [
    "prob_draw",
    "prob_home_win",
    "prob_away_win",
]


# ============================================================
# HELPERS
# ============================================================

def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:

    if not path.exists():
        fail(
            f"Required JSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(
    path: Path,
    data: Dict[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


# ============================================================
# CALIBRATION
# ============================================================

def calibration_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    bins: int = 10,
) -> tuple[float, float]:

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    confidence = (
        probabilities.max(
            axis=1
        )
    )

    predicted = (
        probabilities.argmax(
            axis=1
        )
    )

    correct = (
        predicted
        ==
        y_true
    ).astype(float)

    ece = 0.0
    mce = 0.0

    edges = np.linspace(
        0.0,
        1.0,
        bins + 1,
    )

    for index in range(bins):

        lower = edges[index]
        upper = edges[index + 1]

        if index == bins - 1:

            mask = (
                (confidence >= lower)
                &
                (confidence <= upper)
            )

        else:

            mask = (
                (confidence >= lower)
                &
                (confidence < upper)
            )

        if not mask.any():
            continue

        bin_confidence = (
            confidence[mask].mean()
        )

        bin_accuracy = (
            correct[mask].mean()
        )

        gap = abs(
            bin_accuracy
            -
            bin_confidence
        )

        weight = (
            mask.sum()
            /
            len(y_true)
        )

        ece += (
            weight
            *
            gap
        )

        mce = max(
            mce,
            gap,
        )

    return (
        float(ece),
        float(mce),
    )


def per_class_calibration(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    bins: int = 10,
) -> dict:

    result = {}

    for class_id, label in TARGET_MAPPING.items():

        p = probabilities[
            :,
            class_id,
        ]

        truth = (
            y_true
            ==
            class_id
        ).astype(int)

        ece = 0.0
        mce = 0.0

        edges = np.linspace(
            0.0,
            1.0,
            bins + 1,
        )

        for index in range(bins):

            lower = edges[index]
            upper = edges[index + 1]

            if index == bins - 1:

                mask = (
                    (p >= lower)
                    &
                    (p <= upper)
                )

            else:

                mask = (
                    (p >= lower)
                    &
                    (p < upper)
                )

            if not mask.any():
                continue

            confidence = (
                p[mask].mean()
            )

            accuracy = (
                truth[mask].mean()
            )

            gap = abs(
                accuracy
                -
                confidence
            )

            weight = (
                mask.sum()
                /
                len(y_true)
            )

            ece += (
                weight
                *
                gap
            )

            mce = max(
                mce,
                gap,
            )

        result[label] = {
            "ece": float(ece),
            "mce": float(mce),
            "bins": bins,
        }

    return result


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 50)
    print(
        "FixtureIQ Stage 7.7.4"
    )
    print(
        "Final Test Execution & Evaluation"
    )
    print("=" * 50)

    # ========================================================
    # 1. PRE-FLIGHT PROTECTION
    # ========================================================

    print(
        "\n1. PRE-FLIGHT PROTECTION"
    )

    lock = load_json(
        LOCK_FILE
    )

    if lock.get(
        "status"
    ) != "LOCKED":

        fail(
            "Selected model is not LOCKED."
        )

    if lock.get(
        "selected_candidate"
    ) != "random_forest":

        fail(
            "Locked model is not "
            "Random Forest."
        )

    if lock.get(
        "final_test_used"
    ) is True:

        fail(
            "Final test has already been "
            "marked as used."
        )

    print(
        "Selected model: Random Forest"
    )

    print(
        "Model status: LOCKED"
    )

    print(
        "Final test previously used: NO"
    )

    # ========================================================
    # 2. MODEL IDENTITY
    # ========================================================

    print(
        "\n2. MODEL IDENTITY"
    )

    if not MODEL_FILE.exists():

        fail(
            f"Production model not found: "
            f"{MODEL_FILE}"
        )

    model_hash = sha256_file(
        MODEL_FILE
    )

    locked_hash = lock.get(
        "model_sha256"
    )

    if model_hash != locked_hash:

        fail(
            "Production model SHA256 "
            "does not match selected-model lock."
        )

    model = joblib.load(
        MODEL_FILE
    )

    print(
        "Model artifact: PASS"
    )

    print(
        "SHA256: MATCH"
    )

    print(
        "Model loaded: PASS"
    )

    # ========================================================
    # 3. FINAL TEST INPUT
    # ========================================================

    print(
        "\n3. FINAL TEST INPUT"
    )

    if not X_FINAL_FILE.exists():

        fail(
            "Final-test feature file "
            "does not exist."
        )

    if not Y_FINAL_FILE.exists():

        fail(
            "Final-test target file "
            "does not exist."
        )

    X_raw = pd.read_csv(
        X_FINAL_FILE
    )

    y_frame = pd.read_csv(
        Y_FINAL_FILE
    )

    if len(X_raw) != EXPECTED_ROWS:

        fail(
            f"Expected {EXPECTED_ROWS} "
            f"feature records, found "
            f"{len(X_raw)}."
        )

    if len(y_frame) != EXPECTED_ROWS:

        fail(
            f"Expected {EXPECTED_ROWS} "
            f"target records, found "
            f"{len(y_frame)}."
        )

    if "fixture_id" not in X_raw.columns:

        fail(
            "fixture_id is missing from "
            "final-test feature artifact."
        )

    if "fixture_id" not in y_frame.columns:

        fail(
            "fixture_id is missing from "
            "final-test target artifact."
        )

    if not X_raw[
        "fixture_id"
    ].is_unique:

        fail(
            "Final-test fixture IDs "
            "are not unique."
        )

    if not y_frame[
        "fixture_id"
    ].is_unique:

        fail(
            "Final-test target fixture IDs "
            "are not unique."
        )

    # ========================================================
    # 4. FIXTURE ALIGNMENT
    # ========================================================

    print(
        "\n4. FIXTURE ALIGNMENT"
    )

    feature_ids = (
        X_raw[
            "fixture_id"
        ]
        .astype(int)
        .tolist()
    )

    target_ids = (
        y_frame[
            "fixture_id"
        ]
        .astype(int)
        .tolist()
    )

    if set(feature_ids) != set(
        target_ids
    ):

        fail(
            "Feature and target fixture IDs "
            "do not match."
        )

    print(
        "Fixture IDs: PASS"
    )

    # ========================================================
    # 5. FEATURE SCHEMA
    # ========================================================

    print(
        "\n5. FEATURE SCHEMA"
    )

    feature_columns = [
        column
        for column
        in X_raw.columns
        if column != "fixture_id"
    ]

    if len(feature_columns) != EXPECTED_FEATURES:

        fail(
            "Final-test feature count "
            f"is {len(feature_columns)}, "
            f"expected {EXPECTED_FEATURES}."
        )

    # Read canonical schema directly
    # from X_train.csv.

    canonical_schema_file = (
        MODEL_DIR
        / "X_train.csv"
    )

    if not canonical_schema_file.exists():

        fail(
            "Canonical X_train.csv "
            "does not exist."
        )

    canonical = pd.read_csv(
        canonical_schema_file,
        nrows=0,
    )

    canonical_columns = list(
        canonical.columns
    )

    if feature_columns != canonical_columns:

        fail(
            "Final-test feature columns "
            "do not exactly match the "
            "canonical 86-feature schema."
        )

    if "fixture_id" in feature_columns:

        fail(
            "fixture_id entered the model "
            "feature matrix."
        )

    print(
        "Feature count: 86"
    )

    print(
        "Schema match: PASS"
    )

    # ========================================================
    # 6. MODEL MATRIX
    # ========================================================

    print(
        "\n6. MODEL MATRIX"
    )

    X = (
        X_raw[
            feature_columns
        ]
        .copy()
    )

    non_numeric = [
        column
        for column
        in X.columns
        if not pd.api.types.is_numeric_dtype(
            X[column]
        )
    ]

    if non_numeric:

        fail(
            "Non-numeric model features: "
            f"{non_numeric}"
        )

    values = X.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        values
    ).all():

        fail(
            "NaN or infinite values "
            "found in final-test matrix."
        )

    print(
        "Shape: "
        f"{X.shape}"
    )

    print(
        "Numeric integrity: PASS"
    )

    # ========================================================
    # 7. TARGET VALIDATION
    # ========================================================

    print(
        "\n7. TARGET VALIDATION"
    )

    if "target" not in y_frame.columns:

        fail(
            "Target column missing."
        )

    y = (
        y_frame[
            "target"
        ]
        .astype(int)
        .to_numpy()
    )

    if not set(y).issubset(
        {
            0,
            1,
            2,
        }
    ):

        fail(
            "Invalid target values."
        )

    print(
        "Target mapping: PASS"
    )

    print(
        "Target values: "
        f"{sorted(set(y))}"
    )

    # ========================================================
    # 8. FINAL TEST EXECUTION
    # ========================================================

    print(
        "\n8. FINAL TEST EXECUTION"
    )

    print(
        "Using locked Random Forest..."
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    predictions = (
        model.predict(
            X
        )
    )

    probabilities = (
        model.predict_proba(
            X
        )
    )

    predictions = np.asarray(
        predictions,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if len(predictions) != EXPECTED_ROWS:

        fail(
            "Prediction count does not "
            "equal 380."
        )

    if probabilities.shape != (
        EXPECTED_ROWS,
        3,
    ):

        fail(
            "Probability matrix does not "
            "have shape (380, 3)."
        )

    # ========================================================
    # CLASS ORDER
    # ========================================================

    model_classes = [
        int(value)
        for value
        in model.classes_
    ]

    if model_classes != [
        0,
        1,
        2,
    ]:

        fail(
            "Unexpected model class order: "
            f"{model_classes}"
        )

    if not np.isfinite(
        probabilities
    ).all():

        fail(
            "Non-finite probabilities."
        )

    if (
        probabilities < 0
    ).any():

        fail(
            "Negative probabilities."
        )

    if (
        probabilities > 1
    ).any():

        fail(
            "Probability greater than 1."
        )

    probability_sums = (
        probabilities.sum(
            axis=1
        )
    )

    if not np.allclose(
        probability_sums,
        1.0,
        atol=1e-6,
    ):

        fail(
            "Probability rows do not "
            "sum to 1."
        )

    if not np.array_equal(
        predictions,
        probabilities.argmax(
            axis=1
        ),
    ):

        fail(
            "Predictions do not agree "
            "with maximum-probability class."
        )

    print(
        "Predictions: 380"
    )

    print(
        "Probability generation: PASS"
    )

    print(
        "Probability integrity: PASS"
    )

    # ========================================================
    # 9. FINAL EVALUATION
    # ========================================================

    print(
        "\n9. FINAL TEST EVALUATION"
    )

    accuracy = accuracy_score(
        y,
        predictions,
    )

    logloss = log_loss(
        y,
        probabilities,
        labels=[
            0,
            1,
            2,
        ],
    )

    # Multiclass Brier score:
    # mean squared difference between
    # one-hot truth and predicted probabilities.

    one_hot = np.zeros_like(
        probabilities
    )

    one_hot[
        np.arange(
            len(y)
        ),
        y,
    ] = 1.0

    brier = np.mean(
        np.sum(
            (
                probabilities
                -
                one_hot
            )
            ** 2,
            axis=1,
        )
    )

    precision = precision_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average=None,
        zero_division=0,
    )

    recall = recall_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average=None,
        zero_division=0,
    )

    f1 = f1_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average=None,
        zero_division=0,
    )

    precision_macro = precision_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average="macro",
        zero_division=0,
    )

    recall_macro = recall_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average="macro",
        zero_division=0,
    )

    f1_macro = f1_score(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
        average="macro",
        zero_division=0,
    )

    matrix = confusion_matrix(
        y,
        predictions,
        labels=[
            0,
            1,
            2,
        ],
    )

    ece, mce = calibration_metrics(
        y,
        probabilities,
    )

    class_calibration = (
        per_class_calibration(
            y,
            probabilities,
        )
    )

    per_class_metrics = {}

    for index, label in TARGET_MAPPING.items():

        per_class_metrics[label] = {
            "precision":
                float(
                    precision[index]
                ),

            "recall":
                float(
                    recall[index]
                ),

            "f1":
                float(
                    f1[index]
                ),
        }

    print(
        "\nFINAL TEST RESULTS"
    )

    print(
        "-" * 60
    )

    print(
        f"Accuracy:    {accuracy:.6f}"
    )

    print(
        f"Log Loss:    {logloss:.6f}"
    )

    print(
        f"Brier Score: {brier:.6f}"
    )

    print(
        f"ECE:         {ece:.6f}"
    )

    print(
        f"MCE:         {mce:.6f}"
    )

    print(
        "-" * 60
    )

    print(
        f"Precision Macro: {precision_macro:.6f}"
    )

    print(
        f"Recall Macro:    {recall_macro:.6f}"
    )

    print(
        f"F1 Macro:        {f1_macro:.6f}"
    )

    # ========================================================
    # 10. SAVE PREDICTIONS
    # ========================================================

    print(
        "\n10. PREDICTION ARTIFACT"
    )

    prediction_output = pd.DataFrame(
        {
            "fixture_id":
                feature_ids,

            "actual_target":
                y,

            "predicted_target":
                predictions,

            "actual_label":
                [
                    TARGET_MAPPING[
                        int(value)
                    ]
                    for value in y
                ],

            "predicted_label":
                [
                    TARGET_MAPPING[
                        int(value)
                    ]
                    for value
                    in predictions
                ],

            "prob_draw":
                probabilities[
                    :,
                    0,
                ],

            "prob_home_win":
                probabilities[
                    :,
                    1,
                ],

            "prob_away_win":
                probabilities[
                    :,
                    2,
                ],
        }
    )

    prediction_output.to_csv(
        PREDICTIONS_FILE,
        index=False,
    )

    print(
        "Prediction file:"
    )

    print(
        PREDICTIONS_FILE
    )

    # ========================================================
    # 11. SAVE EVALUATION
    # ========================================================

    evaluation = {
        "stage":
            "7.7.4",

        "dataset":
            "2025/26 final test",

        "sample_count":
            EXPECTED_ROWS,

        "model":
            "Random Forest",

        "candidate_id":
            "random_forest",

        "model_sha256":
            model_hash,

        "training_season":
            2023,

        "validation_season":
            2024,

        "final_test_season":
            "2025/26",

        "feature_count":
            EXPECTED_FEATURES,

        "metrics": {
            "accuracy":
                float(accuracy),

            "log_loss":
                float(logloss),

            "brier_score":
                float(brier),

            "precision_macro":
                float(precision_macro),

            "recall_macro":
                float(recall_macro),

            "f1_macro":
                float(f1_macro),

            "ece":
                float(ece),

            "mce":
                float(mce),
        },

        "per_class_metrics":
            per_class_metrics,

        "confusion_matrix":
            matrix.tolist(),

        "per_class_calibration":
            class_calibration,

        "model_retrained":
            False,

        "model_selection_performed":
            False,

        "final_test_used":
            True,

        "final_test_is_now_consumed":
            True,
    }

    save_json(
        EVALUATION_FILE,
        evaluation,
    )

    # ========================================================
    # 12. EXECUTION METADATA
    # ========================================================

    execution_metadata = {
        "stage":
            "7.7.4",

        "execution":
            "completed",

        "dataset":
            "2025/26 final test",

        "sample_count":
            EXPECTED_ROWS,

        "model":
            "Random Forest",

        "candidate_id":
            "random_forest",

        "model_status":
            "LOCKED",

        "model_sha256":
            model_hash,

        "model_hash_verified":
            True,

        "feature_count":
            EXPECTED_FEATURES,

        "feature_schema_verified":
            True,

        "training_season":
            2023,

        "validation_season":
            2024,

        "final_test_season":
            "2025/26",

        "retrained":
            False,

        "selected_again":
            False,

        "final_test_evaluated":
            True,

        "final_test_consumed":
            True,

        "2025_26_used_for_training":
            False,

        "2025_26_used_for_selection":
            False,
    }

    save_json(
        EXECUTION_METADATA_FILE,
        execution_metadata,
    )

    # ========================================================
    # 13. FINAL TEST CONSUMPTION LOCK
    # ========================================================

    print(
        "\n11. FINAL TEST CONSUMPTION LOCK"
    )

    final_lock = {
        "stage":
            "7.7.4",

        "status":
            "CONSUMED",

        "dataset":
            "2025/26",

        "records":
            EXPECTED_ROWS,

        "model":
            "Random Forest",

        "model_sha256":
            model_hash,

        "evaluated":
            True,

        "training_after_evaluation_allowed":
            False,

        "model_selection_after_evaluation_allowed":
            False,
    }

    save_json(
        FINAL_LOCK_FILE,
        final_lock,
    )

    print(
        "Final-test consumption lock: CREATED"
    )

    # ========================================================
    # 14. UPDATE SELECTED MODEL LOCK
    # ========================================================
    #
    # IMPORTANT:
    # We preserve all existing lock information and
    # only record final-test consumption.
    #
    # The model hash itself is NOT changed.
    # ========================================================

    lock["final_test_used"] = True
    lock["final_test_evaluated"] = True
    lock["final_test_season"] = "2025/26"

    save_json(
        LOCK_FILE,
        lock,
    )

    print(
        "Selected-model lock updated:"
    )

    print(
        "final_test_used = TRUE"
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.7.4: PASS"
    )

    print(
        "=" * 50
    )

    print(
        "Final test: 2025/26"
    )

    print(
        "Records: 380"
    )

    print(
        "Selected model: Random Forest"
    )

    print(
        "Model remained locked: YES"
    )

    print(
        "Model retrained: NO"
    )

    print(
        "Model re-selected: NO"
    )

    print(
        "Final test evaluated: YES"
    )

    print(
        "Final test consumed: YES"
    )

    print(
        "\nPrediction artifact:"
    )

    print(
        PREDICTIONS_FILE
    )

    print(
        "\nEvaluation artifact:"
    )

    print(
        EVALUATION_FILE
    )

    print(
        "\nExecution metadata:"
    )

    print(
        EXECUTION_METADATA_FILE
    )

    print(
        "\nFinal-test lock:"
    )

    print(
        FINAL_LOCK_FILE
    )


if __name__ == "__main__":
    main()