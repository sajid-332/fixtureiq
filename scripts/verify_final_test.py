"""
FixtureIQ Stage 7.7.4
Final Test Verification
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

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

X_FILE = (
    FINAL_TEST_DIR
    / "final_test_features.csv"
)

Y_FILE = (
    FINAL_TEST_DIR
    / "final_test_targets.csv"
)

PREDICTIONS_FILE = (
    FINAL_TEST_DIR
    / "final_test_predictions.csv"
)

EVALUATION_FILE = (
    FINAL_TEST_DIR
    / "final_test_evaluation.json"
)

EXECUTION_FILE = (
    FINAL_TEST_DIR
    / "final_test_execution_metadata.json"
)

FINAL_LOCK_FILE = (
    FINAL_TEST_DIR
    / "final_test_used.lock"
)

EXPECTED_ROWS = 380
EXPECTED_FEATURES = 86


def sha256_file(path):

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def check(
    label,
    condition,
):

    print(
        f"{label}: "
        f"{'PASS' if condition else 'FAIL'}"
    )

    return bool(condition)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.7.4"
    )

    print(
        "Final Test Verification"
    )

    print("=" * 50)

    failures = 0

    # ========================================================
    # 1. MODEL LOCK
    # ========================================================

    print(
        "\n1. MODEL LOCK"
    )

    lock_exists = check(
        "Lock file",
        LOCK_FILE.exists(),
    )

    if not lock_exists:
        failures += 1
        return finish(
            failures
        )

    lock = load_json(
        LOCK_FILE
    )

    failures += not check(
        "Model status LOCKED",
        lock.get("status")
        == "LOCKED",
    )

    failures += not check(
        "Selected Random Forest",
        lock.get(
            "selected_candidate"
        )
        ==
        "random_forest",
    )

    failures += not check(
        "Final test used",
        lock.get(
            "final_test_used"
        )
        is True,
    )

    # ========================================================
    # 2. MODEL HASH
    # ========================================================

    print(
        "\n2. MODEL IDENTITY"
    )

    failures += not check(
        "Model artifact",
        MODEL_FILE.exists(),
    )

    if MODEL_FILE.exists():

        actual_hash = (
            sha256_file(
                MODEL_FILE
            )
        )

        failures += not check(
            "SHA256 match",
            actual_hash
            ==
            lock.get(
                "model_sha256"
            ),
        )

    # ========================================================
    # 3. FINAL TEST INPUT
    # ========================================================

    print(
        "\n3. FINAL TEST INPUT"
    )

    failures += not check(
        "Feature artifact",
        X_FILE.exists(),
    )

    failures += not check(
        "Target artifact",
        Y_FILE.exists(),
    )

    if not (
        X_FILE.exists()
        and
        Y_FILE.exists()
    ):

        return finish(
            failures
        )

    X = pd.read_csv(
        X_FILE
    )

    y = pd.read_csv(
        Y_FILE
    )

    failures += not check(
        "Feature records = 380",
        len(X)
        ==
        EXPECTED_ROWS,
    )

    failures += not check(
        "Target records = 380",
        len(y)
        ==
        EXPECTED_ROWS,
    )

    # ========================================================
    # 4. FEATURE SCHEMA
    # ========================================================

    print(
        "\n4. FEATURE SCHEMA"
    )

    failures += not check(
        "fixture_id present",
        "fixture_id" in X.columns,
    )

    feature_columns = [
        column
        for column
        in X.columns
        if column != "fixture_id"
    ]

    failures += not check(
        "86 model features",
        len(feature_columns)
        ==
        EXPECTED_FEATURES,
    )

    canonical_file = (
        MODEL_DIR
        / "X_train.csv"
    )

    canonical = pd.read_csv(
        canonical_file,
        nrows=0,
    )

    failures += not check(
        "Canonical schema match",
        feature_columns
        ==
        list(canonical.columns),
    )

    # ========================================================
    # 5. NUMERIC INTEGRITY
    # ========================================================

    print(
        "\n5. NUMERIC INTEGRITY"
    )

    matrix = X[
        feature_columns
    ].to_numpy(
        dtype=float
    )

    failures += not check(
        "No NaN",
        not np.isnan(
            matrix
        ).any(),
    )

    failures += not check(
        "No infinite values",
        np.isfinite(
            matrix
        ).all(),
    )

    # ========================================================
    # 6. FIXTURE ALIGNMENT
    # ========================================================

    print(
        "\n6. FIXTURE ALIGNMENT"
    )

    failures += not check(
        "Unique feature fixture IDs",
        X[
            "fixture_id"
        ].is_unique,
    )

    failures += not check(
        "Unique target fixture IDs",
        y[
            "fixture_id"
        ].is_unique,
    )

    failures += not check(
        "Feature/target fixture alignment",
        set(
            X[
                "fixture_id"
            ]
        )
        ==
        set(
            y[
                "fixture_id"
            ]
        ),
    )

    # ========================================================
    # 7. PREDICTIONS
    # ========================================================

    print(
        "\n7. PREDICTION ARTIFACT"
    )

    failures += not check(
        "Prediction file",
        PREDICTIONS_FILE.exists(),
    )

    if PREDICTIONS_FILE.exists():

        predictions = pd.read_csv(
            PREDICTIONS_FILE
        )

        required = {
            "fixture_id",
            "actual_target",
            "predicted_target",
            "actual_label",
            "predicted_label",
            "prob_draw",
            "prob_home_win",
            "prob_away_win",
        }

        failures += not check(
            "Prediction schema",
            required.issubset(
                predictions.columns
            ),
        )

        failures += not check(
            "Prediction count = 380",
            len(predictions)
            ==
            EXPECTED_ROWS,
        )

        failures += not check(
            "Prediction fixture IDs unique",
            predictions[
                "fixture_id"
            ].is_unique,
        )

        probabilities = predictions[
            [
                "prob_draw",
                "prob_home_win",
                "prob_away_win",
            ]
        ].to_numpy(
            dtype=float
        )

        failures += not check(
            "Finite probabilities",
            np.isfinite(
                probabilities
            ).all(),
        )

        failures += not check(
            "Probability range",
            (
                (probabilities >= 0)
                &
                (probabilities <= 1)
            ).all(),
        )

        failures += not check(
            "Probability sums",
            np.allclose(
                probabilities.sum(
                    axis=1
                ),
                1.0,
                atol=1e-6,
            ),
        )

    # ========================================================
    # 8. EVALUATION
    # ========================================================

    print(
        "\n8. FINAL EVALUATION"
    )

    failures += not check(
        "Evaluation file",
        EVALUATION_FILE.exists(),
    )

    if EVALUATION_FILE.exists():

        evaluation = load_json(
            EVALUATION_FILE
        )

        failures += not check(
            "Stage 7.7.4",
            evaluation.get(
                "stage"
            )
            ==
            "7.7.4",
        )

        failures += not check(
            "Sample count = 380",
            evaluation.get(
                "sample_count"
            )
            ==
            EXPECTED_ROWS,
        )

        metrics = evaluation.get(
            "metrics",
            {},
        )

        required_metrics = [
            "accuracy",
            "log_loss",
            "brier_score",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "ece",
            "mce",
        ]

        failures += not check(
            "Metric schema",
            all(
                metric in metrics
                for metric
                in required_metrics
            ),
        )

        failures += not check(
            "Metric values finite",
            all(
                np.isfinite(
                    float(
                        metrics[metric]
                    )
                )
                for metric
                in required_metrics
                if metric in metrics
            ),
        )

        print(
            f"Accuracy: "
            f"{metrics.get('accuracy', 0):.6f}"
        )

        print(
            f"Log Loss: "
            f"{metrics.get('log_loss', 0):.6f}"
        )

        print(
            f"Brier Score: "
            f"{metrics.get('brier_score', 0):.6f}"
        )

        print(
            f"ECE: "
            f"{metrics.get('ece', 0):.6f}"
        )

        print(
            f"MCE: "
            f"{metrics.get('mce', 0):.6f}"
        )

    # ========================================================
    # 9. EXECUTION METADATA
    # ========================================================

    print(
        "\n9. EXECUTION METADATA"
    )

    failures += not check(
        "Execution metadata",
        EXECUTION_FILE.exists(),
    )

    if EXECUTION_FILE.exists():

        execution = load_json(
            EXECUTION_FILE
        )

        failures += not check(
            "Final test evaluated",
            execution.get(
                "final_test_evaluated"
            )
            is True,
        )

        failures += not check(
            "2025/26 not used for training",
            execution.get(
                "2025_26_used_for_training"
            )
            is False,
        )

        failures += not check(
            "2025/26 not used for selection",
            execution.get(
                "2025_26_used_for_selection"
            )
            is False,
        )

        failures += not check(
            "Model not retrained",
            execution.get(
                "retrained"
            )
            is False,
        )

        failures += not check(
            "Model not re-selected",
            execution.get(
                "selected_again"
            )
            is False,
        )

    # ========================================================
    # 10. CONSUMPTION LOCK
    # ========================================================

    print(
        "\n10. FINAL TEST CONSUMPTION LOCK"
    )

    failures += not check(
        "Final-test lock",
        FINAL_LOCK_FILE.exists(),
    )

    if FINAL_LOCK_FILE.exists():

        final_lock = load_json(
            FINAL_LOCK_FILE
        )

        failures += not check(
            "Status CONSUMED",
            final_lock.get(
                "status"
            )
            ==
            "CONSUMED",
        )

        failures += not check(
            "Training after evaluation prohibited",
            final_lock.get(
                "training_after_evaluation_allowed"
            )
            is False,
        )

        failures += not check(
            "Model selection after evaluation prohibited",
            final_lock.get(
                "model_selection_after_evaluation_allowed"
            )
            is False,
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return finish(
        failures
    )


def finish(
    failures
):

    print(
        "\n" + "=" * 50
    )

    if failures == 0:

        print(
            "STAGE 7.7.4: COMPLETE"
        )

        print(
            "Final 2025/26 test successfully "
            "executed and verified."
        )

    else:

        print(
            "STAGE 7.7.4: FAIL"
        )

        print(
            f"Verification failures: {failures}"
        )

    print(
        "=" * 50
    )

    raise SystemExit(
        0 if failures == 0 else 1
    )


if __name__ == "__main__":
    main()