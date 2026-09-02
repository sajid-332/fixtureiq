"""
FixtureIQ Stage 7.5.3 + 7.5.4
Probability and Evaluation Verification.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(BASE_DIR),
)


from backend.models.probabilities import (
    PREDICTIONS_FILE,
    PREDICTION_METADATA_FILE,
)

from backend.models.evaluation import (
    METRICS_FILE,
    CLASS_LABELS,
)


def main():

    print("=" * 50)

    print(
        "FixtureIQ Stage 7.5.3 + 7.5.4"
    )

    print(
        "Final Verification"
    )

    print("=" * 50)

    # ========================================================
    # Prediction files
    # ========================================================

    print(
        "\n1. PREDICTION ARTIFACTS"
    )

    prediction_file_pass = (
        PREDICTIONS_FILE.exists()
    )

    metadata_file_pass = (
        PREDICTION_METADATA_FILE.exists()
    )

    print(
        f"Prediction file: "
        f"{'PASS' if prediction_file_pass else 'FAIL'}"
    )

    print(
        f"Prediction metadata: "
        f"{'PASS' if metadata_file_pass else 'FAIL'}"
    )

    if not prediction_file_pass:
        sys.exit(1)

    predictions = pd.read_csv(
        PREDICTIONS_FILE
    )

    # ========================================================
    # Prediction count
    # ========================================================

    print(
        "\n2. PREDICTION COUNT"
    )

    count_pass = (
        len(predictions) == 380
    )

    print(
        f"Predictions: "
        f"{len(predictions)}"
    )

    print(
        f"Expected: 380"
    )

    print(
        f"Result: "
        f"{'PASS' if count_pass else 'FAIL'}"
    )

    # ========================================================
    # Required columns
    # ========================================================

    print(
        "\n3. PREDICTION SCHEMA"
    )

    required = {
        "fixture_id",
        "actual",
        "predicted",
        "prob_home",
        "prob_draw",
        "prob_away",
    }

    schema_pass = (
        required
        <=
        set(predictions.columns)
    )

    print(
        f"Required columns: "
        f"{'PASS' if schema_pass else 'FAIL'}"
    )

    # ========================================================
    # Target validation
    # ========================================================

    print(
        "\n4. TARGET VALIDATION"
    )

    actual_valid = (
        set(
            predictions["actual"]
            .astype(int)
            .unique()
        )
        <=
        set(CLASS_LABELS)
    )

    predicted_valid = (
        set(
            predictions["predicted"]
            .astype(int)
            .unique()
        )
        <=
        set(CLASS_LABELS)
    )

    target_pass = (
        actual_valid
        and
        predicted_valid
    )

    print(
        f"Actual targets: "
        f"{'PASS' if actual_valid else 'FAIL'}"
    )

    print(
        f"Predicted targets: "
        f"{'PASS' if predicted_valid else 'FAIL'}"
    )

    # ========================================================
    # Probability validation
    # ========================================================

    print(
        "\n5. PROBABILITY VALIDATION"
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

    finite_pass = np.isfinite(
        probabilities
    ).all()

    range_pass = (
        (probabilities >= 0).all()
        and
        (probabilities <= 1).all()
    )

    sums = probabilities.sum(
        axis=1
    )

    sums_pass = np.allclose(
        sums,
        1.0,
        atol=1e-8,
    )

    print(
        f"Finite probabilities: "
        f"{'PASS' if finite_pass else 'FAIL'}"
    )

    print(
        f"Probability range: "
        f"{'PASS' if range_pass else 'FAIL'}"
    )

    print(
        f"Probability sums: "
        f"{'PASS' if sums_pass else 'FAIL'}"
    )

    probability_pass = (
        finite_pass
        and
        range_pass
        and
        sums_pass
    )

    # ========================================================
    # Duplicate fixtures
    # ========================================================

    print(
        "\n6. DUPLICATE PREDICTIONS"
    )

    duplicate_count = int(
        predictions[
            "fixture_id"
        ].duplicated()
        .sum()
    )

    duplicate_pass = (
        duplicate_count == 0
    )

    print(
        f"Duplicate fixture IDs: "
        f"{duplicate_count}"
    )

    print(
        f"Result: "
        f"{'PASS' if duplicate_pass else 'FAIL'}"
    )

    # ========================================================
    # Metrics
    # ========================================================

    print(
        "\n7. EVALUATION METRICS"
    )

    metrics_file_pass = (
        METRICS_FILE.exists()
    )

    print(
        f"Metrics file: "
        f"{'PASS' if metrics_file_pass else 'FAIL'}"
    )

    metrics_pass = False

    if metrics_file_pass:

        with METRICS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            metrics = json.load(file)

        required_metrics = {
            "accuracy",
            "log_loss",
            "brier_score",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "per_class",
            "confusion_matrix",
        }

        metrics_pass = (
            required_metrics
            <=
            set(metrics.keys())
        )

        print(
            f"Metric schema: "
            f"{'PASS' if metrics_pass else 'FAIL'}"
        )

        print(
            f"Accuracy: "
            f"{metrics.get('accuracy')}"
        )

        print(
            f"Log Loss: "
            f"{metrics.get('log_loss')}"
        )

        print(
            f"Brier Score: "
            f"{metrics.get('brier_score')}"
        )

    # ========================================================
    # Final
    # ========================================================

    overall = all(
        [
            prediction_file_pass,
            metadata_file_pass,
            count_pass,
            schema_pass,
            target_pass,
            probability_pass,
            duplicate_pass,
            metrics_file_pass,
            metrics_pass,
        ]
    )

    print(
        "\n" + "=" * 50
    )

    print(
        "FINAL RESULT"
    )

    print(
        f"Stage 7.5.3: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"Stage 7.5.4: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    print(
        f"\n7.5.3 + 7.5.4: "
        f"{'PASS' if overall else 'FAIL'}"
    )

    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()