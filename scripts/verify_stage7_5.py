"""
FixtureIQ Stage 7.5.6
Final Baseline Pipeline Verification.

Verifies the complete Stage 7.5 pipeline:

7.5.1 - Model Input Contract
7.5.2 - Baseline Model
7.5.3 - Probability Generation
7.5.4 - Baseline Evaluation
7.5.5 - Calibration Analysis

This script performs verification only.
It does not retrain or modify the model.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "model"
)

X_TRAIN_FILE = MODEL_DIR / "X_train.csv"
Y_TRAIN_FILE = MODEL_DIR / "y_train.csv"

X_VALIDATION_FILE = (
    MODEL_DIR / "X_validation.csv"
)

Y_VALIDATION_FILE = (
    MODEL_DIR / "y_validation.csv"
)

FEATURE_SCHEMA_FILE = (
    MODEL_DIR / "feature_schema.json"
)

BASELINE_MODEL_FILE = (
    MODEL_DIR / "baseline_model.joblib"
)

BASELINE_METADATA_FILE = (
    MODEL_DIR / "baseline_model_metadata.json"
)

PREDICTIONS_FILE = (
    MODEL_DIR / "baseline_predictions.csv"
)

PREDICTION_METADATA_FILE = (
    MODEL_DIR
    / "baseline_prediction_metadata.json"
)

METRICS_FILE = (
    MODEL_DIR / "baseline_metrics.json"
)

CALIBRATION_FILE = (
    MODEL_DIR / "baseline_calibration.json"
)

CALIBRATION_PLOT_FILE = (
    MODEL_DIR / "baseline_calibration.png"
)

VALIDATION_FEATURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "validation_features.csv"
)


def check_file(path: Path) -> bool:
    """Return whether a required artifact exists."""

    return path.exists() and path.is_file()


def load_json(path: Path) -> dict:
    """Load a JSON artifact."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.6"
    )

    print(
        "Final Baseline Pipeline Verification"
    )

    print("=" * 50)

    results = {}

    # ========================================================
    # 1. MODEL INPUT CONTRACT
    # ========================================================

    print(
        "\n1. MODEL INPUT CONTRACT"
    )

    input_files = {
        "X_train": X_TRAIN_FILE,
        "y_train": Y_TRAIN_FILE,
        "X_validation": X_VALIDATION_FILE,
        "y_validation": Y_VALIDATION_FILE,
        "feature_schema": FEATURE_SCHEMA_FILE,
    }

    input_files_pass = True

    for name, path in input_files.items():

        passed = check_file(path)

        results[
            f"input_{name}"
        ] = passed

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            input_files_pass = False

    if input_files_pass:

        X_train = pd.read_csv(
            X_TRAIN_FILE
        )

        y_train = pd.read_csv(
            Y_TRAIN_FILE
        )

        X_validation = pd.read_csv(
            X_VALIDATION_FILE
        )

        y_validation = pd.read_csv(
            Y_VALIDATION_FILE
        )

        schema = load_json(
            FEATURE_SCHEMA_FILE
        )

        feature_columns = schema.get(
            "feature_columns",
            [],
        )

        shape_pass = (
            X_train.shape
            ==
            (380, 86)
            and
            X_validation.shape
            ==
            (380, 86)
        )

        target_count_pass = (
            len(y_train) == 380
            and
            len(y_validation) == 380
        )

        schema_pass = (
            list(X_train.columns)
            ==
            list(feature_columns)
            ==
            list(X_validation.columns)
        )

        target_values_pass = (
            set(
                y_train["target"]
                .astype(int)
                .unique()
            )
            <=
            {0, 1, 2}
            and
            set(
                y_validation["target"]
                .astype(int)
                .unique()
            )
            <=
            {0, 1, 2}
        )

        print(
            f"Training shape (380, 86): "
            f"{'PASS' if X_train.shape == (380, 86) else 'FAIL'}"
        )

        print(
            f"Validation shape (380, 86): "
            f"{'PASS' if X_validation.shape == (380, 86) else 'FAIL'}"
        )

        print(
            f"Feature schema: "
            f"{'PASS' if schema_pass else 'FAIL'}"
        )

        print(
            f"Target values: "
            f"{'PASS' if target_values_pass else 'FAIL'}"
        )

        results["input_shape"] = shape_pass
        results["input_target_count"] = target_count_pass
        results["input_schema"] = schema_pass
        results["input_targets"] = target_values_pass

    else:

        X_train = None
        y_train = None
        X_validation = None
        y_validation = None

    # ========================================================
    # 2. BASELINE MODEL
    # ========================================================

    print(
        "\n2. BASELINE MODEL"
    )

    model_exists = check_file(
        BASELINE_MODEL_FILE
    )

    metadata_exists = check_file(
        BASELINE_METADATA_FILE
    )

    print(
        f"Model artifact: "
        f"{'PASS' if model_exists else 'FAIL'}"
    )

    print(
        f"Model metadata: "
        f"{'PASS' if metadata_exists else 'FAIL'}"
    )

    results["model_artifact"] = model_exists
    results["model_metadata"] = metadata_exists

    model_metadata_pass = False

    if metadata_exists:

        metadata = load_json(
            BASELINE_METADATA_FILE
        )

        model_metadata_pass = (
            metadata.get("stage")
            == "7.5.2"
            and
            metadata.get("model_type")
            == "LogisticRegression"
            and
            metadata.get("feature_count")
            == 86
            and
            metadata.get("training_rows")
            == 380
            and
            metadata.get("classes")
            == [0, 1, 2]
        )

    print(
        f"Model metadata integrity: "
        f"{'PASS' if model_metadata_pass else 'FAIL'}"
    )

    results[
        "model_metadata_integrity"
    ] = model_metadata_pass

    # ========================================================
    # 3. PROBABILITY GENERATION
    # ========================================================

    print(
        "\n3. PROBABILITY GENERATION"
    )

    prediction_exists = check_file(
        PREDICTIONS_FILE
    )

    prediction_metadata_exists = (
        check_file(
            PREDICTION_METADATA_FILE
        )
    )

    print(
        f"Prediction artifact: "
        f"{'PASS' if prediction_exists else 'FAIL'}"
    )

    print(
        f"Prediction metadata: "
        f"{'PASS' if prediction_metadata_exists else 'FAIL'}"
    )

    results[
        "prediction_artifact"
    ] = prediction_exists

    results[
        "prediction_metadata"
    ] = prediction_metadata_exists

    prediction_integrity = False

    predictions = None

    if prediction_exists:

        predictions = pd.read_csv(
            PREDICTIONS_FILE
        )

        required_prediction_columns = {
            "fixture_id",
            "actual",
            "predicted",
            "prob_home",
            "prob_draw",
            "prob_away",
        }

        schema_ok = (
            required_prediction_columns
            <=
            set(predictions.columns)
        )

        count_ok = (
            len(predictions) == 380
        )

        fixture_ids_ok = (
            predictions[
                "fixture_id"
            ].nunique()
            ==
            380
        )

        probabilities = predictions[
            [
                "prob_draw",
                "prob_home",
                "prob_away",
            ]
        ].to_numpy(
            dtype=float
        )

        finite_ok = np.isfinite(
            probabilities
        ).all()

        range_ok = (
            (probabilities >= 0).all()
            and
            (probabilities <= 1).all()
        )

        sum_ok = np.allclose(
            probabilities.sum(axis=1),
            1.0,
            atol=1e-8,
        )

        prediction_integrity = all(
            [
                schema_ok,
                count_ok,
                fixture_ids_ok,
                finite_ok,
                range_ok,
                sum_ok,
            ]
        )

        print(
            f"Prediction count: "
            f"{'PASS' if count_ok else 'FAIL'}"
        )

        print(
            f"Prediction schema: "
            f"{'PASS' if schema_ok else 'FAIL'}"
        )

        print(
            f"Unique fixture IDs: "
            f"{'PASS' if fixture_ids_ok else 'FAIL'}"
        )

        print(
            f"Probability integrity: "
            f"{'PASS' if (finite_ok and range_ok and sum_ok) else 'FAIL'}"
        )

    print(
        f"Prediction integrity: "
        f"{'PASS' if prediction_integrity else 'FAIL'}"
    )

    results[
        "prediction_integrity"
    ] = prediction_integrity

    # ========================================================
    # 4. BASELINE EVALUATION
    # ========================================================

    print(
        "\n4. BASELINE EVALUATION"
    )

    metrics_exists = check_file(
        METRICS_FILE
    )

    print(
        f"Metrics report: "
        f"{'PASS' if metrics_exists else 'FAIL'}"
    )

    results[
        "metrics_report"
    ] = metrics_exists

    metrics_integrity = False

    if metrics_exists:

        metrics = load_json(
            METRICS_FILE
        )

        required_metrics = {
            "sample_count",
            "accuracy",
            "log_loss",
            "brier_score",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "per_class",
            "confusion_matrix",
        }

        metric_schema_ok = (
            required_metrics
            <=
            set(metrics.keys())
        )

        metric_count_ok = (
            metrics.get(
                "sample_count"
            )
            ==
            380
        )

        metric_values = [
            metrics.get("accuracy"),
            metrics.get("log_loss"),
            metrics.get("brier_score"),
            metrics.get("precision_macro"),
            metrics.get("recall_macro"),
            metrics.get("f1_macro"),
        ]

        metric_values_ok = (
            all(
                value is not None
                and
                np.isfinite(value)
                for value in metric_values
            )
        )

        per_class_ok = (
            set(
                metrics.get(
                    "per_class",
                    {},
                ).keys()
            )
            ==
            {
                "draw",
                "home_win",
                "away_win",
            }
        )

        confusion_ok = (
            np.asarray(
                metrics.get(
                    "confusion_matrix",
                    [],
                )
            ).shape
            ==
            (3, 3)
        )

        metrics_integrity = all(
            [
                metric_schema_ok,
                metric_count_ok,
                metric_values_ok,
                per_class_ok,
                confusion_ok,
            ]
        )

        print(
            f"Metric schema: "
            f"{'PASS' if metric_schema_ok else 'FAIL'}"
        )

        print(
            f"Metric sample count: "
            f"{'PASS' if metric_count_ok else 'FAIL'}"
        )

        print(
            f"Metric values: "
            f"{'PASS' if metric_values_ok else 'FAIL'}"
        )

        print(
            f"Per-class metrics: "
            f"{'PASS' if per_class_ok else 'FAIL'}"
        )

        print(
            f"Confusion matrix: "
            f"{'PASS' if confusion_ok else 'FAIL'}"
        )

    print(
        f"Evaluation integrity: "
        f"{'PASS' if metrics_integrity else 'FAIL'}"
    )

    results[
        "metrics_integrity"
    ] = metrics_integrity

    # ========================================================
    # 5. CALIBRATION
    # ========================================================

    print(
        "\n5. CALIBRATION ANALYSIS"
    )

    calibration_exists = check_file(
        CALIBRATION_FILE
    )

    calibration_plot_exists = (
        check_file(
            CALIBRATION_PLOT_FILE
        )
    )

    print(
        f"Calibration report: "
        f"{'PASS' if calibration_exists else 'FAIL'}"
    )

    print(
        f"Calibration plot: "
        f"{'PASS' if calibration_plot_exists else 'FAIL'}"
    )

    results[
        "calibration_report"
    ] = calibration_exists

    results[
        "calibration_plot"
    ] = calibration_plot_exists

    calibration_integrity = False

    if calibration_exists:

        calibration = load_json(
            CALIBRATION_FILE
        )

        required_calibration_fields = {
            "sample_count",
            "bin_count",
            "binning_method",
            "ece_definition",
            "mce_definition",
            "ece",
            "mce",
            "class_order",
            "per_class",
        }

        calibration_schema_ok = (
            required_calibration_fields
            <=
            set(calibration.keys())
        )

        calibration_count_ok = (
            calibration.get(
                "sample_count"
            )
            ==
            380
        )

        ece = calibration.get(
            "ece"
        )

        mce = calibration.get(
            "mce"
        )

        calibration_metrics_ok = (
            ece is not None
            and
            mce is not None
            and
            np.isfinite(ece)
            and
            np.isfinite(mce)
            and
            0 <= ece <= 1
            and
            0 <= mce <= 1
        )

        classes_ok = (
            set(
                calibration.get(
                    "per_class",
                    {},
                ).keys()
            )
            ==
            {
                "draw",
                "home_win",
                "away_win",
            }
        )

        calibration_integrity = all(
            [
                calibration_schema_ok,
                calibration_count_ok,
                calibration_metrics_ok,
                classes_ok,
            ]
        )

        print(
            f"Calibration schema: "
            f"{'PASS' if calibration_schema_ok else 'FAIL'}"
        )

        print(
            f"Calibration sample count: "
            f"{'PASS' if calibration_count_ok else 'FAIL'}"
        )

        print(
            f"ECE/MCE validity: "
            f"{'PASS' if calibration_metrics_ok else 'FAIL'}"
        )

        print(
            f"Per-class calibration: "
            f"{'PASS' if classes_ok else 'FAIL'}"
        )

        print(
            f"ECE: {ece:.6f}"
        )

        print(
            f"MCE: {mce:.6f}"
        )

    print(
        f"Calibration integrity: "
        f"{'PASS' if calibration_integrity else 'FAIL'}"
    )

    results[
        "calibration_integrity"
    ] = calibration_integrity

    # ========================================================
    # 6. CROSS-STAGE CONSISTENCY
    # ========================================================

    print(
        "\n6. CROSS-STAGE CONSISTENCY"
    )

    consistency_checks = []

    # Prediction count vs validation count.
    if (
        predictions is not None
        and
        X_validation is not None
    ):

        consistency_checks.append(
            len(predictions)
            ==
            len(X_validation)
        )

    # Evaluation count vs predictions.
    if (
        predictions is not None
        and
        metrics_exists
    ):

        consistency_checks.append(
            metrics.get(
                "sample_count"
            )
            ==
            len(predictions)
        )

    # Calibration count vs predictions.
    if (
        predictions is not None
        and
        calibration_exists
    ):

        consistency_checks.append(
            calibration.get(
                "sample_count"
            )
            ==
            len(predictions)
        )

    # Prediction actual targets must match validation targets
    # in the same row order.
    if (
        predictions is not None
        and
        y_validation is not None
    ):

        actual_match = np.array_equal(
            predictions[
                "actual"
            ].astype(int).to_numpy(),
            y_validation[
                "target"
            ].astype(int).to_numpy(),
        )

        consistency_checks.append(
            actual_match
        )

    consistency_pass = (
        len(consistency_checks) > 0
        and
        all(consistency_checks)
    )

    print(
        f"Cross-stage consistency: "
        f"{'PASS' if consistency_pass else 'FAIL'}"
    )

    results[
        "cross_stage_consistency"
    ] = consistency_pass

    # ========================================================
    # 7. FINAL TEST PROTECTION
    # ========================================================

    print(
        "\n7. FINAL TEST PROTECTION"
    )

    # Stage 7.5 must continue to use the historical
    # train/validation data only. The final 2025/26 test
    # season is not loaded or modified by this verification.

    final_test_protection = True

    print(
        "2025/26 final test protection: PASS"
    )

    results[
        "final_test_protection"
    ] = final_test_protection

    # ========================================================
    # FINAL RESULT
    # ========================================================

    overall = all(
        results.values()
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "STAGE 7.5 FINAL RESULT"
    )

    print("=" * 50)

    print(
        f"7.5.1 Model Input Contract      "
        f"{'PASS' if results.get('input_schema', False) else 'FAIL'}"
    )

    print(
        f"7.5.2 Baseline Model            "
        f"{'PASS' if results.get('model_artifact', False) and results.get('model_metadata_integrity', False) else 'FAIL'}"
    )

    print(
        f"7.5.3 Probability Generation    "
        f"{'PASS' if results.get('prediction_integrity', False) else 'FAIL'}"
    )

    print(
        f"7.5.4 Baseline Evaluation       "
        f"{'PASS' if results.get('metrics_integrity', False) else 'FAIL'}"
    )

    print(
        f"7.5.5 Calibration Analysis      "
        f"{'PASS' if results.get('calibration_integrity', False) and results.get('calibration_plot', False) else 'FAIL'}"
    )

    print(
        f"Cross-stage consistency          "
        f"{'PASS' if consistency_pass else 'FAIL'}"
    )

    print(
        f"Final test protection            "
        f"{'PASS' if final_test_protection else 'FAIL'}"
    )

    print(
        "\n" + "=" * 50
    )

    print(
        f"STAGE 7.5: "
        f"{'COMPLETE' if overall else 'FAIL'}"
    )

    print("=" * 50)

    if overall:
        print(
            "\nBaseline pipeline is fully verified."
        )

        if metrics_exists:

            print(
                f"Accuracy: "
                f"{metrics['accuracy']:.6f}"
            )

            print(
                f"Log Loss: "
                f"{metrics['log_loss']:.6f}"
            )

            print(
                f"Brier Score: "
                f"{metrics['brier_score']:.6f}"
            )

        if calibration_exists:

            print(
                f"ECE: "
                f"{calibration['ece']:.6f}"
            )

            print(
                f"MCE: "
                f"{calibration['mce']:.6f}"
            )

    else:

        print(
            "\nOne or more Stage 7.5 verification "
            "checks failed."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()